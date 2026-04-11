"""
DistilBERT-based ML Model utilities for fake news prediction.
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from django.conf import settings


class DistilBERTPredictor:
    """Manages the DistilBERT model for fake news prediction."""
    
    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._device = None
        self._real_label_index = None  # Dynamically detected
        self._load_model()
    
    def _load_model(self):
        """Load the pre-trained DistilBERT model from HuggingFace."""
        print(f"[INFO] Loading DistilBERT model: {settings.DISTILBERT_MODEL_NAME}")
        
        # Determine device
        if settings.USE_GPU and torch.cuda.is_available():
            self._device = torch.device('cuda')
            print(f"[OK] Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            self._device = torch.device('cpu')
            print("[OK] Using CPU")
        
        # Load tokenizer
        self._tokenizer = AutoTokenizer.from_pretrained(
            settings.DISTILBERT_MODEL_NAME,
            cache_dir=settings.DISTILBERT_CACHE_DIR
        )
        
        # Load model
        self._model = AutoModelForSequenceClassification.from_pretrained(
            settings.DISTILBERT_MODEL_NAME,
            cache_dir=settings.DISTILBERT_CACHE_DIR
        )
        
        # Auto-detect label mapping from model config
        self._detect_label_mapping()
        
        # Move to device
        self._model = self._model.to(self._device)
        
        # Use FP16 for faster inference on RTX 3050Ti
        if settings.USE_FP16 and self._device.type == 'cuda':
            self._model = self._model.half()
            print("[OK] Using FP16 mixed precision")
        
        # Set model to evaluation mode
        self._model.eval()
        print("[OK] DistilBERT model and tokenizer loaded successfully")
    
    def _detect_label_mapping(self):
        """
        Auto-detect which label index corresponds to REAL/TRUE news.
        Different models use different label orderings.
        """
        id2label = getattr(self._model.config, 'id2label', None)
        
        if id2label:
            print(f"[INFO] Model id2label mapping: {id2label}")
            # Search for the REAL/TRUE label index
            for idx, label in id2label.items():
                label_upper = str(label).upper()
                if label_upper in ['REAL', 'TRUE', 'RELIABLE', 'NOT FAKE', 'LABEL_1']:
                    self._real_label_index = int(idx)
                    print(f"[OK] REAL/TRUE label detected at index {self._real_label_index}")
                    return
            
            # If no obvious REAL label found, check for FAKE at index 0
            for idx, label in id2label.items():
                label_upper = str(label).upper()
                if label_upper in ['FAKE', 'FALSE', 'UNRELIABLE', 'LABEL_0']:
                    # FAKE is at this index, so REAL is the other one
                    self._real_label_index = 1 - int(idx) if self._model.config.num_labels == 2 else 1
                    print(f"[OK] FAKE label at index {idx}, REAL label at index {self._real_label_index}")
                    return
        
        # Default: assume label 1 = REAL (most common convention)
        self._real_label_index = 1
        print(f"[WARNING] Could not auto-detect label mapping. Defaulting to index {self._real_label_index} for REAL.")
    
    def is_ready(self):
        """Check if model and tokenizer are loaded."""
        return self._model is not None and self._tokenizer is not None
    
    def predict(self, text: str) -> dict:
        """
        Predict whether the given text is fake or true news.
        
        Args:
            text: The news article text to analyze
            
        Returns:
            Dictionary with prediction results including probability
        """
        if not text or not text.strip():
            return {'error': 'No text provided'}
        
        if not self.is_ready():
            return {'error': 'Model not loaded. Please restart the server.'}
        
        try:
            # Tokenize input text
            inputs = self._tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=settings.DISTILBERT_MAX_LENGTH,
                padding='max_length'
            )
            
            # Move inputs to the same device as model
            inputs = {k: v.to(self._device) for k, v in inputs.items()}
            
            # Get prediction (no gradient computation needed for inference)
            with torch.no_grad():
                outputs = self._model(**inputs)
                
            # Get probabilities using softmax
            logits = outputs.logits.float()  # Ensure float32 for softmax
            probs = torch.nn.functional.softmax(logits, dim=-1)
            
            # Use auto-detected label index for REAL/TRUE
            probability = float(probs[0][self._real_label_index].cpu())
            
            # Log for debugging
            all_probs = {str(i): round(float(probs[0][i].cpu()), 4) for i in range(probs.shape[1])}
            print(f"[DEBUG] All probabilities: {all_probs}, REAL index: {self._real_label_index}, REAL prob: {probability:.4f}")
            
            # Determine prediction and confidence
            prediction = "True" if probability > 0.5 else "Fake"
            confidence_level, confidence_label = self._get_confidence(probability)
            
            # Calculate trueness probability (0-100 scale)
            trueness_probability = round(probability * 100, 2)
            
            return {
                'prediction': prediction,
                'probability': round(probability, 4),
                'trueness_probability': trueness_probability,
                'confidence_level': confidence_level,
                'confidence_label': confidence_label,
                'text_length': len(text),
                'model_type': 'DistilBERT'
            }
            
        except Exception as e:
            print(f"[ERROR] Prediction failed: {e}")
            import traceback
            traceback.print_exc()
            return {'error': f'Prediction failed: {str(e)}'}
    
    def _get_confidence(self, probability: float) -> tuple:
        """
        Determine confidence level based on probability.
        
        Returns:
            Tuple of (confidence_level, confidence_label)
        """
        if probability < 0.3:
            return ('High', 'High confidence FAKE')
        elif probability < 0.45:
            return ('Moderate', 'Likely FAKE')
        elif probability < 0.55:
            return ('Low', 'Uncertain - Cannot determine')
        elif probability < 0.7:
            return ('Moderate', 'Likely TRUE')
        else:
            return ('High', 'High confidence TRUE')


# Global predictor instance - lazy loaded
_distilbert_predictor = None

def get_distilbert_predictor() -> DistilBERTPredictor:
    """Get or create the global DistilBERT predictor instance."""
    global _distilbert_predictor
    if _distilbert_predictor is None or not _distilbert_predictor.is_ready():
        _distilbert_predictor = DistilBERTPredictor()
    return _distilbert_predictor


