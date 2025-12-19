# 🎙️ AI Audio Studio - 人声分离专家版

一个基于深度学习的音频分离应用，支持多种 SOTA 模型（RoFormer, Demucs）。

## ✨ 功能特性
- **多种模型切换**：支持 Viper-2, Demucs 等顶尖模型。
- **GPU 加速**：自动检测 NVIDIA 显卡进行高速处理。
- **批量处理**：一次上传多个文件，自动队列执行。
- **手动精度控制**：可调节 Overlap 参数平衡质量与速度。
- **便携性**：内置 FFmpeg 路径管理，跨设备轻松运行。

## 🚀 快速启动
1. **环境准备**：
   `pip install -r requirements_gpu.txt`
2. **放置依赖**：
   将 `ffmpeg.exe` 放入 `bin/ffmpeg/` 目录。
3. **运行程序**：
   `python app_gpu.py`
4. **访问页面**：
   打开浏览器访问 `http://127.0.0.1:5001`