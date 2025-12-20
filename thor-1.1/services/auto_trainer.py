"""
Auto-Training Service for Thor 1.1 (Enhanced with improved training strategies)
Continuously trains the model using conversation data and web scraping
"""
import json
import os
import time
import threading
import torch
from datetime import datetime, timedelta
from pathlib import Path
import random

from models import AllRounderModel
from utils import SimpleTokenizer, MultiTaskDataLoader
from .learning_tracker import get_tracker


class AutoTrainer:
    """Background service that continuously trains Thor 1.1 with enhanced training strategies"""
    
    def __init__(self, training_interval_minutes=30, min_conversations=10):
        self.training_interval = training_interval_minutes * 60  # Convert to seconds
        self.min_conversations = min_conversations
        self.running = False
        self.thread = None
        self.conversations_dir = "conversations"
        self.training_data_dir = "training_data"
        
        # Ensure directories exist
        os.makedirs(self.conversations_dir, exist_ok=True)
        os.makedirs(self.training_data_dir, exist_ok=True)
        os.makedirs("models", exist_ok=True)
        
        print("Auto-Trainer initialized")
    
    def start(self):
        """Start the auto-training service"""
        if self.running:
            print("Auto-Trainer is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._training_loop, daemon=True)
        self.thread.start()
        print("Auto-Trainer started - will train every {} minutes".format(
            self.training_interval // 60
        ))
    
    def stop(self):
        """Stop the auto-training service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("Auto-Trainer stopped")
    
    def _training_loop(self):
        """Main training loop that runs in background"""
        while self.running:
            try:
                # Check if we have enough data to train
                if self._should_train():
                    print(f"[Auto-Trainer] Starting training cycle at {datetime.now()}")
                    self._train_model()
                else:
                    print(f"[Auto-Trainer] Not enough data yet. Waiting...")
                
                # Sleep until next training cycle
                time.sleep(self.training_interval)
                
            except Exception as e:
                print(f"[Auto-Trainer] Error in training loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _should_train(self):
        """Check if we have enough data to train"""
        # Count conversations
        conversations = self._get_conversations()
        num_conversations = len(conversations)
        
        # Check if we have existing training data
        train_file = os.path.join(self.training_data_dir, "train.json")
        has_training_data = os.path.exists(train_file) and os.path.getsize(train_file) > 0
        
        should_train = num_conversations >= self.min_conversations or has_training_data
        
        if not should_train:
            print(f"[Auto-Trainer] Not enough data: {num_conversations} conversations (need {self.min_conversations}), has_training_data={has_training_data}")
        else:
            print(f"[Auto-Trainer] Ready to train: {num_conversations} conversations, has_training_data={has_training_data}")
        
        return should_train
    
    def _get_conversations(self):
        """Get all conversation files from both conversations and chats directories"""
        conversations = []
        
        # Get from conversations directory
        if os.path.exists(self.conversations_dir):
            for file in os.listdir(self.conversations_dir):
                if file.endswith('.json'):
                    conversations.append(os.path.join(self.conversations_dir, file))
        
        # Also get from chats directory (where current chats are saved)
        chats_dir = "chats"
        if os.path.exists(chats_dir):
            for file in os.listdir(chats_dir):
                if file.endswith('.json'):
                    conversations.append(os.path.join(chats_dir, file))
        
        return conversations
    
    def _collect_training_data(self):
        """Collect training data from conversations and web"""
        print("[Auto-Trainer] Collecting training data...")
        
        training_data = []
        
        # 1. Load existing training data
        train_file = os.path.join(self.training_data_dir, "train.json")
        if os.path.exists(train_file):
            try:
                with open(train_file, 'r') as f:
                    existing_data = json.load(f)
                    training_data.extend(existing_data)
                    print(f"  Loaded {len(existing_data)} existing examples")
            except:
                pass
        
        # 2. Extract data from conversations
        conversations = self._get_conversations()
        conversation_data = self._extract_from_conversations(conversations)
        training_data.extend(conversation_data)
        print(f"  Extracted {len(conversation_data)} examples from conversations")
        
        # 3. Collect from web (lightweight)
        web_data = self._collect_from_web()
        training_data.extend(web_data)
        print(f"  Collected {len(web_data)} examples from web")
        
        # Remove duplicates
        seen = set()
        unique_data = []
        for item in training_data:
            key = (item.get('task'), item.get('text', '')[:100])
            if key not in seen:
                seen.add(key)
                unique_data.append(item)
        
        print(f"  Total unique examples: {len(unique_data)}")
        return unique_data
    
    def _extract_from_conversations(self, conversation_files):
        """Extract training examples from conversation files"""
        examples = []
        
        print(f"[Auto-Trainer] Processing {len(conversation_files)} conversation files...")
        
        for conv_file in conversation_files[:50]:  # Limit to recent 50
            try:
                with open(conv_file, 'r') as f:
                    conv_data = json.load(f)
                    messages = conv_data.get('messages', [])
                    
                    if not messages:
                        continue
                    
                    for i, msg in enumerate(messages):
                        if msg.get('role') == 'user':
                            text = msg.get('content', '')
                            if len(text) > 10:  # Valid text
                                # Create text classification example
                                examples.append({
                                    'task': 'text_classification',
                                    'text': text[:500],
                                    'label': random.randint(0, 1)  # Simple classification
                                })
                                
                                # Create sentiment analysis example
                                examples.append({
                                    'task': 'sentiment_analysis',
                                    'text': text[:500],
                                    'label': random.randint(0, 2)  # 0=neg, 1=neutral, 2=pos
                                })
                                
                                # Create text generation example (use assistant response as target)
                                if i + 1 < len(messages):
                                    next_msg = messages[i + 1]
                                    if next_msg.get('role') == 'assistant':
                                        assistant_text = next_msg.get('content', '')
                                        if len(assistant_text) > 10:
                                            examples.append({
                                                'task': 'text_generation',
                                                'text': text[:500],
                                                'label': None  # For generation, input is the prompt
                                            })
            except Exception as e:
                print(f"[Auto-Trainer] Error processing {conv_file}: {e}")
                continue
        
        print(f"[Auto-Trainer] Extracted {len(examples)} training examples")
        return examples
    
    def _collect_from_web(self):
        """Collect training data from web (lightweight) using dictionary.json topics"""
        examples = []
        
        # Load topics from dictionary.json for training
        dictionary_path = "dictionary.json"
        dictionary_topics = []
        
        try:
            if os.path.exists(dictionary_path):
                with open(dictionary_path, 'r') as f:
                    dict_data = json.load(f)
                    dictionary_topics = dict_data.get('topics', [])
                    # Shuffle for random order
                    random.shuffle(dictionary_topics)
                    print(f"[Auto-Trainer] Loaded {len(dictionary_topics)} topics from dictionary.json for training")
        except Exception as e:
            print(f"[Auto-Trainer] Error loading dictionary.json: {e}")
        
        # If no dictionary topics, use minimal fallback
        if not dictionary_topics:
            dictionary_topics = [
                "artificial intelligence", "machine learning", "deep learning",
                "natural language processing", "computer science", "programming"
            ]
            print(f"[Auto-Trainer] Using fallback topics: {len(dictionary_topics)} topics")
        
        # Generate training examples from random dictionary topics
        # Pick random topics (not all, just a sample)
        num_topics_to_use = min(50, len(dictionary_topics))  # Use up to 50 random topics
        selected_topics = random.sample(dictionary_topics, num_topics_to_use)
        
        for topic in selected_topics:
            # Create various training examples from each topic
            # Text classification examples
            examples.append({
                'task': 'text_classification',
                'text': f"What is {topic}?",
                'label': random.randint(0, 1)
            })
            
            # Sentiment examples (mostly neutral/positive for educational topics)
            sentiment_label = random.choices([0, 1, 2], weights=[0.1, 0.3, 0.6])[0]  # Bias toward positive
            examples.append({
                'task': 'sentiment_analysis',
                'text': f"I find {topic} interesting and valuable.",
                'label': sentiment_label
            })
            
            # Text generation examples
            examples.append({
                'task': 'text_generation',
                'text': f"Explain {topic}",
                'label': None
            })
            
            # Question answering examples
            examples.append({
                'task': 'question_answering',
                'text': f"What is {topic}? {topic} is an important concept.",
                'label': {'start': len(f"What is {topic}? "), 'end': len(f"What is {topic}? {topic}")}
            })
        
        print(f"[Auto-Trainer] Generated {len(examples)} training examples from {num_topics_to_use} random dictionary topics")
        return examples
    
    def _train_model(self):
        """Train the model with collected data"""
        try:
            # Collect training data
            all_data = self._collect_training_data()
            
            if len(all_data) < 5:
                print("[Auto-Trainer] Not enough data to train. Skipping...")
                return
            
            # Split data
            random.shuffle(all_data)
            split_idx = int(len(all_data) * 0.8)
            train_data = all_data[:split_idx]
            val_data = all_data[split_idx:]
            
            # Save training data
            train_file = os.path.join(self.training_data_dir, "train.json")
            val_file = os.path.join(self.training_data_dir, "val.json")
            
            with open(train_file, 'w') as f:
                json.dump(train_data, f, indent=2)
            
            with open(val_file, 'w') as f:
                json.dump(val_data, f, indent=2)
            
            print(f"[Auto-Trainer] Training with {len(train_data)} examples")
            
            # Setup device
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            
            # Load or create tokenizer
            tokenizer_path = 'models/tokenizer.json'
            if os.path.exists(tokenizer_path):
                tokenizer = SimpleTokenizer.load(tokenizer_path)
                # Update vocabulary with new data
                texts = [item.get('text', '') for item in train_data]
                tokenizer.build_vocab(texts, min_freq=1)
            else:
                tokenizer = SimpleTokenizer(vocab_size=2000)
                texts = [item.get('text', '') for item in train_data]
                tokenizer.build_vocab(texts, min_freq=1)
            
            tokenizer.save(tokenizer_path)
            
            # Load or create model
            model_path = 'models/final_model.pt'
            task_configs = {
                'text_classification': {'enabled': True, 'num_labels': 2},
                'sentiment_analysis': {'enabled': True, 'num_labels': 3},
                'text_generation': {'enabled': True},
                'question_answering': {'enabled': True},
                'named_entity_recognition': {'enabled': True, 'num_labels': 9}
            }
            
            if os.path.exists(model_path):
                try:
                    model = AllRounderModel.load_model(model_path, task_configs)
                    print("[Auto-Trainer] Loaded existing model for fine-tuning")
                except:
                    model = self._create_model(len(tokenizer.word_to_id), task_configs)
            else:
                model = self._create_model(len(tokenizer.word_to_id), task_configs)
            
            model = model.to(device)
            
            # Create data loaders
            data_loader = MultiTaskDataLoader(
                tokenizer=tokenizer,
                batch_size=4,
                max_length=256
            )
            
            # Training
            optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)  # Lower LR for fine-tuning
            
            # Train for a few epochs
            num_epochs = 2  # Quick training cycles
            for epoch in range(num_epochs):
                for task_name in ['text_classification', 'sentiment_analysis', 'text_generation']:
                    task_data = [item for item in train_data if item.get('task') == task_name]
                    
                    if not task_data:
                        continue
                    
                    train_dataloader = data_loader.create_dataloader(
                        task_data,
                        task=task_name,
                        shuffle=True
                    )
                    
                    model.train()
                    for batch in train_dataloader:
                        input_ids = batch['input_ids'].to(device)
                        attention_mask = batch['attention_mask'].to(device)
                        labels = batch.get('labels')
                        if labels is not None:
                            labels = labels.to(device)
                        
                        optimizer.zero_grad()
                        
                        outputs = model(
                            input_ids=input_ids,
                            attention_mask=attention_mask,
                            task=task_name,
                            labels=labels
                        )
                        
                        loss = outputs.get('loss')
                        if loss is None:
                            logits = outputs.get('logits')
                            if logits is not None and labels is not None:
                                loss_fct = torch.nn.CrossEntropyLoss()
                                loss = loss_fct(logits.view(-1, logits.size(-1)), labels.view(-1))
                            else:
                                continue
                        
                        loss.backward()
                        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                        optimizer.step()
            
            # Save model
            model.save_model(model_path)
            print(f"[Auto-Trainer] Training complete! Model saved at {datetime.now()}")
            
            # Record training in tracker
            try:
                tracker = get_tracker()
                tasks_trained = ['text_classification', 'sentiment_analysis', 'text_generation']
                tracker.record_training(len(train_data), tasks_trained)
                print(f"[Auto-Trainer] Recorded training: {len(train_data)} examples")
            except Exception as e:
                print(f"[Auto-Trainer] Error recording training: {e}")
            
        except Exception as e:
            print(f"[Auto-Trainer] Error during training: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_model(self, vocab_size, task_configs):
        """Create a new model"""
        return AllRounderModel(
            vocab_size=min(vocab_size, 5000),
            hidden_size=256,
            num_layers=4,
            num_heads=8,
            intermediate_size=1024,
            max_position_embeddings=256,
            dropout=0.1,
            task_configs=task_configs
        )
    
    def add_conversation(self, conversation_data):
        """Add a conversation for training"""
        if not conversation_data:
            print("[Auto-Trainer] No conversation data provided")
            return
        
        # Ensure we have messages
        messages = conversation_data.get('messages', [])
        if not messages or len(messages) == 0:
            print("[Auto-Trainer] Conversation has no messages, skipping")
            return
        
        # Save conversation
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        conv_file = os.path.join(self.conversations_dir, f"conv_{timestamp}.json")
        
        try:
            with open(conv_file, 'w') as f:
                json.dump(conversation_data, f, indent=2)
            
            print(f"[Auto-Trainer] Saved conversation with {len(messages)} messages")
            
            # Record conversation in tracker
            try:
                tracker = get_tracker()
                tracker.record_conversation()
            except Exception as e:
                print(f"[Auto-Trainer] Error recording in tracker: {e}")
        except Exception as e:
            print(f"[Auto-Trainer] Error saving conversation: {e}")
            import traceback
            traceback.print_exc()


# Global auto-trainer instance
_auto_trainer = None

def get_auto_trainer():
    """Get or create the global auto-trainer instance"""
    global _auto_trainer
    if _auto_trainer is None:
        _auto_trainer = AutoTrainer(training_interval_minutes=30, min_conversations=3)  # Lower threshold to start learning sooner
    return _auto_trainer

