"""
Transformer-based ML predictor for fake news detection.
Supports any HuggingFace classification model (RoBERTa, BERT, etc.).

Uses a DUAL-MODEL approach:
  - Article model (RoBERTa): For longer text (>= SHORT_TEXT_THRESHOLD words)
  - Headline model (BERT): For short text (< SHORT_TEXT_THRESHOLD words)

This solves the problem of article-trained models producing unreliable
scores on short headlines, which lack the context they were trained on.
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from django.conf import settings


class TransformerPredictor:
    """Manages HuggingFace Transformer models for fake news prediction.
    
    Dual-model architecture:
    - Article model: Optimized for full news articles (long text)
    - Headline model: Optimized for headlines and short text
    
    The appropriate model is auto-selected based on input word count.
    """
    
    def __init__(self):
        self._device = None
        
        # Article model (for long text >= threshold)
        self._article_model = None
        self._article_tokenizer = None
        self._article_real_label_index = None
        
        # Headline model (for short text < threshold)
        self._headline_model = None
        self._headline_tokenizer = None
        self._headline_real_label_index = None
        
        self._short_text_threshold = getattr(settings, 'SHORT_TEXT_THRESHOLD', 150)
        
        self._setup_device()
        self._load_models()
    
    def _setup_device(self):
        """Determine the compute device (GPU/CPU)."""
        if settings.USE_GPU and torch.cuda.is_available():
            self._device = torch.device('cuda')
            print(f"[OK] Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            self._device = torch.device('cpu')
            print("[OK] Using CPU")
    
    def _load_models(self):
        """Load both article and headline models."""
        # Load article model
        article_model_name = settings.MODEL_NAME
        print(f"\n{'='*60}")
        print(f"[INFO] Loading ARTICLE model: {article_model_name}")
        print(f"{'='*60}")
        self._article_model, self._article_tokenizer, self._article_real_label_index = \
            self._load_single_model(article_model_name)
        
        # Load headline model (if configured and different from article model)
        headline_model_name = getattr(settings, 'HEADLINE_MODEL_NAME', '')
        if headline_model_name and headline_model_name != article_model_name:
            print(f"\n{'='*60}")
            print(f"[INFO] Loading HEADLINE model: {headline_model_name}")
            print(f"{'='*60}")
            self._headline_model, self._headline_tokenizer, self._headline_real_label_index = \
                self._load_single_model(headline_model_name)
            print(f"\n[OK] Dual-model setup complete!")
            print(f"     Article model:  {article_model_name}")
            print(f"     Headline model: {headline_model_name}")
            print(f"     Threshold:      {self._short_text_threshold} words")
        else:
            # Fallback: use same model for both
            self._headline_model = self._article_model
            self._headline_tokenizer = self._article_tokenizer
            self._headline_real_label_index = self._article_real_label_index
            print("[INFO] No separate headline model configured. Using single model for all text.")
    
    def _load_single_model(self, model_name):
        """Load a single pre-trained model from HuggingFace.
        
        Args:
            model_name: HuggingFace model identifier
            
        Returns:
            Tuple of (model, tokenizer, real_label_index)
        """
        print(f"[INFO] Downloading/loading: {model_name}")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=settings.MODEL_CACHE_DIR
        )
        
        # Load model
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            cache_dir=settings.MODEL_CACHE_DIR
        )
        
        # Auto-detect label mapping
        real_label_index = self._detect_label_mapping(model, model_name)
        
        # Move to device
        model = model.to(self._device)
        
        # Use FP16 for faster inference on GPU
        if settings.USE_FP16 and self._device.type == 'cuda':
            model = model.half()
            print(f"[OK] Using FP16 mixed precision for {model_name}")
        
        # Set model to evaluation mode
        model.eval()
        print(f"[OK] Model '{model_name}' loaded successfully")
        
        return model, tokenizer, real_label_index
    
    def _detect_label_mapping(self, model, model_name=''):
        """
        Auto-detect which label index corresponds to REAL/TRUE news.
        Different models use different label orderings.
        
        Args:
            model: The loaded HuggingFace model
            model_name: Model name for logging
            
        Returns:
            int: The index of the REAL/TRUE label
        """
        # Check for model-specific override in settings
        # Format: {'model_name': real_label_index}
        label_overrides = getattr(settings, 'MODEL_LABEL_OVERRIDES', {})
        if model_name in label_overrides:
            real_label_index = label_overrides[model_name]
            print(f"[OK] Using settings override for {model_name}: REAL label at index {real_label_index}")
            return real_label_index
        
        id2label = getattr(model.config, 'id2label', None)
        
        if id2label:
            print(f"[INFO] Model ({model_name}) id2label: {id2label}")
            # Search for the REAL/TRUE label index
            for idx, label in id2label.items():
                label_upper = str(label).upper()
                if label_upper in ['REAL', 'TRUE', 'RELIABLE', 'NOT FAKE']:
                    real_label_index = int(idx)
                    print(f"[OK] REAL/TRUE label detected at index {real_label_index}")
                    return real_label_index
            
            # If no obvious REAL label found, check for FAKE at index 0
            for idx, label in id2label.items():
                label_upper = str(label).upper()
                if label_upper in ['FAKE', 'FALSE', 'UNRELIABLE']:
                    # FAKE is at this index, so REAL is the other one
                    real_label_index = 1 - int(idx) if model.config.num_labels == 2 else 1
                    print(f"[OK] FAKE label at index {idx}, REAL label at index {real_label_index}")
                    return real_label_index
        
        # Default: assume label 1 = REAL (most common convention)
        real_label_index = 1
        print(f"[WARNING] Could not auto-detect label mapping for {model_name}. Defaulting to index {real_label_index} for REAL.")
        return real_label_index
    
    def is_ready(self):
        """Check if both models and tokenizers are loaded."""
        return (self._article_model is not None and 
                self._article_tokenizer is not None and
                self._headline_model is not None and
                self._headline_tokenizer is not None)
    
    def predict(self, text: str) -> dict:
        """
        Predict whether the given text is fake or true news.
        Automatically selects the appropriate model based on word count.
        
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
            # Select model based on word count
            word_count = len(text.split())
            is_short_text = word_count < self._short_text_threshold
            
            if is_short_text:
                model = self._headline_model
                tokenizer = self._headline_tokenizer
                real_label_index = self._headline_real_label_index
                model_type = 'Headline-BERT'
                print(f"[PREDICT] Using HEADLINE model ({word_count} words < {self._short_text_threshold} threshold)")
            else:
                model = self._article_model
                tokenizer = self._article_tokenizer
                real_label_index = self._article_real_label_index
                model_type = 'Transformer'
                print(f"[PREDICT] Using ARTICLE model ({word_count} words >= {self._short_text_threshold} threshold)")
            
            # Tokenize input text
            inputs = tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=settings.MODEL_MAX_LENGTH,
                padding='max_length'
            )
            
            # Move inputs to the same device as model
            inputs = {k: v.to(self._device) for k, v in inputs.items()}
            
            # Get prediction (no gradient computation needed for inference)
            with torch.no_grad():
                outputs = model(**inputs)
                
            # Get probabilities using softmax
            logits = outputs.logits.float()  # Ensure float32 for softmax
            probs = torch.nn.functional.softmax(logits, dim=-1)
            
            # Use auto-detected label index for REAL/TRUE
            probability = float(probs[0][real_label_index].cpu())
            
            # Log for debugging
            all_probs = {str(i): round(float(probs[0][i].cpu()), 4) for i in range(probs.shape[1])}
            print(f"[DEBUG] All probabilities: {all_probs}, REAL index: {real_label_index}, REAL prob: {probability:.4f}")
            
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
                'word_count': word_count,
                'model_type': model_type
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
_predictor = None

def get_predictor_instance() -> TransformerPredictor:
    """Get or create the global Transformer predictor instance."""
    global _predictor
    if _predictor is None or not _predictor.is_ready():
        _predictor = TransformerPredictor()
    return _predictor
