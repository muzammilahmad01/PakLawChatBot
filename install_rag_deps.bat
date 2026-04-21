@echo off
REM Quick setup script for RAG dependencies in conda environment

echo ============================================================
echo Installing RAG Dependencies for PakLawChatBot
echo ============================================================
echo.

echo Activating conda environment: paklawchatbot
call conda activate paklawchatbot

echo.
echo Installing dependencies via pip...
pip install pypdf2 chromadb langchain-chroma langchain-community --quiet

echo.
echo ============================================================
echo Installation complete!
echo ============================================================
echo.
echo Next steps:
echo 1. Run: python ChatBot/ingest_documents.py test
echo 2. Then run: streamlit run ChatBot/app.py
echo.
pause
