"""
Advanced Training Manager with PEFT/LoRA support and hyperparameter tuning.
"""
import os
import json
import torch
import torch.nn as nn
import copy
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from peft import LoraConfig, get_peft_model, TaskType
    PEFT_AVAILABLE = True
except ImportError:
    PEFT_AVAILABLE = False
    print("[TrainingManager] PEFT not available. Install with: pip install peft")

try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    print("[TrainingManager] Optuna not available. Install with: pip install optuna")


class TrainingManager:
    """
    Advanced training manager with PEFT/LoRA support and hyperparameter tuning.
    """
    
    def __init__(self, base_model_path: str, output_dir: str = "models/adapters"):
        self.base_model_path = base_model_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.use_peft = PEFT_AVAILABLE
    
    def create_lora_config(
        self,
        r: int = 8,
        lora_alpha: int = 16,
        lora_dropout: float = 0.1,
        target_modules: Optional[List[str]] = None
    ) -> Optional[Any]:
        """
        Create LoRA configuration for parameter-efficient fine-tuning.
        
        Args:
            r: LoRA rank (lower = fewer parameters)
            lora_alpha: LoRA alpha scaling parameter
            lora_dropout: LoRA dropout rate
            target_modules: Modules to apply LoRA to (None = auto-detect)
        """
        if not PEFT_AVAILABLE:
            print("[TrainingManager] PEFT not available, using full fine-tuning")
            return None
        
        if target_modules is None:
            # Default target modules for transformer models
            target_modules = ["query", "key", "value", "dense"]
        
        # For chat SFT, treat this as causal language modeling.
        config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=r,
            lora_alpha=lora_alpha,
            lora_dropout=lora_dropout,
            target_modules=target_modules,
            bias="none"
        )
        
        return config
    
    def apply_peft(self, model: nn.Module, lora_config: Any) -> nn.Module:
        """Apply PEFT/LoRA to a model."""
        if not PEFT_AVAILABLE:
            return model
        
        try:
            peft_model = get_peft_model(model, lora_config)
            print(f"[TrainingManager] Applied LoRA. Trainable params: {peft_model.num_parameters()}")
            return peft_model
        except Exception as e:
            print(f"[TrainingManager] Error applying PEFT: {e}")
            return model
    
    def train_with_lora(
        self,
        model: nn.Module,
        train_loader: Any,
        val_loader: Optional[Any] = None,
        num_epochs: int = 3,
        learning_rate: float = 1e-4,
        lora_r: int = 8,
        lora_alpha: int = 16,
        output_name: Optional[str] = None,
        task: str = "text_generation",
        max_batches_per_epoch: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Train model with LoRA adapters.
        
        Returns:
            Dictionary with training results and adapter path
        """
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = model.to(device)
        
        # Apply LoRA
        if self.use_peft:
            lora_config = self.create_lora_config(r=lora_r, lora_alpha=lora_alpha)
            model = self.apply_peft(model, lora_config)
        
        # Setup training
        optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
        
        training_history = {
            "train_loss": [],
            "val_loss": [],
            "epochs": []
        }
        
        # Training loop
        for epoch in range(num_epochs):
            model.train()
            epoch_train_loss = 0.0
            batches_seen = 0
            
            for batch in train_loader:
                # Move batch to device
                input_ids = batch.get("input_ids", batch.get("inputs")).to(device)
                attention_mask = batch.get("attention_mask")
                if attention_mask is not None:
                    attention_mask = attention_mask.to(device)
                labels = batch.get("labels", batch.get("targets"))
                if labels is not None:
                    labels = labels.to(device)
                
                optimizer.zero_grad()
                # Prefer model-native loss (AllRounderModel computes shifted LM loss for text_generation).
                outputs = None
                loss = None
                try:
                    if attention_mask is not None and labels is not None:
                        outputs = model(input_ids=input_ids, attention_mask=attention_mask, task=task, labels=labels)
                    elif attention_mask is not None:
                        outputs = model(input_ids=input_ids, attention_mask=attention_mask, task=task)
                    else:
                        outputs = model(input_ids=input_ids, task=task, labels=labels) if labels is not None else model(input_ids=input_ids, task=task)
                    if isinstance(outputs, dict):
                        loss = outputs.get("loss")
                except TypeError:
                    # Fallback for non-AllRounder models with a simpler forward signature
                    outputs = model(input_ids)

                if loss is None:
                    # Generic fallback: compute token-level CE over logits and masked labels.
                    if isinstance(outputs, dict) and "logits" in outputs:
                        logits = outputs["logits"]
                    else:
                        logits = outputs
                    if labels is None:
                        raise ValueError("Training requires labels for supervised fine-tuning.")
                    loss_fct = nn.CrossEntropyLoss()  # default ignore_index=-100
                    shift_logits = logits[..., :-1, :].contiguous()
                    shift_labels = labels[..., 1:].contiguous()
                    loss = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))

                loss.backward()
                optimizer.step()
                
                epoch_train_loss += loss.item()
                batches_seen += 1
                if max_batches_per_epoch is not None and batches_seen >= max_batches_per_epoch:
                    break
            
            avg_train_loss = epoch_train_loss / len(train_loader)
            training_history["train_loss"].append(avg_train_loss)
            training_history["epochs"].append(epoch + 1)
            
            # Validation
            if val_loader:
                model.eval()
                val_loss = 0.0
                with torch.no_grad():
                    for batch in val_loader:
                        input_ids = batch.get("input_ids", batch.get("inputs")).to(device)
                        attention_mask = batch.get("attention_mask")
                        if attention_mask is not None:
                            attention_mask = attention_mask.to(device)
                        labels = batch.get("labels", batch.get("targets"))
                        if labels is not None:
                            labels = labels.to(device)

                        outputs = None
                        loss = None
                        try:
                            if attention_mask is not None and labels is not None:
                                outputs = model(input_ids=input_ids, attention_mask=attention_mask, task=task, labels=labels)
                            elif attention_mask is not None:
                                outputs = model(input_ids=input_ids, attention_mask=attention_mask, task=task)
                            else:
                                outputs = model(input_ids=input_ids, task=task, labels=labels) if labels is not None else model(input_ids=input_ids, task=task)
                            if isinstance(outputs, dict):
                                loss = outputs.get("loss")
                        except TypeError:
                            outputs = model(input_ids)

                        if loss is None:
                            if isinstance(outputs, dict) and "logits" in outputs:
                                logits = outputs["logits"]
                            else:
                                logits = outputs
                            if labels is None:
                                raise ValueError("Validation requires labels for supervised fine-tuning.")
                            loss_fct = nn.CrossEntropyLoss()
                            shift_logits = logits[..., :-1, :].contiguous()
                            shift_labels = labels[..., 1:].contiguous()
                            loss = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))

                        val_loss += loss.item()
                avg_val_loss = val_loss / len(val_loader)
                training_history["val_loss"].append(avg_val_loss)
            
            print(f"[TrainingManager] Epoch {epoch+1}/{num_epochs} - Train Loss: {avg_train_loss:.4f}")
        
        # Save adapter
        if output_name is None:
            output_name = f"adapter_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        adapter_path = self.output_dir / output_name
        adapter_path.mkdir(parents=True, exist_ok=True)
        
        if self.use_peft and hasattr(model, 'save_pretrained'):
            model.save_pretrained(str(adapter_path))
        else:
            torch.save(model.state_dict(), adapter_path / "adapter.pt")
        
        return {
            "adapter_path": str(adapter_path),
            "training_history": training_history,
            "use_peft": self.use_peft
        }
    
    def tune_hyperparameters(
        self,
        model: nn.Module,
        train_loader: Any,
        val_loader: Any,
        n_trials: int = 10,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Automatically tune hyperparameters using Optuna.
        
        Args:
            model: Base model
            train_loader: Training data loader
            val_loader: Validation data loader
            n_trials: Number of optimization trials
            timeout: Maximum time in seconds
            
        Returns:
            Best hyperparameters and study results
        """
        if not OPTUNA_AVAILABLE:
            print("[TrainingManager] Optuna not available, skipping hyperparameter tuning")
            return {"error": "Optuna not available"}
        
        base_model_copy = copy.deepcopy(model).cpu()

        def objective(trial):
            # Suggest hyperparameters
            lr = trial.suggest_loguniform('learning_rate', 1e-5, 1e-3)
            num_epochs = trial.suggest_int('num_epochs', 2, 5)
            lora_r = trial.suggest_categorical('lora_r', [4, 8, 16])
            lora_alpha = trial.suggest_categorical('lora_alpha', [8, 16, 32])
            
            # Train with these hyperparameters
            trial_model = copy.deepcopy(base_model_copy)
            result = self.train_with_lora(
                model=trial_model,
                train_loader=train_loader,
                val_loader=val_loader,
                num_epochs=num_epochs,
                learning_rate=lr,
                lora_r=lora_r,
                lora_alpha=lora_alpha,
                output_name=f"trial_{trial.number}"
            )
            
            # Return validation loss (to minimize)
            if result["training_history"].get("val_loss"):
                return min(result["training_history"]["val_loss"])
            return result["training_history"]["train_loss"][-1]
        
        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=n_trials, timeout=timeout)
        
        return {
            "best_params": study.best_params,
            "best_value": study.best_value,
            "n_trials": len(study.trials),
            "study": study
        }


def get_training_manager(base_model_path: str, output_dir: Optional[str] = None) -> TrainingManager:
    """Get or create a training manager instance."""
    if output_dir is None:
        output_dir = "models/adapters"
    return TrainingManager(base_model_path, output_dir)

