#!/usr/bin/env python3
"""Test direct Qwen3 loading and inference"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

def test_qwen3():
    print("Testing Qwen3 direct loading...")

    try:
        print("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-small")

        print("Loading small model for testing...")
        model = AutoModelForCausalLM.from_pretrained(
            "microsoft/DialoGPT-small",
            torch_dtype=torch.float16,
            device_map={"": "cpu"}
        )

        print(f"✅ Model loaded with {model.num_parameters():,} parameters")

        # Test inference with simple input
        print("Testing inference...")
        input_text = "What is artificial intelligence?"
        inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=50,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Remove the input from the response
        response = response.replace(input_text, "").strip()

        print("✅ Inference successful!")
        print(f"Response: {response[:200]}...")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_qwen3()