# 🎙️ AI-Audio-Studio Pro (2025 旗舰版)

**AI-Audio-Studio** 是一款基于 Web 端的高性能人声分离与音频编辑工具。它深度集成了目前业内尖端的 AI 分离模型（如 **Roformer** 和 **Demucs v4**），并配合自研的 **“Mixer Studio (混音工作室)”**，为音乐制作人、DJ 和音频爱好者提供从“音轨拆解”到“创意重组”的一站式工作流。

---

## ✨ 核心功能与技术亮点

### 1. 全架构 AI 核心
* **多架构兼容**：支持 **MDXC (Roformer)**、**MDX-Net**、**VR Arch** 以及 **Demucs v4**。
* **BS-Roformer 强力驱动**：默认搭载 `BS-Roformer-Viper-1297` 模型，提供目前 SOTA 级的干净人声提取。
* **Demucs 四分轨**：一键将音频拆分为 **人声 (Vocals)**、**鼓点 (Drums)**、**贝斯 (Bass)** 和 **其他 (Other)** 乐器。

### 2. 独立混音工作室 (Mixer Studio) 
* **跨任务轨道叠加**：不再局限于单次处理，可自由勾选历史任务中的任意音轨。
* **毫秒级无损合并**：基于 `pydub` 引擎，实现多音轨精准对齐与波形叠加，一键导出混音成品。

### 3. 极致用户体验 (UX)
* **平滑虚拟进度条**：针对 AI 加载期的“反馈真空”，采用非线性减速算法，确保进度条从 0% 到 100% 始终平滑跳动。
* **唯一性命名规范**：遵循 `[任务ID]_[原歌名]_[音轨标签].mp3` 命名逻辑，完美解决浏览器预览重复、文件覆盖的问题，且完整保留中文名称。
* **批量生产力**：支持一键 ZIP 打包所有结果，以及一键清理输出库功能。

### 4. 企业级稳定性
* **GPU 任务排队锁**：内置全局信号量 (Semaphore)，多文件并发上传时自动排队进入显存，彻底杜绝 CUDA Out of Memory (OOM) 崩溃。
* **自动显存回收**：每个任务结束后强制执行 `gc.collect()`，确保显存占用不随处理数量堆积。

---

## 🛠️ 技术栈

* **后端**: Python 3.10+, Flask, Flask-CORS
* **AI 引擎**: `audio-separator` (ONNX Runtime GPU / PyTorch)
* **音频混合**: `pydub` (FFmpeg 支持)
* **前端**: HTML5, Tailwind CSS, JavaScript (SSE 异步通讯)

---

## 📦 安装与环境配置

### 1. 基础环境
确保您的系统安装了 Python 3.10 或更高版本，并拥有 NVIDIA GPU（推荐 4GB 以上显存）。

### 2. 安装依赖
在项目根目录下执行以下命令：
```bash
pip install flask flask-cors audio-separator[gpu] pydub