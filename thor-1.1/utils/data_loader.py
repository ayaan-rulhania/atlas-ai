"""
Data loading utilities for multitask learning.
"""
import torch
from torch.utils.data import Dataset, DataLoader
from typing import List, Dict, Optional, Tuple, Any
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


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    """Read a JSONL file into a list of dicts."""
    items: List[Dict[str, Any]] = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def _encode_no_pad(tokenizer: Any, text: str, add_bos: bool = False, add_eos: bool = False) -> List[int]:
    """
    Encode text to token IDs without padding.

    This repo’s `SimpleTokenizer.encode()` always pads to `max_length`, which makes it
    unsuitable for concatenating prompt+target segments for SFT. This helper mirrors the
    tokenizer’s behavior (lowercase + whitespace split) without padding.
    """
    words = text.lower().split()
    ids: List[int] = []
    if add_bos:
        ids.append(tokenizer.word_to_id.get("<bos>", 2))
    unk_id = tokenizer.word_to_id.get("<unk>", 1)
    max_vocab = getattr(tokenizer, "vocab_size", None)
    for w in words:
        tid = tokenizer.word_to_id.get(w, unk_id)
        # Safety: some checkpoints in this repo have very small vocabularies; clamp IDs to vocab.
        if isinstance(max_vocab, int) and tid >= max_vocab:
            tid = unk_id
        ids.append(tid)
    if add_eos:
        ids.append(tokenizer.word_to_id.get("<eos>", 3))
    return ids


def _format_chat(messages: List[Dict[str, str]]) -> str:
    """
    Convert chat messages into a simple, stable text format.

    NOTE: Because `SimpleTokenizer` is word-split, we use plain role prefixes.
    """
    chunks: List[str] = []
    for m in messages:
        role = (m.get("role") or "").strip().lower()
        content = (m.get("content") or "").strip()
        if not content:
            continue
        if role == "system":
            chunks.append(f"system: {content}")
        elif role == "user":
            chunks.append(f"user: {content}")
        elif role == "assistant":
            chunks.append(f"assistant: {content}")
        else:
            chunks.append(f"{role or 'unknown'}: {content}")
    # End prompt by cueing the assistant turn
    chunks.append("assistant:")
    return "\n".join(chunks).strip()


class ChatSFTDataset(Dataset):
    """
    Chat-style SFT dataset with label masking:
    - Prompt tokens are masked with -100
    - Assistant target tokens are supervised
    - Truncation keeps the most recent prompt tokens within max_length
    """

    def __init__(self, data: List[Dict[str, Any]], tokenizer: Any, max_length: int = 512):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]

        messages = item.get("messages") or []
        target = item.get("target") or ""

        prompt_text = _format_chat(messages)
        # Target is the assistant continuation; keep it as-is and let tokenizer lowercase.
        prompt_ids = _encode_no_pad(self.tokenizer, prompt_text, add_bos=False, add_eos=False)
        target_ids = _encode_no_pad(self.tokenizer, target, add_bos=False, add_eos=False)

        bos_id = self.tokenizer.word_to_id.get("<bos>", 2)
        eos_id = self.tokenizer.word_to_id.get("<eos>", 3)
        pad_id = self.tokenizer.word_to_id.get("<pad>", 0)

        # Reserve space for BOS/EOS.
        max_content = max(self.max_length - 2, 0)

        # If target is too long, truncate it (keep the beginning).
        if len(target_ids) > max_content:
            target_ids = target_ids[:max_content]

        # Keep most recent prompt tokens to fit remaining space.
        remaining_for_prompt = max_content - len(target_ids)
        if remaining_for_prompt < 0:
            remaining_for_prompt = 0
        if len(prompt_ids) > remaining_for_prompt:
            prompt_ids = prompt_ids[-remaining_for_prompt:]

        input_ids = [bos_id] + prompt_ids + target_ids + [eos_id]

        # Labels: supervise only the assistant target (and EOS); mask prompt.
        labels = [-100]  # BOS masked
        labels += [-100] * len(prompt_ids)
        labels += target_ids
        labels += [eos_id]

        # Pad to fixed length
        if len(input_ids) < self.max_length:
            pad_len = self.max_length - len(input_ids)
            input_ids = input_ids + [pad_id] * pad_len
            labels = labels + [-100] * pad_len
        else:
            input_ids = input_ids[: self.max_length]
            labels = labels[: self.max_length]

        attention_mask = [0 if tid == pad_id else 1 for tid in input_ids]

        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
            "task": "text_generation",
            "id": item.get("id"),
            "tags": item.get("tags"),
            "difficulty": item.get("difficulty"),
        }


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

        # Support both JSON and JSONL formats.
        if data_path.endswith(".jsonl"):
            data = _read_jsonl(data_path)
        else:
            with open(data_path, "r") as f:
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
        # If this looks like chat SFT (messages + target), use ChatSFTDataset.
        if data and all(("messages" in x and "target" in x) for x in data):
            dataset = ChatSFTDataset(data, self.tokenizer, self.max_length)
        else:
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

