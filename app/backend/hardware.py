import torch

def get_device_info():
    info = {
        "device": "cpu",
        "name": "CPU",
        "vram": 0
    }
    
    if torch.cuda.is_available():
        info["device"] = "cuda"
        info["name"] = torch.cuda.get_device_name(0)
        info["vram"] = round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2)
    
    return info
