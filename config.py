import os
from pathlib import Path

# 基础目录配置
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
OUTPUT_FOLDER = BASE_DIR / "outputs"
MODEL_FOLDER = BASE_DIR / "models"
BIN_FOLDER = BASE_DIR / "bin" / "ffmpeg"

# 自动创建必要文件夹
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, MODEL_FOLDER]:
    folder.mkdir(parents=True, exist_ok=True)

# FFmpeg 可执行文件路径
FFMPEG_PATH = str(BIN_FOLDER / ("ffmpeg.exe" if os.name == 'nt' else "ffmpeg"))

# --- 严格校准的模型 ID 列表 ---
MODELS = {
    "roformer": {
        "name": "BS-Roformer-Viper-1297",
        "tag": "最强人声",
        "desc": "MDXC 架构 | 目前 SOTA 级人声分离",
        "id": "model_bs_roformer_ep_317_sdr_12.9755.ckpt"
    },
    "demucs": {
        "name": "Demucs v4 FT",
        "tag": "标准分轨",
        "desc": "Demucs 架构 | 适合全乐队/多乐器提取",
        "id": "htdemucs_ft.yaml"  # 修正：Demucs 在该库中需要 .yaml 后缀作为 ID
    },
    "ktv": {
        "name": "保留和声 (KARA 2)",
        "tag": "KTV 模式",
        "desc": "MDX 架构 | 提取伴奏并保留和声",
        "id": "UVR_MDXNET_KARA_2.onnx"
    },
    "inst": {
        "name": "Inst HQ 3",
        "tag": "纯净伴奏",
        "desc": "MDX 架构 | 极致去除人声",
        "id": "UVR-MDX-NET-Inst_HQ_3.onnx"
    },
    "dereverb": {
        "name": "去混响 (DeReverb)",
        "tag": "后期修复",
        "desc": "VR 架构 | 消除房间回声/混响",
        "id": "UVR-DeEcho-DeReverb.pth"
    },
    "denoise": {
        "name": "AI 降噪 (DeNoise)",
        "tag": "音质修复",
        "desc": "VR 架构 | 消除底噪/电流杂音",
        "id": "UVR-DeNoise.pth"
    }
}