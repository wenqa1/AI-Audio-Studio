import torch
print("PyTorch 版本:", torch.__version__)
print("显卡是否可用:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("显卡名称:", torch.cuda.get_device_name(0))