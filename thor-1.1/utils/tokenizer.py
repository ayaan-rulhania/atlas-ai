"""
Simple tokenizer for the model.
In production, you'd want to use a proper tokenizer like BPE or SentencePiece.
"""
from typing import List, Dict
import json
import os


class SimpleTokenizer:
    """Simple word-level tokenizer with vocabulary management."""
    
    def __init__(self, vocab_size: int = 50257):
        self.vocab_size = vocab_size
        self.word_to_id: Dict[str, int] = {
            '<pad>': 0,
            '<unk>': 1,
            '<bos>': 2,
            '<eos>': 3,
            '<mask>': 4,
        }
        self.id_to_word: Dict[int, str] = {v: k for k, v in self.word_to_id.items()}
        self.next_id = len(self.word_to_id)
    
    def build_vocab(self, texts: List[str], min_freq: int = 2):
        """Build vocabulary from texts."""
        word_freq: Dict[str, int] = {}
        
        for text in texts:
            words = text.lower().split()
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Add words that appear at least min_freq times
        for word, freq in sorted(word_freq.items(), key=lambda x: -x[1]):
            if freq >= min_freq and self.next_id < self.vocab_size:
                if word not in self.word_to_id:
                    self.word_to_id[word] = self.next_id
                    self.id_to_word[self.next_id] = word
                    self.next_id += 1
    
    def encode(self, text: str, max_length: int = 512, add_special_tokens: bool = True) -> List[int]:
        """Encode text to token IDs."""
        words = text.lower().split()
        token_ids = []
        
        if add_special_tokens:
            token_ids.append(self.word_to_id.get('<bos>', 2))
        
        for word in words[:max_length - 2]:
            token_ids.append(self.word_to_id.get(word, self.word_to_id.get('<unk>', 1)))
        
        if add_special_tokens:
            token_ids.append(self.word_to_id.get('<eos>', 3))
        
        # Pad to max_length
        while len(token_ids) < max_length:
            token_ids.append(self.word_to_id.get('<pad>', 0))
        
        return token_ids[:max_length]
    
    def decode(self, token_ids: List[int], skip_special_tokens: bool = True) -> str:
        """Decode token IDs to text."""
        words = []
        for token_id in token_ids:
            if token_id in self.id_to_word:
                word = self.id_to_word[token_id]
                if skip_special_tokens and word in ['<pad>', '<bos>', '<eos>', '<unk>', '<mask>']:
                    continue
                words.append(word)
            else:
                if not skip_special_tokens:
                    words.append('<unk>')
        
        return ' '.join(words)
    
    def save(self, path: str):
        """Save tokenizer to disk."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump({
                'word_to_id': self.word_to_id,
                'id_to_word': self.id_to_word,
                'vocab_size': self.vocab_size,
                'next_id': self.next_id
            }, f, indent=2)
    
    @classmethod
    def load(cls, path: str):
        """Load tokenizer from disk."""
        with open(path, 'r') as f:
            data = json.load(f)
        
        tokenizer = cls(data['vocab_size'])
        tokenizer.word_to_id = data['word_to_id']
        tokenizer.id_to_word = {int(k): v for k, v in data['id_to_word'].items()}
        tokenizer.next_id = data['next_id']
        return tokenizer

