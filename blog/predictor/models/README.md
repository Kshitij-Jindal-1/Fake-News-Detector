# Model Cache Directory

This directory stores downloaded HuggingFace models for offline use.

## Contents

- Pre-trained DistilBERT/RoBERTa models from HuggingFace
- Model tokenizers and configuration files

## Size

First download: ~500MB
Subsequent runs: Load from cache (faster startup)

## Cleanup

To free up disk space, you can safely delete this directory.
Models will be re-downloaded on next run.
