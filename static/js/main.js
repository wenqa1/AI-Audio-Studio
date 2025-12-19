document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileList = document.getElementById('file-list');
    const startBtn = document.getElementById('start-btn');
    const overlapRange = document.getElementById('overlap-range');
    const overlapVal = document.getElementById('overlap-val');

    let selectedFiles = [];

    // 更新精度数值显示
    overlapRange.addEventListener('input', (e) => {
        overlapVal.textContent = e.target.value;
    });

    // 点击上传
    dropZone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    function handleFiles(files) {
        for (let file of files) {
            selectedFiles.push(file);
            const item = document.createElement('div');
            item.className = "flex justify-between items-center bg-gray-50 p-4 rounded-xl border border-gray-100";
            item.innerHTML = `
                <span class="text-sm font-medium">🎵 ${file.name}</span>
                <span class="text-xs text-gray-400 status-text">等待处理...</span>
            `;
            fileList.appendChild(item);
        }
    }

    // 开始批量处理
    startBtn.addEventListener('click', async () => {
        if (selectedFiles.length === 0) return alert("请先上传音频文件");

        startBtn.disabled = true;
        startBtn.textContent = "🚀 正在全力处理中...";

        for (let i = 0; i < selectedFiles.length; i++) {
            const formData = new FormData();
            formData.append('file', selectedFiles[i]);
            formData.append('model_id', document.getElementById('model-select').value);
            formData.append('overlap', overlapRange.value);

            const statusElements = document.querySelectorAll('.status-text');
            statusElements[i].textContent = "⏳ 正在分离...";
            statusElements[i].classList.add('text-blue-500');

            try {
                const response = await fetch('http://127.0.0.1:5000/api/process', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();

                if (result.status === 'success') {
                    statusElements[i].textContent = "✅ 已完成";
                    statusElements[i].classList.replace('text-blue-500', 'text-green-500');
                } else {
                    throw new Error(result.message);
                }
            } catch (error) {
                statusElements[i].textContent = "❌ 失败";
                statusElements[i].classList.replace('text-blue-500', 'text-red-500');
            }
        }

        startBtn.disabled = false;
        startBtn.textContent = "✨ 全部处理完毕，请在 outputs 文件夹查看";
    });

    // 初始加载模型列表
    fetch('http://127.0.0.1:5000/api/models')
        .then(res => res.json())
        .then(data => {
            const select = document.getElementById('model-select');
            for (let key in data) {
                const opt = document.createElement('option');
                opt.value = data[key].id;
                opt.textContent = data[key].name;
                select.appendChild(opt);
            }
        });
});