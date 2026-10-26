"""
Production settings for HuggingFace Spaces deployment.
Extends the base settings.py with production-safe overrides.
"""

from blog.settings import *  # noqa: F401, F403

import os

# Security
SECRET_KEY = os.environ.get("SECRET_KEY", SECRET_KEY)  # noqa: F405
DEBUG = False

# Allow HuggingFace Spaces and local hosts
ALLOWED_HOSTS = [
    ".hf.space",
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
]

# CORS - allow your Vercel frontend
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS",
    "https://truthcheckerapp.vercel.app"
).split(",")

# Also allow HF space previews and localhost dev
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.hf\.space$",
    r"^http://localhost:\d+$",
    r"^http://127\.0\.0\.1:\d+$",
]

# WhiteNoise for serving static files
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # noqa: F405

# Model cache - use /tmp on HF Spaces (writable)
MODEL_CACHE_DIR = os.environ.get("MODEL_CACHE_DIR", "/tmp/model_cache")

# Disable GPU on HF Spaces (free tier is CPU-only)
USE_GPU = False
USE_FP16 = False
