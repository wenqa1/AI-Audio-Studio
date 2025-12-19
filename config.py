import os
from pathlib import Path

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent

# --- 自动创建必要文件夹 ---
UPLOAD_FOLDER = BASE_DIR / "uploads"
OUTPUT_FOLDER = BASE_DIR / "outputs"
MODEL_FOLDER = BASE_DIR / "models"
BIN_FOLDER = BASE_DIR / "bin" / "ffmpeg"

for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, MODEL_FOLDER]:
    folder.mkdir(parents=True, exist_ok=True)

# --- FFmpeg 路径设定 ---
ffmpeg_exe = "ffmpeg.exe" if os.name == 'nt' else "ffmpeg"
FFMPEG_PATH = str(BIN_FOLDER / ffmpeg_exe)

# --- 场景模型定义 ---
MODELS = {
    "BS-RoFormer-Viper-2": {
        "name": "🚀 全能王者 (Viper-2)",
        "id": "BS-RoFormer-Viper-2.onnx",
        "desc": "目前最强人声分离，适合绝大部分场景。"
    },
    "Demucs-HT-FT": {
        "name": "🎸 乐队分轨 (Demucs)",
        "id": "htdemucs_ft",
        "desc": "分出人声、鼓、贝斯、其他，适合后期混音。"
    },
    "Inst-HQ-v3": {
        "name": "🎹 高清伴奏 (Inst-HQ)",
        "id": "UVR-MDX-NET-Inst_HQ_3.onnx",
        "desc": "极致伴奏质量，适合 KTV 伴奏制作。"
    },
    "KTV-Karaoke": {
        "name": "🎤 KTV 模式 (保留和声)",
        "id": "UVR_MDXNET_KARA_2.onnx",
        "desc": "保留背景和声，只去除主唱。"
    }
}