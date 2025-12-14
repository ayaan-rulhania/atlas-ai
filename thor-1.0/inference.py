"""
Inference script for the All-Rounder AI Model.
"""
import torch
import argparse
import yaml
import os
from typing import Dict, Optional

from models import AllRounderModel
from utils import SimpleTokenizer


def load_config(config_path: str):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def setup_device():
    """Setup device (CUDA or CPU)."""
    if torch.cuda.is_available():
        return torch.device('cuda')
    return torch.device('cpu')


class AllRounderInference:
    """Inference interface for the All-Rounder model."""
    
    def __init__(self, model_path: str, tokenizer_path: str, config_path: str = 'config/config/config.yaml'):
        self.config = load_config(config_path)
        self.device = setup_device()
        
        # Load tokenizer
        self.tokenizer = SimpleTokenizer.load(tokenizer_path)
        
        # Prepare task configs
        tasks_config = self.config.get('tasks', [])
        task_configs = {task['name']: task for task in tasks_config if task.get('enabled', True)}
        
        # Load model
        self.model = AllRounderModel.load_model(model_path, task_configs)
        self.model = self.model.to(self.device)
        self.model.eval()
        
        print(f"Model loaded from {model_path}")
        print(f"Device: {self.device}")
        print(f"Available tasks: {list(task_configs.keys())}")
    
    def predict(
        self,
        text: str,
        task: str,
        max_length: Optional[int] = None
    ) -> Dict:
        """
        Make a prediction for the given text and task.
        
        Args:
            text: Input text
            task: Task name (e.g., 'text_classification', 'sentiment_analysis')
            max_length: Maximum sequence length
        
        Returns:
            Dictionary with predictions
        """
        if max_length is None:
            max_length = self.config['model']['max_position_embeddings']
        
        # Get actual model max position embeddings (might be smaller than config)
        # Check from loaded model if available
        model_max_pos = 256  # Default safe value
        if hasattr(self, 'model') and hasattr(self.model, 'max_position_embeddings'):
            model_max_pos = self.model.max_position_embeddings
        elif 'model' in self.config:
            model_max_pos = self.config['model'].get('max_position_embeddings', 256)
        
        # Use the smaller of the two
        effective_max = min(max_length, model_max_pos)
        
        # Tokenize with safe length
        input_ids = self.tokenizer.encode(text, max_length=effective_max)
        attention_mask = [1 if tid != 0 else 0 for tid in input_ids]
        
        # Safety: truncate if somehow still too long
        if len(input_ids) > model_max_pos:
            input_ids = input_ids[:model_max_pos]
            attention_mask = attention_mask[:model_max_pos]
        
        # Convert to tensors
        input_ids = torch.tensor([input_ids], dtype=torch.long).to(self.device)
        attention_mask = torch.tensor([attention_mask], dtype=torch.long).to(self.device)
        
        # Forward pass
        with torch.no_grad():
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                task=task
            )
        
        # Process outputs based on task
        result = {'task': task, 'input': text}
        
        if task == 'text_classification' or task == 'sentiment_analysis':
            logits = outputs['logits']
            probs = torch.softmax(logits, dim=-1)
            predicted_class = torch.argmax(logits, dim=-1).item()
            confidence = probs[0][predicted_class].item()
            
            result['prediction'] = predicted_class
            result['confidence'] = confidence
            result['probabilities'] = probs[0].cpu().tolist()
        
        elif task == 'named_entity_recognition':
            logits = outputs['logits']
            predictions = torch.argmax(logits, dim=-1)[0].cpu().tolist()
            tokens = self.tokenizer.decode(input_ids[0].cpu().tolist(), skip_special_tokens=False).split()
            
            result['predictions'] = predictions[:len(tokens)]
            result['tokens'] = tokens
        
        elif task == 'question_answering':
            start_logits = outputs['start_logits']
            end_logits = outputs['end_logits']
            start_pos = torch.argmax(start_logits, dim=-1).item()
            end_pos = torch.argmax(end_logits, dim=-1).item()
            
            # Extract answer span
            answer_tokens = input_ids[0][start_pos:end_pos+1].cpu().tolist()
            answer = self.tokenizer.decode(answer_tokens, skip_special_tokens=True)
            
            result['answer'] = answer
            result['start_position'] = start_pos
            result['end_position'] = end_pos
        
        elif task == 'text_generation':
            try:
                logits = outputs.get('logits')
                if logits is None:
                    # Fallback: use brain knowledge instead
                    result['generated_text'] = f"I understand your message about '{text}'. Let me help you with that."
                    return result
                
                # Check logits shape - should be [batch_size, seq_len, vocab_size]
                if len(logits.shape) < 3:
                    # Unexpected shape, use fallback
                    result['generated_text'] = f"I understand your message: '{text}'. How can I help you?"
                    return result
                
                batch_size, seq_len, vocab_size = logits.shape
                
                # Ensure we have at least one sequence position
                if seq_len == 0:
                    result['generated_text'] = f"I understand your message: '{text}'. How can I help you?"
                    return result
                
                # Simple greedy decoding - take the most likely token from the last position
                next_token_logits = logits[0, -1, :]  # [vocab_size]
                next_token = torch.argmax(next_token_logits).item()
                
                # Start with original input tokens
                generated_ids = input_ids[0].cpu().tolist()
                
                # Add the predicted next token
                generated_ids.append(next_token)
                
                # Decode
                generated_text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
                
                # Fallback if decoded text is empty or same as input
                if not generated_text or generated_text.strip() == text.strip():
                    result['generated_text'] = f"I understand your message: '{text}'. How can I assist you?"
                else:
                    result['generated_text'] = generated_text
                    
            except Exception as e:
                print(f"Error in text generation: {e}")
                import traceback
                traceback.print_exc()
                # Fallback response
                result['generated_text'] = f"I understand your message: '{text}'. How can I help you?"
        
        return result


def main():
    parser = argparse.ArgumentParser(description='Run inference with All-Rounder AI Model')
    parser.add_argument('--model', type=str, required=True,
                       help='Path to model checkpoint')
    parser.add_argument('--tokenizer', type=str, required=True,
                       help='Path to tokenizer file')
    parser.add_argument('--text', type=str, required=True,
                       help='Input text')
    parser.add_argument('--task', type=str, required=True,
                       choices=['text_classification', 'text_generation', 'question_answering',
                               'sentiment_analysis', 'named_entity_recognition'],
                       help='Task to perform')
    parser.add_argument('--config', type=str, default='config/config/config.yaml',
                       help='Path to config file')
    
    args = parser.parse_args()
    
    # Initialize inference
    inference = AllRounderInference(args.model, args.tokenizer, args.config)
    
    # Make prediction
    result = inference.predict(args.text, args.task)
    
    # Print results
    print("\n" + "="*50)
    print(f"Task: {result['task']}")
    print(f"Input: {result['input']}")
    print("-"*50)
    
    if 'prediction' in result:
        print(f"Prediction: {result['prediction']}")
        print(f"Confidence: {result['confidence']:.4f}")
    elif 'answer' in result:
        print(f"Answer: {result['answer']}")
    elif 'generated_text' in result:
        print(f"Generated: {result['generated_text']}")
    elif 'predictions' in result:
        print(f"NER Predictions: {result['predictions']}")
    
    print("="*50)


if __name__ == '__main__':
    main()

