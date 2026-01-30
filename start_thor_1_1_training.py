#!/usr/bin/env python3
"""
Thor 1.1 Continuous Training Orchestrator
Complete system for training, monitoring, and deploying Thor 1.1 with 50M+ parameters
"""

import os
import sys
import json
import time
import signal
import argparse
from pathlib import Path
from datetime import datetime
import subprocess
import threading
import logging

# Add project paths
sys.path.append('apps/chatbot')
sys.path.append('models/thor-1.1')

from apps.tools.monitor_training import get_training_monitor, start_training_monitor, stop_training_monitor
from apps.chatbot.services.auto_trainer import start_auto_trainer, stop_auto_trainer, get_auto_trainer_status


class ThorTrainingOrchestrator:
    """Orchestrator for complete Thor 1.1 training ecosystem"""

    def __init__(self, config_path: str = "models/thor-1.1/config/config.yaml"):
        self.config_path = Path(config_path)
        self.is_running = False
        self.processes = {}
        self.threads = {}

        # Setup logging
        self.setup_logging()

        # Load configuration
        self.load_config()

    def setup_logging(self):
        """Setup comprehensive logging"""
        log_file = Path("data/logs/thor_1_1_orchestrator.log")

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - ThorOrchestrator - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_config(self):
        """Load training configuration"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except:
            # Fallback configuration
            self.config = {
                'training': {
                    'continuous_interval': 30,
                    'max_conversations_per_cycle': 100,
                    'batch_size': 8,
                    'learning_rate': 1e-4
                },
                'monitoring': {
                    'enabled': True,
                    'log_interval': 60
                },
                'evaluation': {
                    'enabled': True,
                    'eval_interval': 3600  # Every hour
                }
            }

    def start_training_pipeline(self):
        """Start the complete training pipeline"""
        self.logger.info("Starting Thor 1.1 Training Pipeline")
        self.is_running = True

        try:
            # 1. Start training monitoring
            self.logger.info("Starting training monitor...")
            self.training_monitor = start_training_monitor("thor-1.1")

            # 2. Start auto trainer service
            self.logger.info("Starting auto trainer service...")
            interval = self.config['training']['continuous_interval']
            start_auto_trainer(interval)

            # 3. Start initial model training if no model exists
            if not self.check_model_exists():
                self.logger.info("No existing model found, starting initial training...")
                self.start_initial_training()
            else:
                self.logger.info("Existing model found, starting continuous training mode")

            # 4. Start evaluation service
            if self.config.get('evaluation', {}).get('enabled', True):
                self.start_evaluation_service()

            # 5. Start health monitoring
            self.start_health_monitor()

            self.logger.info("Thor 1.1 Training Pipeline started successfully!")
            self.logger.info(f"- Continuous training every {interval} minutes")
            self.logger.info("- Auto trainer monitoring conversations")
            self.logger.info("- Training metrics being collected")
            self.logger.info("- Model evaluation scheduled")

        except Exception as e:
            self.logger.error(f"Failed to start training pipeline: {e}")
            self.stop_training_pipeline()
            raise

    def stop_training_pipeline(self):
        """Stop the complete training pipeline"""
        self.logger.info("Stopping Thor 1.1 Training Pipeline")
        self.is_running = False

        # Stop auto trainer
        try:
            stop_auto_trainer()
        except:
            pass

        # Stop training monitor
        try:
            stop_training_monitor()
        except:
            pass

        # Stop any running processes
        for name, process in self.processes.items():
            try:
                if process and process.poll() is None:
                    self.logger.info(f"Terminating {name} process")
                    process.terminate()
                    process.wait(timeout=10)
            except:
                try:
                    process.kill()
                except:
                    pass

        # Stop threads
        for name, thread in self.threads.items():
            try:
                if thread and thread.is_alive():
                    self.logger.info(f"Stopping {name} thread")
                    thread.join(timeout=5)
            except:
                pass

        self.logger.info("Thor 1.1 Training Pipeline stopped")

    def check_model_exists(self) -> bool:
        """Check if Thor 1.1 model exists"""
        model_paths = [
            "models/thor-1.1/models/final_model.pt",
            "models/thor-1.1/checkpoints/best_model.pt"
        ]

        for path in model_paths:
            if Path(path).exists():
                return True
        return False

    def start_initial_training(self):
        """Start initial model training"""
        self.logger.info("Starting initial Thor 1.1 model training")

        cmd = [
            sys.executable, "apps/tools/train_thor_1_1.py",
            "--config", str(self.config_path),
            "--train_data", "data/training_data/train.json",
            "--val_data", "data/training_data/val.json",
            "--num_epochs", "3",  # Initial training with fewer epochs
            "--batch_size", str(self.config['training']['batch_size']),
            "--save_every", "1",
            "--continuous"  # Enable continuous mode
        ]

        try:
            self.processes['initial_training'] = subprocess.Popen(
                cmd,
                cwd=Path.cwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.logger.info("Initial training process started")
        except Exception as e:
            self.logger.error(f"Failed to start initial training: {e}")

    def start_evaluation_service(self):
        """Start periodic evaluation service"""
        def evaluation_worker():
            while self.is_running:
                try:
                    time.sleep(self.config['evaluation']['eval_interval'])

                    if not self.is_running:
                        break

                    self.logger.info("Running periodic evaluation")
                    self.run_evaluation()

                except Exception as e:
                    self.logger.error(f"Evaluation error: {e}")
                    time.sleep(60)

        thread = threading.Thread(target=evaluation_worker, daemon=True)
        thread.start()
        self.threads['evaluation'] = thread
        self.logger.info("Evaluation service started")

    def run_evaluation(self):
        """Run model evaluation"""
        try:
            cmd = [
                sys.executable, "apps/tools/evaluate_thor_1_1.py",
                "--model_path", "models/thor-1.1/checkpoints/best_model.pt",
                "--config_path", str(self.config_path),
                "--output_dir", "data/metrics",
                "--text_generation_data", "data/training_data/val.json",
                "--classification_data", "data/training_data/val.json"
            ]

            result = subprocess.run(
                cmd,
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )

            if result.returncode == 0:
                self.logger.info("Evaluation completed successfully")
            else:
                self.logger.warning(f"Evaluation failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            self.logger.warning("Evaluation timed out")
        except Exception as e:
            self.logger.error(f"Evaluation error: {e}")

    def start_health_monitor(self):
        """Start health monitoring"""
        def health_worker():
            while self.is_running:
                try:
                    time.sleep(300)  # Check every 5 minutes

                    if not self.is_running:
                        break

                    # Check auto trainer status
                    trainer_status = get_auto_trainer_status()
                    if trainer_status.get('is_running'):
                        self.logger.debug("Auto trainer is healthy")
                    else:
                        self.logger.warning("Auto trainer is not running")

                    # Check model file exists
                    if not self.check_model_exists():
                        self.logger.warning("Model file not found - training may have failed")
                    else:
                        self.logger.debug("Model file exists")

                    # Check disk space
                    import shutil
                    disk_usage = shutil.disk_usage("/")
                    free_gb = disk_usage.free / (1024**3)
                    if free_gb < 1.0:  # Less than 1GB free
                        self.logger.warning(".1f")

                except Exception as e:
                    self.logger.error(f"Health check error: {e}")
                    time.sleep(60)

        thread = threading.Thread(target=health_worker, daemon=True)
        thread.start()
        self.threads['health'] = thread
        self.logger.info("Health monitoring started")

    def get_system_status(self) -> dict:
        """Get comprehensive system status"""
        status = {
            'orchestrator_running': self.is_running,
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }

        # Auto trainer status
        try:
            status['components']['auto_trainer'] = get_auto_trainer_status()
        except:
            status['components']['auto_trainer'] = {'error': 'Failed to get status'}

        # Training monitor status
        try:
            monitor = get_training_monitor("thor-1.1")
            status['components']['training_monitor'] = monitor.get_training_stats()
        except:
            status['components']['training_monitor'] = {'error': 'Failed to get status'}

        # Model status
        status['components']['model'] = {
            'exists': self.check_model_exists(),
            'path': 'models/thor-1.1/models/final_model.pt'
        }

        # Processes status
        status['components']['processes'] = {}
        for name, process in self.processes.items():
            status['components']['processes'][name] = {
                'running': process.poll() is None if process else False,
                'pid': process.pid if process else None
            }

        return status

    def save_status_report(self):
        """Save status report to file"""
        status = self.get_system_status()

        status_file = Path("data/logs/thor_1_1_status.json")
        status_file.parent.mkdir(parents=True, exist_ok=True)

        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2, default=str)

        self.logger.info(f"Status report saved to {status_file}")


def main():
    parser = argparse.ArgumentParser(description="Thor 1.1 Training Orchestrator")
    parser.add_argument("--config", type=str, default="models/thor-1.1/config/config.yaml",
                       help="Configuration file path")
    parser.add_argument("--action", type=str, choices=['start', 'stop', 'status', 'restart'],
                       default='start', help="Action to perform")
    parser.add_argument("--daemon", action="store_true",
                       help="Run in daemon mode (background)")

    args = parser.parse_args()

    orchestrator = ThorTrainingOrchestrator(args.config)

    if args.action == 'start':
        if args.daemon:
            # Daemon mode - fork and run in background
            try:
                pid = os.fork()
                if pid > 0:
                    # Parent process
                    print(f"Thor 1.1 orchestrator started in background (PID: {pid})")
                    sys.exit(0)
            except OSError as e:
                print(f"Fork failed: {e}")
                sys.exit(1)

        # Start the orchestrator
        def signal_handler(signum, frame):
            print("Received shutdown signal, stopping orchestrator...")
            orchestrator.stop_training_pipeline()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            orchestrator.start_training_pipeline()

            # Keep running and periodically save status
            while orchestrator.is_running:
                time.sleep(60)  # Check every minute
                orchestrator.save_status_report()

        except KeyboardInterrupt:
            print("Interrupted by user")
        finally:
            orchestrator.stop_training_pipeline()

    elif args.action == 'stop':
        print("Stopping Thor 1.1 orchestrator...")
        orchestrator.stop_training_pipeline()
        print("Orchestrator stopped")

    elif args.action == 'status':
        status = orchestrator.get_system_status()
        print("Thor 1.1 System Status:")
        print(json.dumps(status, indent=2, default=str))

    elif args.action == 'restart':
        print("Restarting Thor 1.1 orchestrator...")
        orchestrator.stop_training_pipeline()
        time.sleep(2)
        orchestrator.start_training_pipeline()
        print("Orchestrator restarted")


if __name__ == "__main__":
    main()