#!/usr/bin/env python3
"""
Checkpoint Migration Utility for Atlas AI Model Architecture Updates

This script helps migrate old model checkpoints to be compatible with the new architecture
that uses RoPE positional embeddings and other improvements.
"""

import torch
import argparse
import os
from pathlib import Path


def migrate_checkpoint(input_path: str, output_path: str, verbose: bool = True):
    """
    Migrate an old checkpoint to be compatible with the new architecture.

    Args:
        input_path: Path to the old checkpoint
        output_path: Path to save the migrated checkpoint
        verbose: Whether to print migration information
    """
    if verbose:
        print(f"Loading checkpoint from {input_path}")

    # Load the old checkpoint
    checkpoint = torch.load(input_path, map_location='cpu')
    state_dict = checkpoint['model_state_dict']
    config = checkpoint['config']

    # Track migrations performed
    migrations = []

    # Remove old positional embeddings (now using RoPE)
    if any('position_embeddings' in k for k in state_dict.keys()):
        if verbose:
            print("✓ Removing absolute positional embeddings (now using RoPE)")
        migrations.append("removed_position_embeddings")

        # Remove positional embeddings
        state_dict = {k: v for k, v in state_dict.items() if 'position_embeddings' not in k}

    # Check for LayerNorm parameters that might need conversion for RMSNorm
    layernorm_keys = [k for k in state_dict.keys() if ('attention_norm' in k or 'ff_norm' in k or 'embedding_norm' in k) and 'bias' in k]
    if layernorm_keys:
        if verbose:
            print("✓ Found LayerNorm bias parameters (can be removed if using RMSNorm)")
            migrations.append("found_layernorm_bias")

    # Update config to indicate this is a migrated checkpoint
    config['migrated'] = True
    config['migrations_applied'] = migrations

    # Create new checkpoint
    new_checkpoint = {
        'model_state_dict': state_dict,
        'config': config
    }

    # Save migrated checkpoint
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    torch.save(new_checkpoint, output_path)

    if verbose:
        print(f"✓ Migrated checkpoint saved to {output_path}")
        print(f"✓ Applied migrations: {migrations}")

    return migrations


def main():
    parser = argparse.ArgumentParser(description="Migrate Atlas AI model checkpoints")
    parser.add_argument('input', help='Path to input checkpoint')
    parser.add_argument('output', help='Path to output migrated checkpoint')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress verbose output')

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input checkpoint not found: {args.input}")
        return 1

    try:
        migrations = migrate_checkpoint(args.input, args.output, verbose=not args.quiet)
        print(f"\nMigration completed successfully!")
        print(f"Applied {len(migrations)} migration(s)")

    except Exception as e:
        print(f"Error during migration: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
