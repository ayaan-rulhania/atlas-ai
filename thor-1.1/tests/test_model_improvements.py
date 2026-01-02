#!/usr/bin/env python3
"""
Unit tests for Thor 1.1 model architecture improvements
"""

import torch
import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.all_rounder_model import AllRounderModel, RotaryPositionEmbedding, RMSNorm, SwiGLU
from models.task_heads import TextClassificationHead, TextGenerationHead, NERHead, CRF


class TestModelImprovements(unittest.TestCase):
    """Test suite for model architecture improvements."""

    def setUp(self):
        """Set up test fixtures."""
        self.batch_size = 2
        self.seq_len = 10
        self.hidden_size = 64
        self.vocab_size = 1000
        self.num_heads = 4

    def test_rotary_position_embedding(self):
        """Test RoPE implementation."""
        rope = RotaryPositionEmbedding(self.hidden_size // self.num_heads, max_seq_len=100)

        # Create test input
        x = torch.randn(self.batch_size, self.num_heads, self.seq_len, self.hidden_size // self.num_heads)

        # Apply RoPE
        result = rope(x, self.seq_len)

        # Check output shape
        self.assertEqual(result.shape, x.shape)

        # Check that different positions produce different rotations
        self.assertFalse(torch.allclose(result[:, :, 0], result[:, :, 1], atol=1e-6))

    def test_rmsnorm(self):
        """Test RMSNorm implementation."""
        rmnorm = RMSNorm(self.hidden_size)

        # Create test input
        x = torch.randn(self.batch_size, self.seq_len, self.hidden_size)

        # Apply RMSNorm
        result = rmnorm(x)

        # Check output shape
        self.assertEqual(result.shape, x.shape)

        # Check that RMSNorm normalizes properly
        # RMSNorm should have similar statistics to input but normalized
        self.assertTrue(torch.allclose(result.std(dim=-1).mean(), torch.tensor(1.0), atol=0.1))

    def test_swiglu(self):
        """Test SwiGLU implementation."""
        swiglu = SwiGLU(self.hidden_size, self.hidden_size * 2)

        # Create test input
        x = torch.randn(self.batch_size, self.seq_len, self.hidden_size)

        # Apply SwiGLU
        result = swiglu(x)

        # Check output shape
        self.assertEqual(result.shape, (self.batch_size, self.seq_len, self.hidden_size))

    def test_crf(self):
        """Test CRF implementation."""
        num_tags = 5
        crf = CRF(num_tags)

        # Create test inputs
        batch_size, seq_len = 2, 8
        emissions = torch.randn(batch_size, seq_len, num_tags)
        tags = torch.randint(0, num_tags, (batch_size, seq_len))
        mask = torch.ones(batch_size, seq_len, dtype=torch.bool)

        # Test forward (loss computation)
        loss = crf(emissions, tags, mask)
        self.assertTrue(loss.item() >= 0)

        # Test decode (Viterbi)
        predictions = crf.decode(emissions, mask)
        self.assertEqual(len(predictions), batch_size)
        self.assertEqual(len(predictions[0]), seq_len)

    def test_enhanced_text_classification_head(self):
        """Test enhanced text classification head with attention pooling."""
        head = TextClassificationHead(self.hidden_size, num_labels=3)

        # Create test input
        hidden_states = torch.randn(self.batch_size, self.seq_len, self.hidden_size)
        attention_mask = torch.ones(self.batch_size, self.seq_len, dtype=torch.bool)

        # Forward pass
        logits = head(hidden_states, attention_mask)

        # Check output shape
        self.assertEqual(logits.shape, (self.batch_size, 3))

    def test_enhanced_text_generation_head(self):
        """Test enhanced text generation head with layer norm."""
        head = TextGenerationHead(self.hidden_size, self.vocab_size)

        # Create test input
        hidden_states = torch.randn(self.batch_size, self.seq_len, self.hidden_size)

        # Forward pass
        logits = head(hidden_states)

        # Check output shape
        self.assertEqual(logits.shape, (self.batch_size, self.seq_len, self.vocab_size))

    def test_enhanced_ner_head(self):
        """Test enhanced NER head with CRF."""
        head = NERHead(self.hidden_size, num_labels=9, use_crf=True)

        # Create test input
        hidden_states = torch.randn(self.batch_size, self.seq_len, self.hidden_size)
        labels = torch.randint(0, 9, (self.batch_size, self.seq_len))
        attention_mask = torch.ones(self.batch_size, self.seq_len, dtype=torch.bool)

        # Forward pass
        result = head(hidden_states, labels, attention_mask)

        # Check that it returns expected keys
        self.assertIn('emissions', result)
        self.assertIn('loss', result)
        self.assertIn('predictions', result)

    def test_model_with_rope(self):
        """Test model with RoPE enabled."""
        model = AllRounderModel(
            hidden_size=self.hidden_size,
            vocab_size=self.vocab_size,
            num_layers=2,
            num_heads=self.num_heads,
            max_position_embeddings=50
        )

        # Create test input
        input_ids = torch.randint(0, self.vocab_size, (self.batch_size, self.seq_len))

        # Forward pass
        outputs = model(input_ids)

        # Check that hidden states are returned
        self.assertIn('hidden_states', outputs)
        self.assertEqual(outputs['hidden_states'].shape, (self.batch_size, self.seq_len, self.hidden_size))

    def test_model_with_rmsnorm(self):
        """Test model with RMSNorm enabled."""
        model = AllRounderModel(
            hidden_size=self.hidden_size,
            vocab_size=self.vocab_size,
            num_layers=2,
            num_heads=self.num_heads,
            max_position_embeddings=50,
            use_rmsnorm=True
        )

        # Create test input
        input_ids = torch.randint(0, self.vocab_size, (self.batch_size, self.seq_len))

        # Forward pass
        outputs = model(input_ids)

        # Check that it works
        self.assertIn('hidden_states', outputs)

    def test_model_with_swiglu(self):
        """Test model with SwiGLU enabled."""
        model = AllRounderModel(
            hidden_size=self.hidden_size,
            vocab_size=self.vocab_size,
            num_layers=2,
            num_heads=self.num_heads,
            max_position_embeddings=50,
            use_swiglu=True
        )

        # Create test input
        input_ids = torch.randint(0, self.vocab_size, (self.batch_size, self.seq_len))

        # Forward pass
        outputs = model(input_ids)

        # Check that it works
        self.assertIn('hidden_states', outputs)

    def test_gradient_checkpointing(self):
        """Test gradient checkpointing functionality."""
        model = AllRounderModel(
            hidden_size=self.hidden_size,
            vocab_size=self.vocab_size,
            num_layers=2,
            num_heads=self.num_heads,
            max_position_embeddings=50,
            gradient_checkpointing=True
        )

        # Enable training mode to test checkpointing
        model.train()

        # Create test input
        input_ids = torch.randint(0, self.vocab_size, (self.batch_size, self.seq_len))

        # Forward pass should work with checkpointing
        outputs = model(input_ids)
        self.assertIn('hidden_states', outputs)


if __name__ == '__main__':
    unittest.main()
