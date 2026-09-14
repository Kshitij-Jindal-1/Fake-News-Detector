"""
Production settings for Railway / HuggingFace Spaces deployment.
Extends the base settings.py with production-safe overrides.
"""

from blog.settings import *  # noqa: F401, F403

import os

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', SECRET_KEY)  # noqa: F405
DEBUG = False

# Allow Railway, HuggingFace, and local hosts
ALLOWED_HOSTS = [
    '.railway.app',       # Railway wildcard
    '.hf.space',          # HuggingFace Spaces wildcard
    'localhost',
    '127.0.0.1',
]

# CORS — allow your Vercel frontend
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'https://truthcheckerapp.vercel.app'
).split(',')

# Also allow Railway and HF space previews
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.hf\.space$",
    r"^https://.*\.railway\.app$",
]

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # noqa: F405

# Model cache — use /tmp (writable, but ephemeral)
MODEL_CACHE_DIR = os.environ.get(
    'MODEL_CACHE_DIR',
    '/tmp/hf_model_cache'
)

# Disable GPU on cloud deployments (CPU tier)
USE_GPU = False
USE_FP16 = False

# === Lightweight model for memory-constrained Railway (1GB RAM) ===
# Full-size BERT/RoBERTa (~440MB) + PyTorch (~400MB) exceeds 1GB.
# bert-tiny is only ~17MB — fits comfortably with plenty of headroom.
# Source verification (60% weight) compensates for the lighter ML model.
MODEL_NAME = 'mrm8488/bert-tiny-finetuned-fake-news-detection'
HEADLINE_MODEL_NAME = ''  # Single-model mode

# bert-tiny uses LABEL_0 = REAL (auto-detection defaults to index 1, which inverts scores)
MODEL_LABEL_OVERRIDES = {
    'mrm8488/bert-tiny-finetuned-fake-news-detection': 0,
}
