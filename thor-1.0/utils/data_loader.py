"""
Data loading utilities for multitask learning.
"""
import torch
from torch.utils.data import Dataset, DataLoader
from typing import List, Dict, Optional, Tuple
import json
import os


class MultiTaskDataset(Dataset):
    """Dataset for multitask learning."""
    
    def __init__(
        self,
        data: List[Dict],
        tokenizer,
        max_length: int = 512,
        task: Optional[str] = None
    ):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.task = task
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        task = item.get('task', self.task)
        
        # Encode input text
        text = item.get('text', item.get('input', ''))
        input_ids = self.tokenizer.encode(text, max_length=self.max_length)
        attention_mask = [1 if tid != 0 else 0 for tid in input_ids]  # 0 is pad token
        
        result = {
            'input_ids': torch.tensor(input_ids, dtype=torch.long),
            'attention_mask': torch.tensor(attention_mask, dtype=torch.long),
            'task': task
        }
        
        # Add labels based on task
        if 'label' in item:
            if task == 'question_answering':
                # For QA, labels are start and end positions
                result['start_positions'] = torch.tensor(item['label'].get('start', 0), dtype=torch.long)
                result['end_positions'] = torch.tensor(item['label'].get('end', 0), dtype=torch.long)
            elif task == 'text_generation':
                # For generation, labels are the same as input_ids (shifted)
                result['labels'] = torch.tensor(input_ids, dtype=torch.long)
            else:
                result['labels'] = torch.tensor(item['label'], dtype=torch.long)
        
        return result


class MultiTaskDataLoader:
    """Data loader for multitask training."""
    
    def __init__(
        self,
        tokenizer,
        batch_size: int = 32,
        max_length: int = 512,
        num_workers: int = 0
    ):
        self.tokenizer = tokenizer
        self.batch_size = batch_size
        self.max_length = max_length
        self.num_workers = num_workers
    
    def load_data(self, data_path: str) -> List[Dict]:
        """Load data from JSON file."""
        if not os.path.exists(data_path):
            return []
        
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'data' in data:
            return data['data']
        else:
            return []
    
    def create_dataloader(
        self,
        data: List[Dict],
        task: Optional[str] = None,
        shuffle: bool = False
    ) -> DataLoader:
        """Create a DataLoader from data."""
        dataset = MultiTaskDataset(data, self.tokenizer, self.max_length, task)
        return DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=shuffle,
            num_workers=self.num_workers,
            collate_fn=self._collate_fn
        )
    
    def _collate_fn(self, batch):
        """Collate function for batching."""
        input_ids = torch.stack([item['input_ids'] for item in batch])
        attention_mask = torch.stack([item['attention_mask'] for item in batch])
        tasks = [item['task'] for item in batch]
        
        result = {
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'task': tasks[0] if len(set(tasks)) == 1 else None
        }
        
        if 'labels' in batch[0]:
            result['labels'] = torch.stack([item['labels'] for item in batch])
        
        if 'start_positions' in batch[0]:
            result['start_positions'] = torch.stack([item['start_positions'] for item in batch])
            result['end_positions'] = torch.stack([item['end_positions'] for item in batch])
        
        return result

