import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from audio_separator.separator import Separator
import config

app = Flask(__name__)
CORS(app)


@app.route('/api/models', methods=['GET'])
def get_models():
    return jsonify(config.MODELS)


@app.route('/api/process', methods=['POST'])
def process():
    if 'file' not in request.files:
        return jsonify({"error": "没有文件"}), 400

    file = request.files['file']
    model_id = request.form.get('model_id')
    overlap = float(request.form.get('overlap', 0.6))

    # 唯一任务ID
    task_id = str(uuid.uuid4())[:8]
    input_filename = f"{task_id}_{file.filename}"
    input_path = config.UPLOAD_FOLDER / input_filename
    file.save(input_path)

    try:
        # 初始化分离器
        separator = Separator(
            output_dir=str(config.OUTPUT_FOLDER),
            model_file_dir=str(config.MODEL_FOLDER),
            output_format="mp3",
            ffmpeg_location=config.FFMPEG_PATH
        )

        separator.load_model(model_id)

        # 分离处理
        output_files = separator.separate(str(input_path))

        # 清理原始上传文件
        if os.path.exists(input_path):
            os.remove(input_path)

        return jsonify({
            "status": "success",
            "task_id": task_id,
            "results": output_files
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    print(f"✅ 后端已启动，FFmpeg 路径: {config.FFMPEG_PATH}")
    app.run(host='0.0.0.0', port=5000, debug=True)