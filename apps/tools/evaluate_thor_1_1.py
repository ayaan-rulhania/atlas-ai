#!/usr/bin/env python3
"""
Thor 1.1 Evaluation and Benchmarking
Comprehensive evaluation suite for multi-task performance assessment
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
import numpy as np
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from transformers import GPT2TokenizerFast
from tqdm import tqdm
import logging
import argparse
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report,
    roc_auc_score, mean_squared_error
)
import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
import evaluate

# Try to import optional metrics
try:
    import bert_score
    BERTSCORE_AVAILABLE = True
except ImportError:
    BERTSCORE_AVAILABLE = False

try:
    perplexity_metric = evaluate.load("perplexity")
    PERPLEXITY_AVAILABLE = True
except ImportError:
    PERPLEXITY_AVAILABLE = False

# Add model paths
import sys
sys.path.append('models/thor-1.1')

from models.thor_1_1_model import AllRounderModel
from models.model_utils import ModelScaler, get_memory_usage


class EvaluationDataset(Dataset):
    """Dataset for model evaluation"""

    def __init__(self, data_path: str, tokenizer, task: str, max_length: int = 2048):
        self.data_path = Path(data_path)
        self.tokenizer = tokenizer
        self.task = task
        self.max_length = max_length
        self.data = []

        self.load_data()

    def load_data(self):
        """Load evaluation data"""
        with open(self.data_path, 'r', encoding='utf-8') as f:
            if self.data_path.suffix == '.jsonl':
                for line in f:
                    self.data.append(json.loads(line.strip()))
            else:
                self.data = json.load(f)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]

        if self.task == 'text_generation':
            text = item.get('input', item.get('text', ''))
            target = item.get('output', item.get('target', ''))

            return {
                'input_text': text,
                'target_text': target,
                'task': self.task
            }

        elif self.task in ['text_classification', 'sentiment_analysis']:
            text = item.get('text', item.get('input', ''))
            label = item.get('label', item.get('sentiment', 0))

            return {
                'input_text': text,
                'label': label,
                'task': self.task
            }

        elif self.task == 'question_answering':
            question = item.get('question', '')
            context = item.get('context', '')
            answer_start = item.get('answer_start', 0)
            answer_end = item.get('answer_end', 0)

            input_text = f"Question: {question} Context: {context}"

            return {
                'input_text': input_text,
                'answer_start': answer_start,
                'answer_end': answer_end,
                'task': self.task
            }

        return item


class ThorEvaluator:
    """Comprehensive evaluator for Thor 1.1"""

    def __init__(self, model_path: str, config_path: str, tokenizer_path: Optional[str] = None):
        self.model_path = Path(model_path)
        self.config_path = Path(config_path)
        self.tokenizer_path = Path(tokenizer_path) if tokenizer_path else None

        # Load configuration
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Setup logging
        self.setup_logging()

        # Load model and tokenizer
        self.model, self.tokenizer = self.load_model_and_tokenizer()

        # Initialize metrics
        self.metrics = self.initialize_metrics()

    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - ThorEvaluator - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def load_model_and_tokenizer(self):
        """Load model and tokenizer"""
        # Load tokenizer
        if self.tokenizer_path and self.tokenizer_path.exists():
            tokenizer = GPT2TokenizerFast.from_pretrained(str(self.tokenizer_path))
        else:
            tokenizer = GPT2TokenizerFast.from_pretrained('gpt2')
            tokenizer.pad_token = tokenizer.eos_token

        # Load model
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        checkpoint = torch.load(self.model_path, map_location=device)

        model = AllRounderModel(
            vocab_size=self.config['hyperparameters']['vocab_size'],
            hidden_size=self.config['hyperparameters']['hidden_size'],
            num_layers=self.config['hyperparameters']['num_hidden_layers'],
            num_heads=self.config['hyperparameters']['num_attention_heads'],
            intermediate_size=self.config['hyperparameters']['intermediate_size'],
            max_position_embeddings=self.config['hyperparameters']['max_position_embeddings']
        )

        if 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
        else:
            model.load_state_dict(checkpoint)

        model = model.to(device)
        model.eval()

        self.logger.info(f"Loaded model with {model.get_num_params():,} parameters")
        self.logger.info(f"Model loaded on device: {device}")

        return model, tokenizer

    def initialize_metrics(self) -> Dict[str, Any]:
        """Initialize evaluation metrics"""
        metrics = {}

        # Classification metrics
        metrics['classification'] = {
            'accuracy': accuracy_score,
            'precision': lambda y_true, y_pred: precision_score(y_true, y_pred, average='weighted'),
            'recall': lambda y_true, y_pred: recall_score(y_true, y_pred, average='weighted'),
            'f1': lambda y_true, y_pred: f1_score(y_true, y_pred, average='weighted')
        }

        # Text generation metrics
        metrics['text_generation'] = {}

        # Try to initialize ROUGE scorer
        try:
            metrics['text_generation']['rouge'] = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'])
        except:
            self.logger.warning("ROUGE scorer not available")

        # BLEU score
        try:
            nltk.download('punkt', quiet=True)
            metrics['text_generation']['bleu'] = lambda ref, pred: sentence_bleu(
                [ref.split()], pred.split(),
                smoothing_function=SmoothingFunction().method1
            )
        except:
            self.logger.warning("BLEU scorer not available")

        # BERTScore
        if BERTSCORE_AVAILABLE:
            try:
                metrics['text_generation']['bertscore'] = bert_score.BERTScorer(lang='en')
            except:
                self.logger.warning("BERTScore not available")

        # Perplexity
        if PERPLEXITY_AVAILABLE:
            metrics['text_generation']['perplexity'] = perplexity_metric

        # QA metrics
        metrics['question_answering'] = {
            'exact_match': self.exact_match_score,
            'f1': self.qa_f1_score
        }

        return metrics

    def evaluate_text_generation(self, dataset: EvaluationDataset, max_length: int = 100,
                               temperature: float = 1.0) -> Dict[str, float]:
        """Evaluate text generation performance"""
        self.logger.info("Evaluating text generation")
        results = {}

        predictions = []
        references = []

        for item in tqdm(dataset, desc="Generating text"):
            input_text = item['input_text']
            target_text = item['target_text']

            # Tokenize input
            inputs = self.tokenizer(
                input_text,
                return_tensors='pt',
                truncation=True,
                max_length=self.config['hyperparameters']['max_position_embeddings'] - max_length
            )

            # Move to device
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

            # Generate text
            with torch.no_grad():
                generated_ids = self.model.generate(
                    input_ids=inputs['input_ids'],
                    attention_mask=inputs.get('attention_mask'),
                    max_length=max_length,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )

            # Decode generated text
            generated_text = self.tokenizer.decode(
                generated_ids[0][len(inputs['input_ids'][0]):],
                skip_special_tokens=True
            ).strip()

            predictions.append(generated_text)
            references.append(target_text)

        # Calculate metrics
        if 'rouge' in self.metrics['text_generation']:
            rouge_scores = []
            for pred, ref in zip(predictions, references):
                scores = self.metrics['text_generation']['rouge'].score(ref, pred)
                rouge_scores.append({
                    'rouge1': scores['rouge1'].fmeasure,
                    'rouge2': scores['rouge2'].fmeasure,
                    'rougeL': scores['rougeL'].fmeasure
                })

            results['rouge1'] = np.mean([s['rouge1'] for s in rouge_scores])
            results['rouge2'] = np.mean([s['rouge2'] for s in rouge_scores])
            results['rougeL'] = np.mean([s['rougeL'] for s in rouge_scores])

        if 'bleu' in self.metrics['text_generation']:
            bleu_scores = [
                self.metrics['text_generation']['bleu'](ref, pred)
                for pred, ref in zip(predictions, references)
            ]
            results['bleu'] = np.mean(bleu_scores)

        if 'bertscore' in self.metrics['text_generation']:
            try:
                P, R, F1 = self.metrics['text_generation']['bertscore'].score(predictions, references)
                results['bertscore_f1'] = F1.mean().item()
            except:
                pass

        # Calculate perplexity if available
        if 'perplexity' in self.metrics['text_generation'] and PERPLEXITY_AVAILABLE:
            try:
                perplexity_results = self.metrics['text_generation']['perplexity'].compute(
                    predictions=predictions,
                    model_id='gpt2'  # Use GPT-2 as reference
                )
                results['perplexity'] = perplexity_results['mean_perplexity']
            except:
                pass

        self.logger.info(f"Text generation results: {results}")
        return results

    def evaluate_classification(self, dataset: EvaluationDataset) -> Dict[str, float]:
        """Evaluate classification performance"""
        self.logger.info("Evaluating classification")
        results = {}

        all_predictions = []
        all_labels = []

        for item in tqdm(dataset, desc="Classifying"):
            input_text = item['input_text']
            true_label = item['label']

            # Tokenize input
            inputs = self.tokenizer(
                input_text,
                return_tensors='pt',
                truncation=True,
                max_length=self.config['hyperparameters']['max_position_embeddings']
            )

            # Move to device
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

            # Get classification logits
            with torch.no_grad():
                outputs = self.model(
                    input_ids=inputs['input_ids'],
                    attention_mask=inputs.get('attention_mask'),
                    task='text_classification'
                )

            # Get prediction
            logits = outputs['logits']
            prediction = torch.argmax(logits, dim=-1).item()

            all_predictions.append(prediction)
            all_labels.append(true_label)

        # Calculate metrics
        for metric_name, metric_func in self.metrics['classification'].items():
            try:
                score = metric_func(all_labels, all_predictions)
                results[metric_name] = score
            except Exception as e:
                self.logger.warning(f"Failed to calculate {metric_name}: {e}")

        # Confusion matrix
        if len(set(all_labels)) <= 10:  # Only for small number of classes
            cm = confusion_matrix(all_labels, all_predictions)
            results['confusion_matrix'] = cm.tolist()

        self.logger.info(f"Classification results: {results}")
        return results

    def evaluate_question_answering(self, dataset: EvaluationDataset) -> Dict[str, float]:
        """Evaluate question answering performance"""
        self.logger.info("Evaluating question answering")
        results = {}

        exact_matches = []
        f1_scores = []

        for item in tqdm(dataset, desc="Answering questions"):
            input_text = item['input_text']
            true_start = item['answer_start']
            true_end = item['answer_end']

            # Tokenize input
            inputs = self.tokenizer(
                input_text,
                return_tensors='pt',
                truncation=True,
                max_length=self.config['hyperparameters']['max_position_embeddings']
            )

            # Move to device
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

            # Get QA predictions
            with torch.no_grad():
                outputs = self.model(
                    input_ids=inputs['input_ids'],
                    attention_mask=inputs.get('attention_mask'),
                    task='question_answering'
                )

            # Get predicted start and end positions
            start_logits = outputs['start_logits']
            end_logits = outputs['end_logits']

            start_pred = torch.argmax(start_logits, dim=-1).item()
            end_pred = torch.argmax(end_logits, dim=-1).item()

            # Calculate metrics
            em = self.exact_match_score((true_start, true_end), (start_pred, end_pred))
            f1 = self.qa_f1_score((true_start, true_end), (start_pred, end_pred))

            exact_matches.append(em)
            f1_scores.append(f1)

        results['exact_match'] = np.mean(exact_matches)
        results['f1'] = np.mean(f1_scores)

        self.logger.info(f"QA results: {results}")
        return results

    def exact_match_score(self, true_span: Tuple[int, int], pred_span: Tuple[int, int]) -> float:
        """Calculate exact match score for QA"""
        return 1.0 if true_span == pred_span else 0.0

    def qa_f1_score(self, true_span: Tuple[int, int], pred_span: Tuple[int, int]) -> float:
        """Calculate F1 score for QA spans"""
        true_start, true_end = true_span
        pred_start, pred_end = pred_span

        # Convert spans to sets of positions
        true_positions = set(range(true_start, true_end + 1))
        pred_positions = set(range(pred_start, pred_end + 1))

        # Calculate precision and recall
        if not pred_positions:
            return 0.0

        precision = len(true_positions & pred_positions) / len(pred_positions)
        recall = len(true_positions & pred_positions) / len(true_positions) if true_positions else 0.0

        # Calculate F1
        if precision + recall == 0:
            return 0.0

        return 2 * (precision * recall) / (precision + recall)

    def benchmark_inference_speed(self, batch_sizes: List[int] = [1, 4, 8, 16],
                                seq_lengths: List[int] = [128, 256, 512]) -> Dict[str, List[float]]:
        """Benchmark inference speed"""
        self.logger.info("Benchmarking inference speed")
        results = {}

        for batch_size in batch_sizes:
            batch_times = []
            for seq_len in seq_lengths:
                # Create dummy input
                input_ids = torch.randint(
                    0, self.config['hyperparameters']['vocab_size'],
                    (batch_size, seq_len)
                ).to(self.model.device)

                # Warmup
                with torch.no_grad():
                    for _ in range(3):
                        _ = self.model(input_ids, task='text_generation')

                # Benchmark
                torch.cuda.synchronize() if torch.cuda.is_available() else None
                start_time = torch.cuda.Event(enable_timing=True) if torch.cuda.is_available() else None
                if start_time:
                    start_time.record()

                start_cpu = torch.cuda.Event() if torch.cuda.is_available() else None
                if not torch.cuda.is_available():
                    import time
                    start_cpu = time.time()

                with torch.no_grad():
                    for _ in range(10):  # 10 runs
                        _ = self.model(input_ids, task='text_generation')

                if torch.cuda.is_available():
                    end_time = torch.cuda.Event(enable_timing=True)
                    end_time.record()
                    torch.cuda.synchronize()
                    elapsed = start_time.elapsed_time(end_time) / 10  # Average over 10 runs
                else:
                    elapsed = (time.time() - start_cpu) * 1000 / 10  # Convert to ms

                batch_times.append(elapsed)

            results[f'batch_{batch_size}'] = batch_times

        self.logger.info(f"Inference speed results: {results}")
        return results

    def evaluate_memory_usage(self) -> Dict[str, float]:
        """Evaluate memory usage"""
        self.logger.info("Evaluating memory usage")

        # Get memory usage from ModelScaler
        scaler = ModelScaler(self.config)
        memory_info = scaler.get_memory_usage(self.model, (1, 512))

        if torch.cuda.is_available():
            memory_info['gpu_memory_allocated'] = torch.cuda.memory_allocated() / (1024 * 1024)
            memory_info['gpu_memory_reserved'] = torch.cuda.memory_reserved() / (1024 * 1024)

        self.logger.info(f"Memory usage: {memory_info}")
        return memory_info

    def evaluate_long_context_reasoning(self, dataset: EvaluationDataset) -> Dict[str, float]:
        """Evaluate long-context reasoning capabilities (new for expanded model)"""
        self.logger.info("Evaluating long-context reasoning")

        all_predictions = []
        all_labels = []

        self.model.eval()
        with torch.no_grad():
            for batch in tqdm(dataset.get_dataloader(batch_size=1), desc="Long-context reasoning"):
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch.get('labels', None)

                # Generate response with extended context
                generated = self.model.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    max_length=input_ids.size(1) + 200,  # Allow for longer reasoning
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )

                # Decode predictions
                predictions = self.tokenizer.batch_decode(generated[:, input_ids.size(1):],
                                                        skip_special_tokens=True)

                if labels is not None:
                    labels = self.tokenizer.batch_decode(labels, skip_special_tokens=True)
                    all_labels.extend(labels)

                all_predictions.extend(predictions)

        # Calculate metrics for long-context reasoning
        if all_labels:
            # Use ROUGE and BLEU for reasoning quality
            scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
            rouge_scores = {'rouge1': [], 'rouge2': [], 'rougeL': []}

            smoothing = SmoothingFunction().method4
            bleu_scores = []

            for pred, label in zip(all_predictions, all_labels):
                # ROUGE scores
                scores = scorer.score(label, pred)
                for key in rouge_scores:
                    rouge_scores[key].append(scores[key].fmeasure)

                # BLEU score
                pred_tokens = pred.split()
                label_tokens = label.split()
                if pred_tokens and label_tokens:
                    bleu = sentence_bleu([label_tokens], pred_tokens, smoothing_function=smoothing)
                    bleu_scores.append(bleu)

            results = {
                'rouge1_f1': np.mean(rouge_scores['rouge1']),
                'rouge2_f1': np.mean(rouge_scores['rouge2']),
                'rougeL_f1': np.mean(rouge_scores['rougeL']),
                'bleu_score': np.mean(bleu_scores) if bleu_scores else 0.0,
                'reasoning_coherence': self._evaluate_reasoning_coherence(all_predictions),
                'context_utilization': self._evaluate_context_utilization(all_predictions, dataset)
            }
        else:
            # Fallback metrics for unlabeled evaluation
            results = {
                'avg_response_length': np.mean([len(pred.split()) for pred in all_predictions]),
                'vocabulary_diversity': self._calculate_vocabulary_diversity(all_predictions),
                'reasoning_coherence': self._evaluate_reasoning_coherence(all_predictions)
            }

        self.logger.info(f"Long-context reasoning results: {results}")
        return results

    def _evaluate_reasoning_coherence(self, predictions: List[str]) -> float:
        """Evaluate coherence of reasoning in predictions"""
        coherence_scores = []

        for pred in predictions:
            # Simple coherence heuristics
            sentences = pred.split('.')
            if len(sentences) < 2:
                coherence_scores.append(0.5)  # Neutral score for short responses
                continue

            # Check for logical connectors
            logical_connectors = ['because', 'therefore', 'however', 'although', 'since', 'thus']
            connector_count = sum(1 for connector in logical_connectors if connector in pred.lower())

            # Check for numbered steps or structured reasoning
            structured_indicators = ['first', 'second', 'then', 'finally', 'step', '1.', '2.', '3.']
            structured_count = sum(1 for indicator in structured_indicators if indicator in pred.lower())

            # Calculate coherence score
            coherence = min(1.0, (connector_count * 0.2 + structured_count * 0.3 + len(sentences) * 0.1))
            coherence_scores.append(coherence)

        return np.mean(coherence_scores) if coherence_scores else 0.0

    def _evaluate_context_utilization(self, predictions: List[str], dataset: EvaluationDataset) -> float:
        """Evaluate how well the model utilizes long context"""
        utilization_scores = []

        for pred in predictions:
            # This is a simplified metric - in practice, you'd need ground truth context utilization
            # For now, reward longer, more detailed responses that show context awareness
            words = len(pred.split())
            sentences = len(pred.split('.'))

            # Score based on response comprehensiveness
            utilization = min(1.0, (words / 100) * 0.4 + (sentences / 5) * 0.6)
            utilization_scores.append(utilization)

        return np.mean(utilization_scores) if utilization_scores else 0.0

    def _calculate_vocabulary_diversity(self, predictions: List[str]) -> float:
        """Calculate vocabulary diversity in predictions"""
        all_words = []
        for pred in predictions:
            all_words.extend(pred.lower().split())

        if not all_words:
            return 0.0

        unique_words = set(all_words)
        return len(unique_words) / len(all_words)

    def run_comprehensive_evaluation(self, eval_datasets: Dict[str, str],
                                   output_path: Optional[str] = None) -> Dict[str, Any]:
        """Run comprehensive evaluation across all tasks"""
        self.logger.info("Running comprehensive evaluation")

        results = {
            'timestamp': datetime.now().isoformat(),
            'model_info': {
                'parameters': self.model.get_num_params(),
                'config': self.config
            },
            'tasks': {}
        }

        # Evaluate each task
        for task_name, dataset_path in eval_datasets.items():
            if not Path(dataset_path).exists():
                self.logger.warning(f"Dataset not found: {dataset_path}")
                continue

            dataset = EvaluationDataset(dataset_path, self.tokenizer, task_name)

            if task_name == 'text_generation':
                task_results = self.evaluate_text_generation(dataset)
            elif task_name in ['text_classification', 'sentiment_analysis']:
                task_results = self.evaluate_classification(dataset)
            elif task_name == 'question_answering':
                task_results = self.evaluate_question_answering(dataset)
            elif task_name == 'long_context_reasoning':
                task_results = self.evaluate_long_context_reasoning(dataset)
            else:
                self.logger.warning(f"Unknown task: {task_name}")
                continue

            results['tasks'][task_name] = task_results

        # Benchmark performance
        results['benchmarks'] = {
            'inference_speed': self.benchmark_inference_speed(),
            'memory_usage': self.evaluate_memory_usage()
        }

        # Save results
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)

            self.logger.info(f"Results saved to {output_path}")

        return results

    def generate_report(self, results: Dict[str, Any], output_path: str):
        """Generate a detailed evaluation report"""
        self.logger.info("Generating evaluation report")

        report = f"""
# Thor 1.1 Evaluation Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Model Information
- Parameters: {results['model_info']['parameters']:,}
- Architecture: Thor 1.1 Transformer
- Tasks: {', '.join(results['tasks'].keys())}

## Task Performance

"""

        for task_name, task_results in results['tasks'].items():
            report += f"### {task_name.replace('_', ' ').title()}\n"
            for metric, value in task_results.items():
                if isinstance(value, float):
                    report += ".4f"
                else:
                    report += f"- {metric}: {value}\n"
            report += "\n"

        report += """
## Benchmarks

### Inference Speed (ms)
"""

        speed_results = results['benchmarks']['inference_speed']
        for batch_size, times in speed_results.items():
            report += f"- {batch_size}: {['.2f' for t in times]}\n"

        report += "\n### Memory Usage (MB)\n"
        memory_results = results['benchmarks']['memory_usage']
        for key, value in memory_results.items():
            if isinstance(value, float):
                report += ".2f"
            else:
                report += f"- {key}: {value}\n"

        # Save report
        with open(output_path, 'w') as f:
            f.write(report)

        self.logger.info(f"Report saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate Thor 1.1 Model")
    parser.add_argument("--model_path", type=str, required=True, help="Path to model checkpoint")
    parser.add_argument("--config_path", type=str, default="models/thor-1.1/config/config.yaml",
                       help="Path to config file")
    parser.add_argument("--tokenizer_path", type=str, default=None, help="Path to tokenizer")
    parser.add_argument("--output_dir", type=str, default="data/metrics",
                       help="Output directory for results")

    # Task-specific datasets
    parser.add_argument("--text_generation_data", type=str, default=None,
                       help="Path to text generation evaluation data")
    parser.add_argument("--classification_data", type=str, default=None,
                       help="Path to classification evaluation data")
    parser.add_argument("--qa_data", type=str, default=None,
                       help="Path to question answering evaluation data")

    parser.add_argument("--benchmark_only", action="store_true",
                       help="Run only benchmarks, no task evaluation")

    args = parser.parse_args()

    # Setup output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize evaluator
    evaluator = ThorEvaluator(args.model_path, args.config_path, args.tokenizer_path)

    if args.benchmark_only:
        # Run only benchmarks
        results = {
            'timestamp': datetime.now().isoformat(),
            'model_info': {
                'parameters': evaluator.model.get_num_params(),
                'config': evaluator.config
            },
            'benchmarks': {
                'inference_speed': evaluator.benchmark_inference_speed(),
                'memory_usage': evaluator.evaluate_memory_usage()
            }
        }
    else:
        # Run comprehensive evaluation
        eval_datasets = {}

        if args.text_generation_data:
            eval_datasets['text_generation'] = args.text_generation_data
        if args.classification_data:
            eval_datasets['text_classification'] = args.classification_data
        if args.qa_data:
            eval_datasets['question_answering'] = args.qa_data

        if not eval_datasets:
            # Use default datasets if available
            default_datasets = {
                'text_generation': 'data/training_data/val.json',
                'text_classification': 'data/training_data/val.json'
            }
            for task, path in default_datasets.items():
                if Path(path).exists():
                    eval_datasets[task] = path

        results = evaluator.run_comprehensive_evaluation(eval_datasets)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = output_dir / f"evaluation_results_{timestamp}.json"
    report_file = output_dir / f"evaluation_report_{timestamp}.md"

    # Generate report
    evaluator.generate_report(results, str(report_file))

    print(f"Evaluation completed!")
    print(f"Results saved to: {results_file}")
    print(f"Report saved to: {report_file}")


if __name__ == "__main__":
    main()