"""
Auto Trainer Service for Thor 1.1
Continuous learning system that monitors conversations and trains the model automatically
"""

import os
import sys
import json
import time
import threading
import schedule
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import subprocess
import signal
import psutil

# Add model paths
sys.path.append('../../../models/thor-1.1')
sys.path.append('../../../models/thor-1.0')

from config import CHATS_DIR, CONVERSATIONS_DIR, DATA_ROOT


class AutoTrainer:
    """Automatic training service for Thor 1.1"""

    def __init__(self, training_interval_minutes: int = 30, max_conversations_per_cycle: int = 100):
        self.training_interval = training_interval_minutes
        self.max_conversations = max_conversations_per_cycle
        self.is_running = False
        self.training_process = None

        # Setup directories
        self.chats_dir = Path(CHATS_DIR)
        self.conversations_dir = Path(CONVERSATIONS_DIR)
        self.training_data_dir = Path("data/training_data")
        self.models_dir = Path("models/thor-1.1")
        self.logs_dir = Path("data/logs")

        # Ensure directories exist
        self.training_data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.setup_logging()

        # Training state
        self.last_training_time = datetime.now()
        self.conversations_processed = 0
        self.training_cycles_completed = 0

    def setup_logging(self):
        """Setup logging for auto trainer"""
        log_file = self.logs_dir / "auto_trainer.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - AutoTrainer - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def start(self):
        """Start the auto training service"""
        self.logger.info(f"Starting Auto Trainer with {self.training_interval} minute intervals")
        self.is_running = True

        # Schedule training
        schedule.every(self.training_interval).minutes.do(self.training_cycle)

        # Start background thread
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()

        # Run initial training cycle
        self.training_cycle()

    def stop(self):
        """Stop the auto training service"""
        self.logger.info("Stopping Auto Trainer")
        self.is_running = False

        if self.training_process and self.training_process.poll() is None:
            self.logger.info("Terminating training process")
            self.training_process.terminate()
            try:
                self.training_process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                self.training_process.kill()

        schedule.clear()

    def _run_scheduler(self):
        """Run the scheduler in background thread"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    def training_cycle(self):
        """Execute one training cycle"""
        try:
            self.logger.info("Starting training cycle")

            # Collect new conversations
            new_conversations = self.collect_new_conversations()

            if not new_conversations:
                self.logger.info("No new conversations found, skipping training")
                return

            self.logger.info(f"Found {len(new_conversations)} new conversations")

            # Convert conversations to training data
            training_examples = self.convert_conversations_to_training_data(new_conversations)

            if not training_examples:
                self.logger.info("No valid training examples generated, skipping training")
                return

            # Save training data
            self.save_training_data(training_examples)

            # Start training process
            self.start_training_process()

            # Update statistics
            self.training_cycles_completed += 1
            self.conversations_processed += len(new_conversations)
            self.last_training_time = datetime.now()

            self.logger.info(f"Training cycle completed. Processed {len(new_conversations)} conversations")

        except Exception as e:
            self.logger.error(f"Training cycle failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def collect_new_conversations(self) -> List[Dict]:
        """Collect new conversations since last training"""
        new_conversations = []

        # Check chats directory
        if self.chats_dir.exists():
            for chat_file in self.chats_dir.glob("*.json"):
                try:
                    with open(chat_file, 'r', encoding='utf-8') as f:
                        chat_data = json.load(f)

                    # Check if chat was modified since last training
                    modified_time = datetime.fromtimestamp(chat_file.stat().st_mtime)
                    if modified_time > self.last_training_time:
                        new_conversations.append(chat_data)

                except Exception as e:
                    self.logger.warning(f"Failed to read chat file {chat_file}: {e}")

        # Check conversations archive
        if self.conversations_dir.exists():
            for conv_file in self.conversations_dir.glob("*.json"):
                try:
                    with open(conv_file, 'r', encoding='utf-8') as f:
                        conv_data = json.load(f)

                    modified_time = datetime.fromtimestamp(conv_file.stat().st_mtime)
                    if modified_time > self.last_training_time:
                        new_conversations.append(conv_data)

                except Exception as e:
                    self.logger.warning(f"Failed to read conversation file {conv_file}: {e}")

        # Limit number of conversations to process
        if len(new_conversations) > self.max_conversations:
            new_conversations = new_conversations[-self.max_conversations:]

        return new_conversations

    def convert_conversations_to_training_data(self, conversations: List[Dict]) -> List[Dict]:
        """Convert conversations to training examples"""
        training_examples = []

        for conversation in conversations:
            if not isinstance(conversation, dict) or 'messages' not in conversation:
                continue

            messages = conversation.get('messages', [])

            # Process conversation turns
            for i in range(len(messages) - 1):
                user_msg = messages[i]
                assistant_msg = messages[i + 1]

                # Only process user -> assistant pairs
                if (user_msg.get('role') == 'user' and
                    assistant_msg.get('role') == 'assistant'):

                    user_text = user_msg.get('content', '').strip()
                    assistant_text = assistant_msg.get('content', '').strip()

                    if not user_text or not assistant_text:
                        continue

                    # Create text generation example
                    # Format: "User: {query}\nAssistant: {response}"
                    full_text = f"User: {user_text}\nAssistant: {assistant_text}"

                    training_examples.append({
                        'task': 'text_generation',
                        'text': full_text,
                        'source': 'conversation',
                        'timestamp': conversation.get('timestamp', datetime.now().isoformat())
                    })

                    # Also create classification example if sentiment can be inferred
                    if self._extract_sentiment_label(assistant_text):
                        training_examples.append({
                            'task': 'sentiment_analysis',
                            'text': assistant_text,
                            'label': self._extract_sentiment_label(assistant_text),
                            'source': 'conversation',
                            'timestamp': conversation.get('timestamp', datetime.now().isoformat())
                        })

        return training_examples

    def _extract_sentiment_label(self, text: str) -> Optional[int]:
        """Extract sentiment label from text (simple heuristic)"""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'like', 'happy']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'dislike', 'sad', 'angry', 'frustrated']

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            return 1  # Positive
        elif negative_count > positive_count:
            return 0  # Negative
        else:
            return None  # Neutral or unclear

    def save_training_data(self, training_examples: List[Dict]):
        """Save training examples to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversations_{timestamp}.json"

        output_file = self.training_data_dir / filename

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(training_examples, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved {len(training_examples)} training examples to {output_file}")

        except Exception as e:
            self.logger.error(f"Failed to save training data: {e}")

    def start_training_process(self):
        """Start the training process"""
        try:
            # Check if training is already running
            if self.training_process and self.training_process.poll() is None:
                self.logger.info("Training process already running, skipping")
                return

            # Prepare training command
            train_script = Path("apps/tools/train_thor_1_1.py")
            config_path = self.models_dir / "config" / "config.yaml"

            if not train_script.exists():
                self.logger.error(f"Training script not found: {train_script}")
                return

            if not config_path.exists():
                self.logger.error(f"Config file not found: {config_path}")
                return

            # Find latest training data
            training_files = list(self.training_data_dir.glob("conversations_*.json"))
            if not training_files:
                self.logger.warning("No training data files found")
                return

            latest_training_data = max(training_files, key=lambda x: x.stat().st_mtime)

            # Build command
            cmd = [
                sys.executable,
                str(train_script),
                "--config", str(config_path),
                "--train_data", str(latest_training_data),
                "--num_epochs", "1",  # One epoch per cycle
                "--batch_size", "4",  # Smaller batch for continuous training
                "--no_wandb",  # Disable wandb for automated training
                "--continuous"  # Enable continuous mode (short training)
            ]

            # Check for existing model
            model_files = list((self.models_dir / "checkpoints").glob("best_model.pt"))
            if model_files:
                latest_model = max(model_files, key=lambda x: x.stat().st_mtime)
                cmd.extend(["--model_path", str(latest_model)])

            self.logger.info(f"Starting training with command: {' '.join(cmd)}")

            # Start training process
            self.training_process = subprocess.Popen(
                cmd,
                cwd=Path.cwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Monitor training process
            self._monitor_training_process()

        except Exception as e:
            self.logger.error(f"Failed to start training process: {e}")

    def _monitor_training_process(self):
        """Monitor the training process"""
        if not self.training_process:
            return

        try:
            # Wait for process to complete with timeout
            stdout, stderr = self.training_process.communicate(timeout=3600)  # 1 hour timeout

            if self.training_process.returncode == 0:
                self.logger.info("Training process completed successfully")
                if stdout:
                    self.logger.debug(f"Training stdout: {stdout}")
            else:
                self.logger.error(f"Training process failed with return code {self.training_process.returncode}")
                if stderr:
                    self.logger.error(f"Training stderr: {stderr}")

        except subprocess.TimeoutExpired:
            self.logger.warning("Training process timed out")
            self.training_process.kill()
        except Exception as e:
            self.logger.error(f"Error monitoring training process: {e}")

        self.training_process = None

    def get_status(self) -> Dict[str, Any]:
        """Get current status of auto trainer"""
        is_training = self.training_process is not None and self.training_process.poll() is None

        return {
            'is_running': self.is_running,
            'is_training': is_training,
            'last_training_time': self.last_training_time.isoformat(),
            'training_cycles_completed': self.training_cycles_completed,
            'conversations_processed': self.conversations_processed,
            'training_interval_minutes': self.training_interval,
            'next_training_time': (self.last_training_time + timedelta(minutes=self.training_interval)).isoformat()
        }


def get_auto_trainer(training_interval_minutes: int = 30) -> AutoTrainer:
    """Get or create auto trainer instance"""
    if not hasattr(get_auto_trainer, '_instance'):
        get_auto_trainer._instance = AutoTrainer(training_interval_minutes)

    return get_auto_trainer._instance


# Global auto trainer instance
_auto_trainer = None


def start_auto_trainer(interval_minutes: int = 30):
    """Start the auto trainer service"""
    global _auto_trainer

    if _auto_trainer is None:
        _auto_trainer = AutoTrainer(interval_minutes)

    if not _auto_trainer.is_running:
        _auto_trainer.start()
        print(f"Auto trainer started with {interval_minutes} minute intervals")


def stop_auto_trainer():
    """Stop the auto trainer service"""
    global _auto_trainer

    if _auto_trainer and _auto_trainer.is_running:
        _auto_trainer.stop()
        print("Auto trainer stopped")


def get_auto_trainer_status():
    """Get auto trainer status"""
    global _auto_trainer

    if _auto_trainer:
        return _auto_trainer.get_status()
    else:
        return {'is_running': False, 'error': 'Auto trainer not initialized'}


if __name__ == "__main__":
    # Run auto trainer directly
    import argparse

    parser = argparse.ArgumentParser(description="Thor 1.1 Auto Trainer")
    parser.add_argument("--interval", type=int, default=30, help="Training interval in minutes")
    parser.add_argument("--max-conversations", type=int, default=100, help="Max conversations per cycle")

    args = parser.parse_args()

    trainer = AutoTrainer(args.interval, args.max_conversations)

    def signal_handler(signum, frame):
        print("Received shutdown signal, stopping auto trainer...")
        trainer.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        trainer.start()

        # Keep running
        while trainer.is_running:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        trainer.stop()