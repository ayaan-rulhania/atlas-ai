"""
Metrics computation for different tasks.
"""
import torch
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
from typing import Dict, List, Optional


def compute_metrics(
    predictions: np.ndarray,
    labels: np.ndarray,
    task: str,
    average: str = 'weighted'
) -> Dict[str, float]:
    """
    Compute metrics for different tasks.
    
    Args:
        predictions: Model predictions
        labels: Ground truth labels
        task: Task name
        average: Averaging strategy for multi-class metrics
    
    Returns:
        Dictionary of metrics
    """
    metrics = {}
    
    if task in ['text_classification', 'sentiment_analysis']:
        accuracy = accuracy_score(labels, predictions)
        f1 = f1_score(labels, predictions, average=average)
        precision, recall, _, _ = precision_recall_fscore_support(
            labels, predictions, average=average, zero_division=0
        )
        
        metrics = {
            'accuracy': float(accuracy),
            'f1': float(f1),
            'precision': float(precision),
            'recall': float(recall)
        }
    
    elif task == 'named_entity_recognition':
        # Flatten for token-level classification
        predictions_flat = predictions.flatten()
        labels_flat = labels.flatten()
        
        # Remove padding tokens (assuming 0 is padding)
        mask = labels_flat != -100  # -100 is typically used for ignored tokens
        if mask.sum() > 0:
            predictions_flat = predictions_flat[mask]
            labels_flat = labels_flat[mask]
            
            accuracy = accuracy_score(labels_flat, predictions_flat)
            f1 = f1_score(labels_flat, predictions_flat, average=average)
            
            metrics = {
                'accuracy': float(accuracy),
                'f1': float(f1)
            }
    
    elif task == 'question_answering':
        # For QA, we'd need to compute exact match and F1 on spans
        # This is a simplified version
        metrics = {
            'exact_match': 0.0,  # Placeholder
            'f1': 0.0  # Placeholder
        }
    
    elif task == 'text_generation':
        # For generation, we'd compute perplexity, BLEU, etc.
        metrics = {
            'perplexity': 0.0  # Placeholder
        }
    
    return metrics

