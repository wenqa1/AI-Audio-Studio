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
from flask import (
    Flask, request, jsonify, render_template, Response,
    send_from_directory, send_file, abort
)
from flask_cors import CORS
from pydub import AudioSegment
import config
from audio_separator.separator import Separator

# 常量
ALLOWED_AUDIO_EXTS = {'.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.wma'}
MAX_UPLOAD_SIZE = 500 * 1024 * 1024
PROGRESS_TTL = 300                # 任务完成后保留 5 分钟,供客户端拉取
SSE_MAX_WAIT_SECONDS = 30 * 60    # SSE 最长等待 30 分钟,避免永久挂起
SSE_POLL_INTERVAL = 1
TASK_ID_RE = re.compile(r'[0-9a-f]{8}')
DEBUG_MODE = os.environ.get('FLASK_DEBUG', '0') == '1'

# 环境配置
ffmpeg_dir = str(config.BIN_FOLDER)
if ffmpeg_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + ffmpeg_dir
AudioSegment.converter = config.FFMPEG_PATH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates")
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE
CORS(app)

gpu_semaphore = threading.Semaphore(1)
progress_db = {}
progress_lock = threading.Lock()
OUTPUT_ROOT = config.OUTPUT_FOLDER.resolve()


def get_safe_filename(name):
    return re.sub(r'[\\/:*?"<>|]', '_', name).strip()


def safe_output_path(filename):
    """校验 filename 没有路径穿越,返回解析后的绝对路径,非法返回 None。"""
    if not filename or not isinstance(filename, str):
        return None
    if '/' in filename or '\\' in filename or filename in ('..', '.'):
        return None
    candidate = (OUTPUT_ROOT / filename).resolve()
    try:
        candidate.relative_to(OUTPUT_ROOT)
    except ValueError:
        return None
    return candidate


def schedule_progress_cleanup(task_id, delay=PROGRESS_TTL):
    """延迟从 progress_db 中清理任务记录,避免无限增长。"""
    def _cleanup():
        time.sleep(delay)
        with progress_lock:
            progress_db.pop(task_id, None)
        logger.info("清理任务记录 %s", task_id)
    threading.Thread(target=_cleanup, daemon=True).start()


def set_progress(task_id, percent, files=None):
    with progress_lock:
        progress_db[task_id] = {"percent": percent, "files": files or []}


def get_progress(task_id):
    with progress_lock:
        # 复制一份,避免迭代时被改写
        data = progress_db.get(task_id)
        return dict(data) if data else {"percent": 0, "files": []}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/models')
def get_models():
    return jsonify(config.MODELS)


@app.route('/outputs/<path:filename>')
def serve_output(filename):
    # send_from_directory 内部已使用 safe_join 拒绝路径穿越
    return send_from_directory(OUTPUT_ROOT, filename)


@app.route('/api/merge', methods=['POST'])
def merge_tracks():
    data = request.get_json(silent=True) or {}
    files = data.get('files', [])
    if not isinstance(files, list) or len(files) < 2:
        return jsonify({"error": "至少需要 2 个轨道才能合并"}), 400

    paths = []
    for f in files:
        p = safe_output_path(f)
        if p is None or not p.exists():
            return jsonify({"error": f"非法或不存在的文件: {f}"}), 400
        paths.append(p)

    try:
        base_track = AudioSegment.from_file(paths[0])
        for p in paths[1:]:
            base_track = base_track.overlay(AudioSegment.from_file(p))
        out_name = f"Mix_{int(time.time())}.mp3"
        base_track.export(OUTPUT_ROOT / out_name, format="mp3")
        return jsonify({"status": "success", "filename": out_name})
    except Exception:
        logger.exception("合并失败")
        return jsonify({"error": "合并处理失败"}), 500


@app.route('/api/progress/<task_id>')
def progress_stream(task_id):
    if not TASK_ID_RE.fullmatch(task_id):
        abort(400)

    def generate():
        start = time.time()
        while time.time() - start < SSE_MAX_WAIT_SECONDS:
            data = get_progress(task_id)
            yield f"data: {json.dumps(data)}\n\n"
            if data["percent"] >= 100 or data["percent"] == -1:
                return
            time.sleep(SSE_POLL_INTERVAL)
        yield f"data: {json.dumps({'percent': -1, 'files': [], 'error': 'timeout'})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


def separation_task(task_id, input_path, original_name, model_id, overlap):
    sep = None
    with gpu_semaphore:
        try:
            sep = Separator(
                output_dir=str(OUTPUT_ROOT),
                model_file_dir=str(config.MODEL_FOLDER),
                output_format="mp3",
            )
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

            label_map = {
                "Vocals": "人声", "Drums": "鼓点", "Bass": "贝斯",
                "Other": "其他", "Instrumental": "伴奏",
            }
            final_files = []
            name_base = os.path.splitext(original_name)[0]
            for f in raw_files:
                old_p = OUTPUT_ROOT / f
                label = next((v for k, v in label_map.items() if k in f), "音轨")
                new_n = f"{task_id}_{name_base}_{label}.mp3"
                new_p = OUTPUT_ROOT / new_n
                if new_p.exists():
                    new_p.unlink()
                old_p.rename(new_p)
                final_files.append(new_n)

            set_progress(task_id, 100, final_files)
            logger.info("任务 %s 完成: %d 个文件", task_id, len(final_files))
        except Exception:
            logger.exception("任务 %s 失败", task_id)
            set_progress(task_id, -1)
        finally:
            sep = None
            gc.collect()
            try:
                if os.path.exists(input_path):
                    os.remove(input_path)
            except OSError as e:
                logger.warning("清理临时文件失败 %s: %s", input_path, e)
            schedule_progress_cleanup(task_id)


@app.route('/api/process', methods=['POST'])
def process():
    if 'file' not in request.files:
        return jsonify({"error": "缺少上传文件"}), 400
    file = request.files['file']
    if not file or not file.filename:
        return jsonify({"error": "文件为空"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_AUDIO_EXTS:
        return jsonify({"error": f"不支持的音频格式: {ext}"}), 400

    model_key = request.form.get('model_key')
    if model_key not in config.MODELS:
        return jsonify({"error": "无效的模型选项"}), 400

    try:
        overlap = float(request.form.get('overlap', 0.6))
    except (TypeError, ValueError):
        return jsonify({"error": "overlap 必须为数字"}), 400
    if not 0.0 < overlap < 1.0:
        return jsonify({"error": "overlap 必须在 (0, 1) 范围内"}), 400

    task_id = uuid.uuid4().hex[:8]
    clean_name = get_safe_filename(file.filename)
    temp_path = config.UPLOAD_FOLDER / f"{task_id}_{clean_name}"
    file.save(temp_path)

    set_progress(task_id, 0)
    threading.Thread(
        target=separation_task,
        args=(task_id, temp_path, clean_name, config.MODELS[model_key]['id'], overlap),
        daemon=True,
    ).start()

    return jsonify({"status": "started", "task_id": task_id})


@app.route('/api/download_zip', methods=['POST'])
def download_zip():
    data = request.get_json(silent=True) or {}
    file_list = data.get('files', [])
    if not isinstance(file_list, list) or not file_list:
        return jsonify({"error": "未指定文件"}), 400

    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in file_list:
            p = safe_output_path(f)
            if p and p.exists():
                zf.write(p, arcname=f)
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name="Studio_Results.zip",
    )


@app.errorhandler(413)
def too_large(_e):
    return jsonify({"error": f"文件过大,上限 {MAX_UPLOAD_SIZE // (1024 * 1024)}MB"}), 413


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=DEBUG_MODE)
