"""
Inference Server Abstraction Layer.
Supports multiple backends: direct PyTorch, vLLM, TensorRT-LLM, etc.
"""
import os
import torch
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod


class InferenceBackend(ABC):
    """Abstract base class for inference backends."""
    
    @abstractmethod
    def load_model(self, model_path: str, **kwargs):
        """Load model for inference."""
        pass
    
    @abstractmethod
    def predict(self, inputs: Any, **kwargs) -> Any:
        """Run inference."""
        pass
    
    @abstractmethod
    def unload_model(self):
        """Unload model from memory."""
        pass


class PyTorchBackend(InferenceBackend):
    """Direct PyTorch inference backend."""
    
    def __init__(self):
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    def load_model(self, model_path: str, **kwargs):
        """Load PyTorch model."""
        try:
            from models import AllRounderModel
            task_configs = kwargs.get('task_configs', {})
            self.model = AllRounderModel.load_model(model_path, task_configs)
            self.model = self.model.to(self.device)
            self.model.eval()
            print(f"[PyTorchBackend] Model loaded on {self.device}")
        except Exception as e:
            print(f"[PyTorchBackend] Error loading model: {e}")
            raise
    
    def predict(self, inputs: Any, task: str = "text_generation", **kwargs) -> Any:
        """Run inference with PyTorch model."""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        if hasattr(self.model, 'predict'):
            return self.model.predict(inputs, task=task, **kwargs)
        else:
            # Fallback: direct forward pass
            with torch.no_grad():
                if isinstance(inputs, str):
                    # Simple tokenization (would need proper tokenizer in production)
                    inputs = torch.tensor([[1, 2, 3]])  # Placeholder
                outputs = self.model(inputs.to(self.device))
                return {"output": outputs.cpu().numpy().tolist()}
    
    def unload_model(self):
        """Unload model from memory."""
        if self.model is not None:
            del self.model
            self.model = None
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            print("[PyTorchBackend] Model unloaded")


class InferenceServer:
    """
    Unified inference server that can use different backends.
    """
    
    def __init__(self, backend_type: str = "pytorch"):
        """
        Initialize inference server.
        
        Args:
            backend_type: Type of backend ("pytorch", "vllm", "tensorrt", etc.)
        """
        self.backend_type = backend_type
        self.backend = self._create_backend(backend_type)
        self.model_loaded = False
    
    def _create_backend(self, backend_type: str) -> InferenceBackend:
        """Create appropriate backend instance."""
        if backend_type == "pytorch":
            return PyTorchBackend()
        elif backend_type == "vllm":
            # Placeholder for vLLM integration
            print("[InferenceServer] vLLM backend not yet implemented, using PyTorch")
            return PyTorchBackend()
        elif backend_type == "tensorrt":
            # Placeholder for TensorRT integration
            print("[InferenceServer] TensorRT backend not yet implemented, using PyTorch")
            return PyTorchBackend()
        else:
            print(f"[InferenceServer] Unknown backend type {backend_type}, using PyTorch")
            return PyTorchBackend()
    
    def load_model(self, model_path: str, **kwargs):
        """Load model using the configured backend."""
        self.backend.load_model(model_path, **kwargs)
        self.model_loaded = True
    
    def predict(self, inputs: Any, task: str = "text_generation", **kwargs) -> Any:
        """Run inference."""
        if not self.model_loaded:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        return self.backend.predict(inputs, task=task, **kwargs)
    
    def unload_model(self):
        """Unload model."""
        if self.model_loaded:
            self.backend.unload_model()
            self.model_loaded = False
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about the current backend."""
        return {
            "backend_type": self.backend_type,
            "model_loaded": self.model_loaded,
            "device": str(self.backend.device) if hasattr(self.backend, 'device') else "unknown"
        }


def get_inference_server(backend_type: Optional[str] = None) -> InferenceServer:
    """Get or create an inference server instance."""
    if backend_type is None:
        # Try to detect best backend
        backend_type = os.environ.get("INFERENCE_BACKEND", "pytorch")
    return InferenceServer(backend_type)

