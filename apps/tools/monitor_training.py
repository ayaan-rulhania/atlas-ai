#!/usr/bin/env python3
"""
Thor 1.1 Training Monitor
Comprehensive monitoring and metrics collection for training progress
"""

import os
import sys
import json
import time
import psutil
import GPUtil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import threading
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import torch
from torch.utils.tensorboard import SummaryWriter

# Setup matplotlib for headless operation
plt.switch_backend('Agg')
sns.set_style("darkgrid")

# Add model paths
sys.path.append('models/thor-1.1')


class TrainingMonitor:
    """Comprehensive training monitor for Thor 1.1"""

    def __init__(self, model_name: str = "thor-1.1", log_dir: str = "data/metrics",
                 tensorboard_dir: str = "data/metrics/tensorboard"):
        self.model_name = model_name
        self.log_dir = Path(log_dir)
        self.tensorboard_dir = Path(tensorboard_dir)

        # Create directories
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.tensorboard_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.setup_logging()

        # Initialize TensorBoard writer
        self.writer = SummaryWriter(str(self.tensorboard_dir))

        # Monitoring state
        self.training_start_time = None
        self.last_log_time = time.time()
        self.metrics_history = []
        self.system_stats_history = []

        # GPU monitoring
        self.gpu_available = torch.cuda.is_available()
        if self.gpu_available:
            self.gpu_count = torch.cuda.device_count()
        else:
            self.gpu_count = 0

        # Background monitoring thread
        self.monitoring_thread = None
        self.is_monitoring = False

    def setup_logging(self):
        """Setup logging configuration"""
        log_file = self.log_dir / f"{self.model_name}_training.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - TrainingMonitor - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def start_monitoring(self):
        """Start monitoring"""
        self.training_start_time = time.time()
        self.is_monitoring = True
        self.last_log_time = time.time()

        # Start background monitoring
        self.monitoring_thread = threading.Thread(target=self._background_monitor, daemon=True)
        self.monitoring_thread.start()

        self.logger.info(f"Started monitoring for {self.model_name}")

    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False

        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)

        # Final log
        self.log_system_stats()
        self.save_metrics_summary()

        self.writer.close()
        self.logger.info(f"Stopped monitoring for {self.model_name}")

    def log_training_step(self, step: int, loss: float, learning_rate: float,
                         grad_norm: Optional[float] = None, **kwargs):
        """Log training step metrics"""
        timestamp = time.time()

        metrics = {
            'timestamp': timestamp,
            'step': step,
            'loss': loss,
            'learning_rate': learning_rate,
            'grad_norm': grad_norm,
            **kwargs
        }

        # Add to history
        self.metrics_history.append(metrics)

        # Log to TensorBoard
        self.writer.add_scalar('train/loss', loss, step)
        self.writer.add_scalar('train/learning_rate', learning_rate, step)
        if grad_norm is not None:
            self.writer.add_scalar('train/grad_norm', grad_norm, step)

        # Log additional metrics
        for key, value in kwargs.items():
            if isinstance(value, (int, float)):
                self.writer.add_scalar(f'train/{key}', value, step)

        # Periodic logging
        if timestamp - self.last_log_time > 60:  # Log every minute
            self._log_progress(step, loss, learning_rate)
            self.last_log_time = timestamp

    def log_validation_step(self, step: int, metrics: Dict[str, float]):
        """Log validation metrics"""
        # Log to TensorBoard
        for key, value in metrics.items():
            self.writer.add_scalar(f'val/{key}', value, step)

        self.logger.info(f"Validation at step {step}: {metrics}")

    def log_epoch(self, epoch: int, train_loss: float, val_metrics: Optional[Dict[str, float]] = None,
                  epoch_time: Optional[float] = None):
        """Log epoch completion"""
        log_data = {
            'epoch': epoch,
            'train_loss': train_loss,
            'epoch_time': epoch_time,
            'timestamp': time.time()
        }

        if val_metrics:
            log_data.update({f'val_{k}': v for k, v in val_metrics.items()})

        # Log to TensorBoard
        self.writer.add_scalar('epoch/train_loss', train_loss, epoch)
        if val_metrics:
            for key, value in val_metrics.items():
                self.writer.add_scalar(f'epoch/val_{key}', value, epoch)
        if epoch_time:
            self.writer.add_scalar('epoch/time', epoch_time, epoch)

        self.logger.info(f"Epoch {epoch} completed - Train Loss: {train_loss:.4f}" +
                        (f" - Val: {val_metrics}" if val_metrics else "") +
                        (f" - Time: {epoch_time:.2f}s" if epoch_time else ""))

    def log_checkpoint(self, step: int, checkpoint_path: str, model_size_mb: float):
        """Log checkpoint saving"""
        self.writer.add_scalar('checkpoint/size_mb', model_size_mb, step)

        self.logger.info(f"Checkpoint saved at step {step}: {checkpoint_path} ({model_size_mb:.2f} MB)")

    def _background_monitor(self):
        """Background monitoring thread"""
        while self.is_monitoring:
            try:
                self.log_system_stats()
                time.sleep(30)  # Log every 30 seconds
            except Exception as e:
                self.logger.error(f"Background monitoring error: {e}")
                time.sleep(60)

    def log_system_stats(self):
        """Log system statistics"""
        try:
            stats = {
                'timestamp': time.time(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'memory_used_gb': psutil.virtual_memory().used / (1024**3)
            }

            # GPU stats
            if self.gpu_available:
                try:
                    gpu_stats = GPUtil.getGPUs()
                    for i, gpu in enumerate(gpu_stats):
                        stats[f'gpu_{i}_utilization'] = gpu.load * 100
                        stats[f'gpu_{i}_memory_used'] = gpu.memoryUsed
                        stats[f'gpu_{i}_memory_total'] = gpu.memoryTotal
                        stats[f'gpu_{i}_temperature'] = gpu.temperature
                except:
                    pass

            # Add to history
            self.system_stats_history.append(stats)

            # Log to TensorBoard
            for key, value in stats.items():
                if key != 'timestamp' and isinstance(value, (int, float)):
                    self.writer.add_scalar(f'system/{key}', value, int(stats['timestamp']))

        except Exception as e:
            self.logger.warning(f"Failed to collect system stats: {e}")

    def _log_progress(self, step: int, loss: float, learning_rate: float):
        """Log training progress"""
        elapsed = time.time() - self.training_start_time
        elapsed_str = str(timedelta(seconds=int(elapsed)))

        self.logger.info(
            f"Step {step} - Loss: {loss:.4f} - LR: {learning_rate:.6f} - "
            f"Elapsed: {elapsed_str}"
        )

    def save_metrics_summary(self):
        """Save comprehensive metrics summary"""
        if not self.metrics_history:
            return

        # Convert to DataFrame
        df = pd.DataFrame(self.metrics_history)

        # Calculate summary statistics
        summary = {
            'total_steps': len(df),
            'total_time_seconds': df['timestamp'].max() - df['timestamp'].min(),
            'avg_loss': df['loss'].mean(),
            'min_loss': df['loss'].min(),
            'final_loss': df['loss'].iloc[-1] if len(df) > 0 else None,
            'avg_learning_rate': df['learning_rate'].mean(),
            'final_learning_rate': df['learning_rate'].iloc[-1] if len(df) > 0 else None,
            'training_start': datetime.fromtimestamp(df['timestamp'].min()).isoformat(),
            'training_end': datetime.fromtimestamp(df['timestamp'].max()).isoformat()
        }

        # Add gradient norm stats if available
        if 'grad_norm' in df.columns:
            grad_norm_data = df['grad_norm'].dropna()
            if len(grad_norm_data) > 0:
                summary.update({
                    'avg_grad_norm': grad_norm_data.mean(),
                    'max_grad_norm': grad_norm_data.max(),
                    'min_grad_norm': grad_norm_data.min()
                })

        # Save summary
        summary_file = self.log_dir / f"{self.model_name}_training_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        # Save full metrics history
        metrics_file = self.log_dir / f"{self.model_name}_metrics_history.json"
        with open(metrics_file, 'w') as f:
            json.dump(self.metrics_history, f, indent=2, default=str)

        # Save system stats history
        if self.system_stats_history:
            system_file = self.log_dir / f"{self.model_name}_system_stats.json"
            with open(system_file, 'w') as f:
                json.dump(self.system_stats_history, f, indent=2, default=str)

        self.logger.info(f"Metrics summary saved to {summary_file}")

    def create_training_plots(self):
        """Create training visualization plots"""
        if not self.metrics_history:
            return

        df = pd.DataFrame(self.metrics_history)

        # Create plots directory
        plots_dir = self.log_dir / "plots"
        plots_dir.mkdir(exist_ok=True)

        # Loss plot
        if 'loss' in df.columns:
            plt.figure(figsize=(12, 6))
            plt.plot(df['step'], df['loss'], label='Training Loss', alpha=0.7)
            plt.xlabel('Training Step')
            plt.ylabel('Loss')
            plt.title('Training Loss Over Time')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.savefig(plots_dir / 'training_loss.png', dpi=150, bbox_inches='tight')
            plt.close()

        # Learning rate plot
        if 'learning_rate' in df.columns:
            plt.figure(figsize=(12, 6))
            plt.plot(df['step'], df['learning_rate'], label='Learning Rate', color='orange')
            plt.xlabel('Training Step')
            plt.ylabel('Learning Rate')
            plt.title('Learning Rate Schedule')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.yscale('log')
            plt.savefig(plots_dir / 'learning_rate.png', dpi=150, bbox_inches='tight')
            plt.close()

        # System stats plots
        if self.system_stats_history:
            system_df = pd.DataFrame(self.system_stats_history)

            # CPU and Memory usage
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

            if 'cpu_percent' in system_df.columns:
                ax1.plot(system_df['timestamp'], system_df['cpu_percent'], label='CPU %', color='blue')
                ax1.set_ylabel('CPU Usage (%)')
                ax1.set_title('System Resource Usage')
                ax1.legend()
                ax1.grid(True, alpha=0.3)

            if 'memory_percent' in system_df.columns:
                ax2.plot(system_df['timestamp'], system_df['memory_percent'], label='Memory %', color='green')
                ax2.set_xlabel('Time')
                ax2.set_ylabel('Memory Usage (%)')
                ax2.legend()
                ax2.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.savefig(plots_dir / 'system_resources.png', dpi=150, bbox_inches='tight')
            plt.close()

            # GPU stats if available
            gpu_cols = [col for col in system_df.columns if col.startswith('gpu_') and 'utilization' in col]
            if gpu_cols:
                plt.figure(figsize=(12, 6))
                for col in gpu_cols:
                    gpu_id = col.split('_')[1]
                    plt.plot(system_df['timestamp'], system_df[col],
                           label=f'GPU {gpu_id} Utilization', alpha=0.7)

                plt.xlabel('Time')
                plt.ylabel('GPU Utilization (%)')
                plt.title('GPU Utilization Over Time')
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.savefig(plots_dir / 'gpu_utilization.png', dpi=150, bbox_inches='tight')
                plt.close()

        self.logger.info(f"Training plots saved to {plots_dir}")

    def get_training_stats(self) -> Dict[str, Any]:
        """Get current training statistics"""
        if not self.metrics_history:
            return {'status': 'no_data'}

        latest_metrics = self.metrics_history[-1]
        elapsed = time.time() - self.training_start_time

        return {
            'status': 'active' if self.is_monitoring else 'stopped',
            'current_step': latest_metrics.get('step', 0),
            'current_loss': latest_metrics.get('loss', 0),
            'learning_rate': latest_metrics.get('learning_rate', 0),
            'elapsed_seconds': elapsed,
            'total_steps': len(self.metrics_history),
            'avg_loss': sum(m.get('loss', 0) for m in self.metrics_history) / len(self.metrics_history)
        }


def create_comprehensive_report(monitor: TrainingMonitor, output_path: str):
    """Create comprehensive training report"""
    stats = monitor.get_training_stats()

    # Generate plots
    monitor.create_training_plots()

    # Create report
    report = f"""
# Thor 1.1 Training Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Training Summary
- **Model**: {monitor.model_name}
- **Status**: {stats['status']}
- **Total Steps**: {stats.get('total_steps', 0)}
- **Current Loss**: {stats.get('current_loss', 0):.4f}
- **Average Loss**: {stats.get('avg_loss', 0):.4f}
- **Current Learning Rate**: {stats.get('learning_rate', 0):.6f}
- **Elapsed Time**: {str(timedelta(seconds=int(stats.get('elapsed_seconds', 0))))}

## System Information
- **GPU Available**: {monitor.gpu_available}
- **GPU Count**: {monitor.gpu_count}
- **Monitoring Active**: {monitor.is_monitoring}

## Files Generated
- Metrics History: `data/metrics/{monitor.model_name}_metrics_history.json`
- System Stats: `data/metrics/{monitor.model_name}_system_stats.json`
- Training Summary: `data/metrics/{monitor.model_name}_training_summary.json`
- Plots Directory: `data/metrics/plots/`
- TensorBoard Logs: `data/metrics/tensorboard/`

## Recommendations
"""

    if stats.get('current_loss', 0) > 1.0:
        report += "- Consider adjusting learning rate or checking data quality\n"
    if stats.get('elapsed_seconds', 0) > 3600:  # More than 1 hour
        report += "- Long training time detected - consider early stopping or learning rate scheduling\n"
    if not monitor.system_stats_history:
        report += "- System monitoring not available - install psutil and gputil for better insights\n"

    report += "\n## Next Steps\n"
    report += "- Review training curves in the plots directory\n"
    report += "- Check TensorBoard logs for detailed metrics\n"
    report += "- Consider model evaluation if training is complete\n"

    # Save report
    with open(output_path, 'w') as f:
        f.write(report)

    print(f"Comprehensive report saved to {output_path}")


# Global monitor instance
_monitor = None


def get_training_monitor(model_name: str = "thor-1.1") -> TrainingMonitor:
    """Get or create training monitor instance"""
    global _monitor

    if _monitor is None or _monitor.model_name != model_name:
        _monitor = TrainingMonitor(model_name)

    return _monitor


def start_training_monitor(model_name: str = "thor-1.1"):
    """Start training monitoring"""
    monitor = get_training_monitor(model_name)
    monitor.start_monitoring()
    return monitor


def stop_training_monitor():
    """Stop training monitoring"""
    global _monitor

    if _monitor:
        _monitor.stop_monitoring()
        # Generate final report
        report_path = _monitor.log_dir / f"{_monitor.model_name}_final_report.md"
        create_comprehensive_report(_monitor, str(report_path))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Thor 1.1 Training Monitor")
    parser.add_argument("--model_name", type=str, default="thor-1.1", help="Model name")
    parser.add_argument("--generate_report", action="store_true", help="Generate comprehensive report")
    parser.add_argument("--test_monitoring", action="store_true", help="Test monitoring functionality")

    args = parser.parse_args()

    monitor = TrainingMonitor(args.model_name)

    if args.test_monitoring:
        print("Testing monitoring functionality...")

        # Start monitoring
        monitor.start_monitoring()

        # Simulate training steps
        for step in range(10):
            loss = 2.0 * (0.95 ** step)  # Simulated decreasing loss
            lr = 1e-3 * (0.95 ** step)   # Simulated learning rate decay

            monitor.log_training_step(
                step=step,
                loss=loss,
                learning_rate=lr,
                grad_norm=1.0 / (step + 1)
            )

            time.sleep(2)  # Simulate training time

        # Stop monitoring
        monitor.stop_monitoring()

        print("Monitoring test completed")

    if args.generate_report:
        report_path = f"data/metrics/{args.model_name}_report.md"
        create_comprehensive_report(monitor, report_path)

    print("Training monitoring setup complete")
    print(f"Logs: data/metrics/{args.model_name}_training.log")
    print(f"TensorBoard: tensorboard --logdir data/metrics/tensorboard")