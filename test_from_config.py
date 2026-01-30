#!/usr/bin/env python3
"""
Test the from_config method for AllRounderModel
"""

import sys
import os
from pathlib import Path

# Add model path
sys.path.insert(0, 'models/thor-1.1')
sys.path.insert(0, 'models/thor-1.1/models')

try:
    from models.all_rounder_model import AllRounderModel
    print("✅ Successfully imported AllRounderModel")
except ImportError as e:
    print(f"❌ Failed to import AllRounderModel: {e}")
    sys.exit(1)

def test_from_config():
    """Test the from_config method"""
    print("\n=== Testing from_config method ===")

    # Load config
    import yaml
    try:
        with open("models/thor-1.1/config/config.yaml", 'r') as f:
            config = yaml.safe_load(f)
        print("✅ Config loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False

    try:
        model = AllRounderModel.from_config(config)
        print("✅ Model created successfully from config")

        # Check model properties
        print(f"   Hidden size: {model.hidden_size}")
        print(f"   Num layers: {len(model.transformer_blocks)}")
        print(f"   Vocab size: {model.vocab_size}")

        # Count parameters
        total_params = sum(p.numel() for p in model.parameters())
        print(f"   Total parameters: {total_params:,} ({total_params/1e6:.1f}M)")

        return True

    except Exception as e:
        print(f"❌ Failed to create model from config: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing AllRounderModel.from_config")

    # Change to project root
    os.chdir(Path(__file__).parent)

    success = test_from_config()

    if success:
        print("\n🎉 from_config test passed!")
    else:
        print("\n💥 from_config test failed!")
        sys.exit(1)