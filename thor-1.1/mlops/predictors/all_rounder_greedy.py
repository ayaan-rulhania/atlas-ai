"""
Minimal greedy text-generation wrapper for AllRounderModel.

This is intended for offline evaluation (e.g., judge scoring). It avoids the (currently complex)
`thor-1.1/inference.py` path and instead calls the model directly.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import torch


def _encode_no_pad(tokenizer: Any, text: str, add_bos: bool = True) -> List[int]:
    words = text.lower().split()
    unk_id = tokenizer.word_to_id.get("<unk>", 1)
    max_vocab = getattr(tokenizer, "vocab_size", None)
    ids: List[int] = []
    if add_bos:
        ids.append(tokenizer.word_to_id.get("<bos>", 2))
    for w in words:
        tid = tokenizer.word_to_id.get(w, unk_id)
        if isinstance(max_vocab, int) and tid >= max_vocab:
            tid = unk_id
        ids.append(tid)
    return ids


class AllRounderGreedyPredictor:
    def __init__(self, model: torch.nn.Module, tokenizer: Any, device: Optional[torch.device] = None):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.model.to(self.device)
        self.model.eval()

    def predict(self, text: str, task: str = "text_generation", max_new_tokens: int = 128) -> Dict[str, Any]:
        if task != "text_generation":
            raise ValueError("AllRounderGreedyPredictor currently supports task='text_generation' only.")

        eos_id = self.tokenizer.word_to_id.get("<eos>", 3)
        max_pos = getattr(self.model, "max_position_embeddings", None)

        prompt_ids = _encode_no_pad(self.tokenizer, text, add_bos=True)
        generated: List[int] = list(prompt_ids)

        with torch.no_grad():
            for _ in range(max_new_tokens):
                if isinstance(max_pos, int) and len(generated) >= max_pos:
                    break
                input_ids = torch.tensor([generated], dtype=torch.long, device=self.device)
                attention_mask = torch.ones_like(input_ids, dtype=torch.long, device=self.device)
                out = self.model(input_ids=input_ids, attention_mask=attention_mask, task="text_generation")
                logits = out.get("logits") if isinstance(out, dict) else out
                next_id = int(torch.argmax(logits[0, -1, :]).item())
                generated.append(next_id)
                if next_id == eos_id:
                    break

        # Decode only the generated continuation (excluding the prompt)
        continuation = generated[len(prompt_ids) :]
        text_out = self.tokenizer.decode(continuation, skip_special_tokens=True)
        return {"generated_text": text_out.strip()}


