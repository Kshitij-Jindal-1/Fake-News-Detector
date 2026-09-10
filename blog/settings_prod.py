"""
Production settings for HuggingFace Spaces deployment.
Extends the base settings.py with production-safe overrides.
"""

from blog.settings import *  # noqa: F401, F403

import os

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', SECRET_KEY)  # noqa: F405
DEBUG = False

# HuggingFace Spaces provides the app at a URL like:
# https://username-spacename.hf.space
ALLOWED_HOSTS = [
    '.hf.space',          # HuggingFace Spaces wildcard
    'localhost',
    '127.0.0.1',
]

# CORS — allow your Vercel frontend
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'https://your-app.vercel.app'
).split(',')

# Also allow all HF space previews (optional but handy)
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.hf\.space$",
]

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # noqa: F405

# Model cache — use /tmp in HF Spaces (writable, but ephemeral)
MODEL_CACHE_DIR = os.environ.get(
    'MODEL_CACHE_DIR',
    '/tmp/hf_model_cache'
)

# Disable GPU on HF Spaces CPU tier
USE_GPU = False
USE_FP16 = False
