"""
ML Model utilities for fake news prediction.
Uses a HuggingFace Transformer model (RoBERTa/BERT) for classification.
"""

from .ml_predictor import get_predictor_instance


def get_predictor():
    """
    Get the ML predictor instance.

    Returns:
        TransformerPredictor instance (lazy-loaded singleton).
    """
    return get_predictor_instance()
