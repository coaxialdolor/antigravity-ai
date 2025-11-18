import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
from pathlib import Path

class ImageEngine:
    def __init__(self, models_dir, device="cuda"):
        self.models_dir = Path(models_dir)
        self.device = device if torch.cuda.is_available() else "cpu"
        self.pipeline = None
        self.current_model_id = None

    def load_model(self, model_id="runwayml/stable-diffusion-v1-5"):
        """
        Loads a model. 
        model_id can be a HuggingFace ID or a local path.
        """
        try:
            # Use float16 for GPU to save VRAM
            dtype = torch.float16 if self.device == "cuda" else torch.float32
            
            self.pipeline = StableDiffusionPipeline.from_pretrained(
                model_id, 
                torch_dtype=dtype,
                use_safetensors=True
            )
            self.pipeline.scheduler = DPMSolverMultistepScheduler.from_config(self.pipeline.scheduler.config)
            self.pipeline.to(self.device)
            
            # Enable memory efficient attention if on CUDA
            if self.device == "cuda":
                try:
                    self.pipeline.enable_xformers_memory_efficient_attention()
                except Exception:
                    self.pipeline.enable_attention_slicing()

            self.current_model_id = model_id
            return f"Loaded {model_id}"
        except Exception as e:
            return f"Error loading model: {e}"

    def generate(self, prompt, negative_prompt="", steps=25, guidance=7.5):
        if not self.pipeline:
            # Auto load default if not loaded
            res = self.load_model()
            if "Error" in res:
                return None, res
        
        try:
            image = self.pipeline(
                prompt=prompt, 
                negative_prompt=negative_prompt, 
                num_inference_steps=steps, 
                guidance_scale=guidance
            ).images[0]
            return image, "Success"
        except Exception as e:
            return None, f"Generation failed: {e}"
