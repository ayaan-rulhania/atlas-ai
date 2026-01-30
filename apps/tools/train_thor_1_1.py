#!/usr/bin/env python3
"""
Thor 1.1 Training Pipeline
Comprehensive training script for continuous learning and large-scale model training
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, DistributedSampler
import torch.distributed as dist
import torch.multiprocessing as mp
from torch.nn.parallel import DistributedDataParallel as DDP
import torch.optim.lr_scheduler as lr_scheduler

import os
import json
import yaml
import argparse
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from transformers import GPT2TokenizerFast, AutoTokenizer
import wandb
from tqdm import tqdm
import schedule
import threading
import signal
import sys

# Add model paths
sys.path.append('models/thor-1.1')
sys.path.append('models/thor-1.0')

from thor_1_1_model import ThorModel, create_model

def create_model_from_config(config):
    """Create Thor model from config with proper structure"""
    # Convert config format to match model expectations
    features = config['features'].copy()

    # Map config keys to expected model keys
    features['use_rotary_embeddings'] = features.get('use_rope', True)

    model_config = {
        'architecture': {
            'vocab_size': config['hyperparameters']['vocab_size'],
            'hidden_size': config['hyperparameters']['hidden_size'],
            'num_layers': config['hyperparameters']['num_hidden_layers'],
            'num_heads': config['hyperparameters']['num_attention_heads'],
            'intermediate_size': config['hyperparameters']['intermediate_size'],
            'max_position_embeddings': config['hyperparameters']['max_position_embeddings'],
            'hidden_dropout_prob': config['hyperparameters']['hidden_dropout_prob'],
            'attention_dropout_prob': config['hyperparameters']['attention_probs_dropout_prob']
        },
        'features': features
    }

    return ThorModel(model_config)


class ThorDataset(Dataset):
    """Multi-task dataset for Thor 1.1 training"""

    def __init__(self, data_path: str, tokenizer, max_length: int = 2048, task_weights: Optional[Dict] = None):
        self.data_path = Path(data_path)
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.task_weights = task_weights or {
            'text_generation': 0.4,
            'text_classification': 0.2,
            'question_answering': 0.2,
            'sentiment_analysis': 0.2
        }

        self.data = []
        self.load_data()

    def load_data(self):
        """Load and preprocess training data"""
        if self.data_path.is_file():
            files = [self.data_path]
        else:
            files = list(self.data_path.glob("*.json")) + list(self.data_path.glob("*.jsonl"))

        for file_path in files:
            print(f"Loading data from {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix == '.jsonl':
                    for line in f:
                        item = json.loads(line.strip())
                        self.data.append(self.preprocess_item(item))
                else:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            self.data.append(self.preprocess_item(item))
                    else:
                        self.data.append(self.preprocess_item(data))

        print(f"Loaded {len(self.data)} training examples")

    def preprocess_item(self, item: Dict) -> Dict:
        """Preprocess a single data item"""
        task = item.get('task', 'text_generation')
        text = item.get('text', '')
        label = item.get('label')

        # Tokenize text
        if task in ['text_generation', 'question_answering']:
            # For generation and QA, use full text
            tokens = self.tokenizer(
                text,
                truncation=True,
                max_length=self.max_length,
                padding=False,
                return_tensors='pt'
            )
            input_ids = tokens['input_ids'].squeeze()
            attention_mask = tokens['attention_mask'].squeeze()

            processed_item = {
                'input_ids': input_ids,
                'attention_mask': attention_mask,
                'task': task,
                'labels': input_ids.clone() if task == 'text_generation' else None
            }

            if task == 'question_answering' and isinstance(label, dict):
                # Add QA labels
                start_pos = label.get('start', 0)
                end_pos = label.get('end', 0)
                processed_item['qa_labels'] = torch.tensor([start_pos, end_pos])

        elif task in ['text_classification', 'sentiment_analysis']:
            # For classification, use [CLS] token approach
            tokens = self.tokenizer(
                text,
                truncation=True,
                max_length=self.max_length,
                padding=False,
                return_tensors='pt'
            )
            input_ids = tokens['input_ids'].squeeze()
            attention_mask = tokens['attention_mask'].squeeze()

            # Convert label to tensor
            if isinstance(label, int):
                label_tensor = torch.tensor(label, dtype=torch.long)
            elif isinstance(label, str):
                # Simple label mapping for binary classification
                label_tensor = torch.tensor(1 if label.lower() in ['positive', 'yes', 'true'] else 0, dtype=torch.long)
            else:
                label_tensor = torch.tensor(0, dtype=torch.long)

            processed_item = {
                'input_ids': input_ids,
                'attention_mask': attention_mask,
                'task': task,
                'labels': label_tensor
            }

        else:
            # Default to text generation
            tokens = self.tokenizer(
                text,
                truncation=True,
                max_length=self.max_length,
                padding=False,
                return_tensors='pt'
            )
            input_ids = tokens['input_ids'].squeeze()
            attention_mask = tokens['attention_mask'].squeeze()

            processed_item = {
                'input_ids': input_ids,
                'attention_mask': attention_mask,
                'task': 'text_generation',
                'labels': input_ids.clone()
            }

        return processed_item

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]


class DataCollator:
    """Data collator for batching"""

    def __init__(self, tokenizer, max_length: int = 2048):
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __call__(self, batch: List[Dict]) -> Dict:
        """Collate batch of examples"""
        batch_input_ids = []
        batch_attention_masks = []
        batch_labels = []
        batch_tasks = []

        max_len = 0
        for item in batch:
            batch_input_ids.append(item['input_ids'])
            batch_attention_masks.append(item['attention_mask'])
            batch_tasks.append(item['task'])

            # Find max length in batch
            max_len = max(max_len, len(item['input_ids']))

            # Handle labels based on task
            if item['task'] == 'text_generation':
                batch_labels.append(item['labels'])
            elif item['task'] in ['text_classification', 'sentiment_analysis']:
                batch_labels.append(item['labels'])
            elif item['task'] == 'question_answering':
                batch_labels.append(item.get('qa_labels', torch.tensor([0, 0])))

        # Pad sequences to max length in batch
        padded_input_ids = []
        padded_attention_masks = []
        padded_labels = []

        for i, (input_ids, attention_mask) in enumerate(zip(batch_input_ids, batch_attention_masks)):
            pad_len = max_len - len(input_ids)

            # Pad input_ids
            if pad_len > 0:
                padded_input_ids.append(torch.cat([input_ids, torch.full((pad_len,), self.tokenizer.pad_token_id)]))
                padded_attention_masks.append(torch.cat([attention_mask, torch.zeros(pad_len, dtype=torch.long)]))
            else:
                padded_input_ids.append(input_ids)
                padded_attention_masks.append(attention_mask)

            # Handle labels padding
            if batch_tasks[i] == 'text_generation':
                if pad_len > 0:
                    padded_labels.append(torch.cat([batch_labels[i], torch.full((pad_len,), -100)]))
                else:
                    padded_labels.append(batch_labels[i])
            elif batch_tasks[i] in ['text_classification', 'sentiment_analysis']:
                padded_labels.append(batch_labels[i])
            elif batch_tasks[i] == 'question_answering':
                padded_labels.append(batch_labels[i])

        # Stack tensors
        collated = {
            'input_ids': torch.stack(padded_input_ids),
            'attention_mask': torch.stack(padded_attention_masks),
            'tasks': batch_tasks
        }

        # Handle different label types
        if batch_tasks[0] == 'text_generation':
            collated['labels'] = torch.stack(padded_labels)
        elif batch_tasks[0] in ['text_classification', 'sentiment_analysis']:
            collated['labels'] = torch.stack(padded_labels)
        elif batch_tasks[0] == 'question_answering':
            collated['labels'] = torch.stack(padded_labels)

        return collated


class ThorTrainer:
    """Thor 1.1 Training Manager"""

    def __init__(self, config_path: str, model_path: Optional[str] = None,
                 output_dir: str = "models/thor-1.1/checkpoints",
                 use_wandb: bool = True, distributed: bool = False):
        self.config_path = Path(config_path)
        self.model_path = model_path
        self.output_dir = Path(output_dir)
        self.use_wandb = use_wandb
        self.distributed = distributed

        # Load configuration
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Setup logging
        self.setup_logging()

        # Initialize tokenizer
        self.tokenizer = self.load_tokenizer()

        # Initialize model
        self.model = self.load_model()

        # Setup distributed training if enabled
        if distributed:
            self.setup_distributed()

        # Setup optimizer and scheduler
        self.optimizer, self.scheduler = self.setup_optimizer()

        # Initialize wandb if enabled
        if use_wandb and (not distributed or dist.get_rank() == 0):
            wandb.init(project="thor-1.1", config=self.config)

        # Training state
        self.global_step = 0
        self.best_loss = float('inf')
        self.start_time = time.time()

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.output_dir / "training.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_tokenizer(self):
        """Load or create tokenizer"""
        tokenizer_dir = Path("models/thor-1.1/tokenizer")

        if (tokenizer_dir / "tokenizer.json").exists():
            self.logger.info("Loading existing tokenizer")
            tokenizer = GPT2TokenizerFast.from_pretrained(str(tokenizer_dir))
        else:
            self.logger.info("Creating new GPT-2 tokenizer")
            tokenizer = GPT2TokenizerFast.from_pretrained('gpt2')

            # Save tokenizer
            tokenizer.save_pretrained(str(tokenizer_dir))

        tokenizer.pad_token = tokenizer.eos_token
        return tokenizer

    def load_model(self) -> ThorModel:
        """Load Thor 1.1 model"""
        if self.model_path and Path(self.model_path).exists():
            # Load existing model (not implemented yet)
            model = create_model_from_config(self.config)
            # TODO: Load state dict from checkpoint
        else:
            # Create new model from config
            model = create_model_from_config(self.config)

        # Move to GPU if available
        if torch.cuda.is_available():
            model = model.cuda()

        return model

    def setup_distributed(self):
        """Setup distributed training"""
        if not torch.distributed.is_initialized():
            torch.distributed.init_process_group(backend='nccl')

        local_rank = int(os.environ.get('LOCAL_RANK', 0))
        torch.cuda.set_device(local_rank)
        self.model = DDP(self.model, device_ids=[local_rank])

    def setup_optimizer(self):
        """Setup optimizer and learning rate scheduler"""
        # Extract training config
        train_config = self.config['training']

        # Create optimizer
        optimizer = optim.AdamW(
            self.model.parameters(),
            lr=train_config['learning_rate'],
            weight_decay=train_config['weight_decay'],
            betas=(train_config['adam_beta1'], train_config['adam_beta2']),
            eps=train_config['adam_epsilon']
        )

        # Create scheduler
        if train_config['lr_scheduler_type'] == 'cosine':
            scheduler = lr_scheduler.CosineAnnealingLR(
                optimizer,
                T_max=train_config.get('num_epochs', 10),
                eta_min=train_config['learning_rate'] * 0.1
            )
        else:
            scheduler = lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.95)

        return optimizer, scheduler

    def create_data_loader(self, data_path: str, batch_size: int = 8, shuffle: bool = True) -> DataLoader:
        """Create data loader for training"""
        dataset = ThorDataset(data_path, self.tokenizer, max_length=self.config['hyperparameters']['max_position_embeddings'])
        data_collator = DataCollator(self.tokenizer, max_length=self.config['hyperparameters']['max_position_embeddings'])

        sampler = None
        if self.distributed:
            sampler = DistributedSampler(dataset, shuffle=shuffle)

        data_loader = DataLoader(
            dataset,
            batch_size=batch_size,
            sampler=sampler,
            shuffle=shuffle if sampler is None else False,
            collate_fn=data_collator,
            num_workers=4,
            pin_memory=True
        )

        return data_loader

    def train_epoch(self, data_loader: DataLoader) -> float:
        """Train for one epoch"""
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        progress_bar = tqdm(data_loader, desc="Training", disable=self.distributed and dist.get_rank() != 0)

        for batch in progress_bar:
            # Move batch to device
            batch = {k: v.cuda() if torch.is_tensor(v) else v for k, v in batch.items()}

            # Handle multi-task batching (simplified - assumes same task per batch)
            task = batch['tasks'][0] if isinstance(batch['tasks'], list) else batch['tasks']

            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(
                input_ids=batch['input_ids'],
                attention_mask=batch['attention_mask'],
                task=task,
                labels=batch.get('labels')
            )

            loss = outputs['loss']

            # Backward pass
            loss.backward()

            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config['training']['max_grad_norm'])

            # Optimizer step
            self.optimizer.step()

            # Update metrics
            total_loss += loss.item()
            num_batches += 1
            self.global_step += 1

            # Update progress bar
            progress_bar.set_postfix({'loss': f"{loss.item():.4f}"})

            # Log to wandb
            if self.use_wandb and (not self.distributed or dist.get_rank() == 0):
                wandb.log({
                    'train/loss': loss.item(),
                    'train/learning_rate': self.scheduler.get_last_lr()[0],
                    'train/global_step': self.global_step
                })

        return total_loss / num_batches

    def validate(self, data_loader: DataLoader) -> Dict[str, float]:
        """Validate model"""
        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch in tqdm(data_loader, desc="Validating", disable=self.distributed and dist.get_rank() != 0):
                # Move batch to device
                batch = {k: v.cuda() if torch.is_tensor(v) else v for k, v in batch.items()}

                # Handle multi-task batching
                task = batch['tasks'][0] if isinstance(batch['tasks'], list) else batch['tasks']

                outputs = self.model(
                    input_ids=batch['input_ids'],
                    attention_mask=batch['attention_mask'],
                    task=task,
                    labels=batch.get('labels')
                )

                loss = outputs['loss']
                total_loss += loss.item()
                num_batches += 1

        avg_loss = total_loss / num_batches

        # Log validation metrics
        if self.use_wandb and (not self.distributed or dist.get_rank() == 0):
            wandb.log({'val/loss': avg_loss})

        return {'loss': avg_loss}

    def save_checkpoint(self, epoch: int, loss: float, is_best: bool = False):
        """Save model checkpoint"""
        if self.distributed and dist.get_rank() != 0:
            return

        checkpoint_dir = self.output_dir / f"checkpoint-{epoch}"
        checkpoint_dir.mkdir(exist_ok=True)

        checkpoint = {
            'epoch': epoch,
            'global_step': self.global_step,
            'model_state_dict': self.model.module.state_dict() if self.distributed else self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'loss': loss,
            'config': self.config
        }

        checkpoint_path = checkpoint_dir / "checkpoint.pt"
        torch.save(checkpoint, checkpoint_path)

        # Save tokenizer
        self.tokenizer.save_pretrained(checkpoint_dir / "tokenizer")

        self.logger.info(f"Saved checkpoint to {checkpoint_path}")

        # Save best model
        if is_best:
            best_path = self.output_dir / "best_model.pt"
            torch.save(checkpoint, best_path)
            self.logger.info(f"Saved best model to {best_path}")

    def train(self, train_data_path: str, val_data_path: Optional[str] = None,
              num_epochs: int = 10, batch_size: int = 8, save_every: int = 1):
        """Main training loop"""
        # Create data loaders
        train_loader = self.create_data_loader(train_data_path, batch_size=batch_size)
        val_loader = self.create_data_loader(val_data_path, batch_size=batch_size, shuffle=False) if val_data_path else None

        self.logger.info(f"Starting training for {num_epochs} epochs")
        self.logger.info(f"Model has {self.model.module.get_num_params() if self.distributed else self.model.get_num_params():,} parameters")

        for epoch in range(num_epochs):
            self.logger.info(f"Epoch {epoch + 1}/{num_epochs}")

            # Train epoch
            train_loss = self.train_epoch(train_loader)
            self.logger.info(f"Training loss: {train_loss:.4f}")

            # Validate
            val_metrics = None
            if val_loader:
                val_metrics = self.validate(val_loader)
                self.logger.info(f"Validation loss: {val_metrics['loss']:.4f}")

            # Update scheduler
            self.scheduler.step()

            # Save checkpoint
            current_loss = val_metrics['loss'] if val_metrics else train_loss
            is_best = current_loss < self.best_loss
            if is_best:
                self.best_loss = current_loss

            if (epoch + 1) % save_every == 0 or is_best:
                self.save_checkpoint(epoch + 1, current_loss, is_best)

            # Log epoch summary
            if self.use_wandb and (not self.distributed or dist.get_rank() == 0):
                wandb.log({
                    'epoch': epoch + 1,
                    'epoch/train_loss': train_loss,
                    'epoch/val_loss': val_metrics['loss'] if val_metrics else 0,
                    'epoch/learning_rate': self.scheduler.get_last_lr()[0]
                })

        training_time = time.time() - self.start_time
        self.logger.info(f"Training completed in {training_time:.2f} seconds")

    def continuous_train(self, data_path: str, interval_minutes: int = 30):
        """Continuous training loop that runs every interval"""
        def train_job():
            self.logger.info("Starting continuous training cycle")
            try:
                # Create fresh data loader for new data
                train_loader = self.create_data_loader(data_path, batch_size=8, shuffle=True)

                # Train for one epoch on new data
                train_loss = self.train_epoch(train_loader)
                self.logger.info(f"Continuous training loss: {train_loss:.4f}")

                # Save updated model
                self.save_checkpoint(0, train_loss, is_best=False)

            except Exception as e:
                self.logger.error(f"Continuous training failed: {e}")

        # Schedule continuous training
        schedule.every(interval_minutes).minutes.do(train_job)

        self.logger.info(f"Continuous training scheduled every {interval_minutes} minutes")

        # Run initial training
        train_job()

        # Keep running scheduled jobs
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


def main():
    parser = argparse.ArgumentParser(description="Train Thor 1.1 Model")
    parser.add_argument("--config", type=str, default="models/thor-1.1/config/config.yaml",
                       help="Path to config file")
    parser.add_argument("--model_path", type=str, default=None,
                       help="Path to existing model checkpoint")
    parser.add_argument("--output_dir", type=str, default="models/thor-1.1/checkpoints",
                       help="Output directory for checkpoints")
    parser.add_argument("--train_data", type=str, default="data/training_data/train.json",
                       help="Path to training data")
    parser.add_argument("--val_data", type=str, default=None,
                       help="Path to validation data")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size")
    parser.add_argument("--num_epochs", type=int, default=10, help="Number of epochs")
    parser.add_argument("--save_every", type=int, default=1, help="Save checkpoint every N epochs")
    parser.add_argument("--continuous", action="store_true", help="Enable continuous training")
    parser.add_argument("--interval", type=int, default=30, help="Continuous training interval (minutes)")
    parser.add_argument("--no_wandb", action="store_true", help="Disable wandb logging")
    parser.add_argument("--distributed", action="store_true", help="Enable distributed training")

    args = parser.parse_args()

    # Setup output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize trainer
    trainer = ThorTrainer(
        config_path=args.config,
        model_path=args.model_path,
        output_dir=str(output_dir),
        use_wandb=not args.no_wandb,
        distributed=args.distributed
    )

    if args.continuous:
        # Continuous training mode
        trainer.continuous_train(args.train_data, args.interval)
    else:
        # Standard training mode
        trainer.train(
            train_data_path=args.train_data,
            val_data_path=args.val_data,
            num_epochs=args.num_epochs,
            batch_size=args.batch_size,
            save_every=args.save_every
        )


if __name__ == "__main__":
    # Handle graceful shutdown
    def signal_handler(signum, frame):
        print("Received signal, shutting down gracefully...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    main()