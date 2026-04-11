"""
ML Model utilities for fake news prediction.
Uses DistilBERT (RoBERTa) model via HuggingFace Transformers.
"""

from .utils_distilbert import get_distilbert_predictor


def get_predictor():
    """
    Get the DistilBERT predictor instance.

    Returns:
        DistilBERTPredictor instance (lazy-loaded singleton).
    """
    return get_distilbert_predictor()
