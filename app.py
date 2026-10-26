import subprocess
import sys
import os

# Use production settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blog.settings_prod")

# Run collectstatic first (in case it wasn't done at build time)
subprocess.run([sys.executable, "manage.py", "collectstatic", "--noinput"], check=False)

# Launch Django with gunicorn on port 7860 (HF Spaces default)
subprocess.run([
    "gunicorn",
    "blog.wsgi:application",
    "--bind", "0.0.0.0:7860",
    "--timeout", "300",
    "--workers", "1",
    "--threads", "4",
    "--log-level", "info",
], check=True)
