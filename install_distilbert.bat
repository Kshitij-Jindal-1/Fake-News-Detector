@echo off
echo ========================================
echo DistilBERT Installation Script
echo ========================================
echo.
echo This script will install the required dependencies for DistilBERT fake news detection.
echo Packages to install: transformers, torch, sentencepiece
echo.
echo Estimated download size: ~2GB
echo This may take 5-10 minutes depending on your internet connection.
echo.
pause

echo.
echo Installing packages...
pip install transformers torch sentencepiece

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Run the Django server: python manage.py runserver
echo 2. Test the API endpoint: http://localhost:8000/api/health/
echo.
pause
