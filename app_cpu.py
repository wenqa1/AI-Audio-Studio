"""CPU 启动入口。与 app_gpu.py 共享全部业务代码,仅依赖包不同(参考 requirements_cpu.txt)。"""
from app_gpu import app, DEBUG_MODE

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=DEBUG_MODE)
