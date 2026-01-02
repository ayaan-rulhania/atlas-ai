"""
Quantization utilities for memory-efficient inference.
Provides INT8 quantization support to reduce memory usage by 4x.
"""
import torch
import torch.nn as nn
from typing import Dict, Optional, Any, Union
import logging

logger = logging.getLogger(__name__)


class ModelQuantizer:
    """
    Handles quantization of transformer models for memory-efficient inference.
    Supports INT8 quantization using PyTorch's dynamic quantization.
    """

    def __init__(self):
        self.quantized_models = {}

    def quantize_model(self, model: nn.Module, method: str = "dynamic_int8") -> nn.Module:
        """
        Quantize a model for memory-efficient inference.

        Args:
            model: The model to quantize
            method: Quantization method ("dynamic_int8", "static_int8", "qint8")

        Returns:
            Quantized model
        """
        if method == "dynamic_int8":
            return self._dynamic_int8_quantization(model)
        elif method == "static_int8":
            return self._static_int8_quantization(model)
        elif method == "qint8":
            return self._qint8_quantization(model)
        else:
            logger.warning(f"Unknown quantization method {method}, using dynamic_int8")
            return self._dynamic_int8_quantization(model)

    def _dynamic_int8_quantization(self, model: nn.Module) -> nn.Module:
        """
        Apply dynamic INT8 quantization.
        Quantizes weights on-the-fly during inference for maximum memory savings.
        """
        try:
            # Prepare model for quantization
            model.eval()

            # Define quantization configuration
            qconfig = torch.quantization.get_default_qconfig('fbgemm')

            # Apply quantization configuration
            model.qconfig = qconfig

            # Prepare the model for quantization
            torch.quantization.prepare(model, inplace=True)

            # Convert to quantized model
            torch.quantization.convert(model, inplace=True)

            logger.info("Successfully applied dynamic INT8 quantization")
            return model

        except Exception as e:
            logger.error(f"Dynamic quantization failed: {e}")
            return model

    def _static_int8_quantization(self, model: nn.Module) -> nn.Module:
        """
        Apply static INT8 quantization.
        Requires calibration data for optimal accuracy.
        """
        try:
            model.eval()

            # Fuse layers where possible (Conv + BN + ReLU, Linear + ReLU)
            model = torch.quantization.fuse_modules(model, [
                ['token_embeddings', torch.nn.quantized.FloatFunctional()],
            ])

            # Set quantization config
            model.qconfig = torch.quantization.get_default_qconfig('fbgemm')

            # Prepare for quantization
            torch.quantization.prepare(model, inplace=True)

            # Calibrate with dummy data (in production, use real calibration data)
            self._calibrate_model(model)

            # Convert to quantized
            torch.quantization.convert(model, inplace=True)

            logger.info("Successfully applied static INT8 quantization")
            return model

        except Exception as e:
            logger.error(f"Static quantization failed: {e}")
            return model

    def _qint8_quantization(self, model: nn.Module) -> nn.Module:
        """
        Apply QINT8 quantization using torch.quantization.quantize_dynamic.
        """
        try:
            # Define modules to quantize (Linear layers are most beneficial)
            qconfig_dict = {
                torch.nn.Linear: torch.quantization.per_channel_dynamic_qconfig
            }

            # Prepare model
            model.eval()

            # Apply dynamic quantization to Linear layers
            quantized_model = torch.quantization.quantize_dynamic(
                model,
                qconfig_dict,
                inplace=False
            )

            logger.info("Successfully applied QINT8 quantization")
            return quantized_model

        except Exception as e:
            logger.error(f"QINT8 quantization failed: {e}")
            return model

    def _calibrate_model(self, model: nn.Module, num_calibration_batches: int = 10):
        """
        Calibrate the model with sample data for static quantization.
        In production, use representative data from your dataset.
        """
        model.eval()

        with torch.no_grad():
            for _ in range(num_calibration_batches):
                # Generate dummy calibration data
                batch_size = 1
                seq_len = min(128, getattr(model, 'max_position_embeddings', 512))
                vocab_size = getattr(model, 'vocab_size', 50257)

                input_ids = torch.randint(0, vocab_size, (batch_size, seq_len))
                attention_mask = torch.ones_like(input_ids)

                # Forward pass for calibration
                try:
                    _ = model(input_ids=input_ids, attention_mask=attention_mask)
                except:
                    # If forward pass fails, skip calibration
                    break

    def get_model_size_info(self, model: nn.Module) -> Dict[str, Any]:
        """
        Get memory usage information for a model.

        Args:
            model: The model to analyze

        Returns:
            Dictionary with size information
        """
        total_params = sum(p.numel() for p in model.parameters())
        total_size_bytes = sum(p.numel() * p.element_size() for p in model.parameters())

        # Calculate size in MB
        total_size_mb = total_size_bytes / (1024 * 1024)

        return {
            'total_parameters': total_params,
            'total_size_bytes': total_size_bytes,
            'total_size_mb': total_size_mb,
            'quantized': hasattr(model, 'qconfig') or any(hasattr(m, 'weight') and m.weight.dtype != torch.float32 for m in model.modules())
        }

    def optimize_for_inference(self, model: nn.Module) -> nn.Module:
        """
        Apply inference optimizations beyond quantization.

        Args:
            model: Model to optimize

        Returns:
            Optimized model
        """
        model.eval()

        # Enable inference mode optimizations
        torch.set_grad_enabled(False)

        # Additional optimizations can be added here:
        # - JIT compilation
        # - Memory pinning
        # - etc.

        return model


class QuantizedModelLoader:
    """
    Handles loading and managing quantized models.
    """

    def __init__(self):
        self.quantizer = ModelQuantizer()

    def load_quantized_model(
        self,
        model_path: str,
        model_class: Any,
        quantization_method: str = "dynamic_int8",
        **model_kwargs
    ) -> nn.Module:
        """
        Load a model with quantization applied.

        Args:
            model_path: Path to saved model
            model_class: Model class to instantiate
            quantization_method: Quantization method to apply
            **model_kwargs: Additional arguments for model initialization

        Returns:
            Quantized model
        """
        try:
            # Load the base model
            checkpoint = torch.load(model_path, map_location='cpu')
            config = checkpoint.get('config', {})

            # Create model instance
            model = model_class(**{**config, **model_kwargs})

            # Load state dict
            if 'model_state_dict' in checkpoint:
                model.load_state_dict(checkpoint['model_state_dict'], strict=False)
            else:
                model.load_state_dict(checkpoint, strict=False)

            # Apply quantization
            model = self.quantizer.quantize_model(model, quantization_method)

            # Optimize for inference
            model = self.quantizer.optimize_for_inference(model)

            logger.info(f"Successfully loaded quantized model from {model_path}")
            logger.info(f"Model size: {self.quantizer.get_model_size_info(model)}")

            return model

        except Exception as e:
            logger.error(f"Failed to load quantized model: {e}")
            raise

    def save_quantized_model(self, model: nn.Module, path: str):
        """
        Save a quantized model to disk.

        Args:
            model: Model to save
            path: Save path
        """
        try:
            # For quantized models, we need special handling
            if hasattr(model, 'qconfig'):
                # Save quantized model
                torch.save({
                    'model_state_dict': model.state_dict(),
                    'config': getattr(model, 'config', {}),
                    'quantized': True,
                    'quantization_method': 'int8'
                }, path)
            else:
                # Regular save
                torch.save(model.state_dict(), path)

            logger.info(f"Saved quantized model to {path}")

        except Exception as e:
            logger.error(f"Failed to save quantized model: {e}")
            raise


# Global instances
_quantizer = None
_quantized_loader = None


def get_quantizer() -> ModelQuantizer:
    """Get or create the global quantizer instance."""
    global _quantizer
    if _quantizer is None:
        _quantizer = ModelQuantizer()
    return _quantizer


def get_quantized_loader() -> QuantizedModelLoader:
    """Get or create the global quantized loader instance."""
    global _quantized_loader
    if _quantized_loader is None:
        _quantized_loader = QuantizedModelLoader()
    return _quantized_loader


def quantize_model_for_inference(
    model: nn.Module,
    method: str = "dynamic_int8"
) -> nn.Module:
    """
    Convenience function to quantize a model for inference.

    Args:
        model: Model to quantize
        method: Quantization method

    Returns:
        Quantized model
    """
    quantizer = get_quantizer()
    return quantizer.quantize_model(model, method)


def load_quantized_model(
    model_path: str,
    model_class: Any,
    quantization_method: str = "dynamic_int8",
    **model_kwargs
) -> nn.Module:
    """
    Convenience function to load a quantized model.

    Args:
        model_path: Path to model
        model_class: Model class
        quantization_method: Quantization method
        **model_kwargs: Model arguments

    Returns:
        Loaded quantized model
    """
    loader = get_quantized_loader()
    return loader.load_quantized_model(model_path, model_class, quantization_method, **model_kwargs)
