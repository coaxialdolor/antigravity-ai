import os
from pathlib import Path
try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

class TextEngine:
    def __init__(self, default_models_dir, custom_dirs=[]):
        self.default_models_dir = Path(default_models_dir)
        self.custom_dirs = [Path(d) for d in custom_dirs]
        self.model = None
        self.model_name = None
        self.model_map = {} # Maps filename -> full path
        
        # Ensure default directory exists
        self.default_models_dir.mkdir(parents=True, exist_ok=True)

    def list_models(self):
        self.model_map = {}
        
        # Helper to scan a dir
        def scan_dir(d):
            if not d.exists(): return
            for f in d.glob("*.gguf"):
                self.model_map[f.name] = f

        # Scan default
        scan_dir(self.default_models_dir)
        
        # Scan custom
        for d in self.custom_dirs:
            scan_dir(d)
            
        return list(self.model_map.keys())

    def load_model(self, model_name, n_gpu_layers=-1):
        if not Llama:
            return "Error: llama-cpp-python not installed."
            
        if model_name not in self.model_map:
            # Try refreshing
            self.list_models()
            if model_name not in self.model_map:
                return f"Error: Model {model_name} not found in any directory."
        
        model_path = self.model_map[model_name]

        try:
            # n_gpu_layers=-1 offloads all to GPU if compiled with CUDA
            self.model = Llama(model_path=str(model_path), n_ctx=4096, n_gpu_layers=n_gpu_layers, verbose=False)
            self.model_name = model_name
            return f"Loaded {model_name}"
        except Exception as e:
            return f"Failed to load model: {e}"

    def generate(self, prompt, history=[], system_prompt="You are a helpful assistant.", stream=False):
        if not self.model:
            if stream:
                yield "Please load a model first."
                return
            return "Please load a model first."

        # Simple chat format construction (assuming Llama-3/ChatML style for simplicity)
        full_prompt = f"<|system|>\n{system_prompt}</s>\n"
        for user_msg, ai_msg in history:
            if user_msg: full_prompt += f"<|user|>\n{user_msg}</s>\n"
            if ai_msg: full_prompt += f"<|assistant|>\n{ai_msg}</s>\n"
        full_prompt += f"<|user|>\n{prompt}</s>\n<|assistant|>\n"

        output = self.model(
            full_prompt, 
            max_tokens=2048, 
            stop=["</s>", "<|user|>", "<|system|>"], 
            echo=False,
            stream=stream
        )
        
        if stream:
            for chunk in output:
                delta = chunk['choices'][0]['text']
                yield delta
        else:
            return output['choices'][0]['text'].strip()
