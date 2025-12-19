import os
import uuid
import logging
import threading
import json
import time
import gc
import zipfile
import re
from io import BytesIO
from flask import Flask, request, jsonify, render_template, Response, send_from_directory, send_file
from flask_cors import CORS
from pydub import AudioSegment
import config
from audio_separator.separator import Separator

# 环境配置
ffmpeg_dir = str(config.BIN_FOLDER)
if ffmpeg_dir not in os.environ["PATH"]:
    os.environ["PATH"] += os.pathsep + ffmpeg_dir
AudioSegment.converter = config.FFMPEG_PATH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates")
CORS(app)

gpu_semaphore = threading.Semaphore(1)
progress_db = {}


def get_safe_filename(name):
    return re.sub(r'[\\/:*?"<>|]', '_', name).strip()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/models')
def get_models():
    return jsonify(config.MODELS)


@app.route('/outputs/<path:filename>')
def serve_output(filename):
    return send_from_directory(config.OUTPUT_FOLDER, filename)


# 核心功能：音频合并
@app.route('/api/merge', methods=['POST'])
def merge_tracks():
    try:
        data = request.json
        files = data.get('files', [])
        if not files: return jsonify({"error": "未选中任何轨道"}), 400

        # 合并逻辑
        base_track = AudioSegment.from_file(config.OUTPUT_FOLDER / files[0])
        for file in files[1:]:
            overlay_track = AudioSegment.from_file(config.OUTPUT_FOLDER / file)
            base_track = base_track.overlay(overlay_track)

        out_name = f"Mix_{int(time.time())}.mp3"
        base_track.export(config.OUTPUT_FOLDER / out_name, format="mp3")
        return jsonify({"status": "success", "filename": out_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/progress/<task_id>')
def progress_stream(task_id):
    def generate():
        while True:
            data = progress_db.get(task_id, {"percent": 0, "files": []})
            yield f"data: {json.dumps(data)}\n\n"
            if data["percent"] >= 100 or data["percent"] == -1: break
            time.sleep(1)

    return Response(generate(), mimetype='text/event-stream')


def separation_task(task_id, input_path, original_name, model_id, overlap):
    with gpu_semaphore:
        try:
            sep = Separator(output_dir=str(config.OUTPUT_FOLDER), model_file_dir=str(config.MODEL_FOLDER),
                            output_format="mp3")
            if model_id.endswith(".ckpt"):
                sep.mdxc_params = {"overlap": overlap, "batch_size": 1}
            elif model_id.endswith(".onnx"):
                sep.mdx_params = {"overlap": overlap, "batch_size": 1}
            elif model_id.endswith(".pth"):
                sep.vr_params = {"window_size": 512}
            elif "demucs" in model_id.lower():
                sep.demucs_params = {"overlap": overlap}

            sep.load_model(model_id)
            raw_files = sep.separate(str(input_path))

            final_files = []
            name_base = os.path.splitext(original_name)[0]
            for f in raw_files:
                old_p = config.OUTPUT_FOLDER / f
                if "Vocals" in f:
                    label = "人声"
                elif "Drums" in f:
                    label = "鼓点"
                elif "Bass" in f:
                    label = "贝斯"
                elif "Other" in f:
                    label = "其他"
                elif "Instrumental" in f:
                    label = "伴奏"
                else:
                    label = "音轨"
                new_n = f"{task_id}_{name_base}_{label}.mp3"
                if os.path.exists(config.OUTPUT_FOLDER / new_n): os.remove(config.OUTPUT_FOLDER / new_n)
                os.rename(old_p, config.OUTPUT_FOLDER / new_n)
                final_files.append(new_n)

            progress_db[task_id] = {"percent": 100, "files": final_files}
        except Exception as e:
            progress_db[task_id] = {"percent": -1, "files": []}
        finally:
            if 'sep' in locals(): del sep
            gc.collect()
            if os.path.exists(input_path): os.remove(input_path)


@app.route('/api/process', methods=['POST'])
def process():
    file = request.files['file']
    task_id = uuid.uuid4().hex[:8]
    clean_name = get_safe_filename(file.filename)
    temp_path = config.UPLOAD_FOLDER / f"{task_id}_{clean_name}"
    file.save(temp_path)
    progress_db[task_id] = {"percent": 0, "files": []}
    threading.Thread(target=separation_task,
                     args=(task_id, temp_path, clean_name, config.MODELS[request.form.get('model_key')]['id'],
                           float(request.form.get('overlap', 0.6)))).start()
    return jsonify({"status": "started", "task_id": task_id})


@app.route('/api/download_zip', methods=['POST'])
def download_zip():
    file_list = request.json.get('files', [])
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in file_list:
            p = config.OUTPUT_FOLDER / f
            if p.exists(): zf.write(p, arcname=f)
    memory_file.seek(0)
    return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name="Studio_Results.zip")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)