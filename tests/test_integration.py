import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add ChatBot directory to sys.path so we can import the FastAPI app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ChatBot')))

from api import app

# Create a TestClient instance for the FastAPI app
client = TestClient(app)

def test_chat_api_off_topic():
    """
    Test the /api/chat endpoint with an off-topic query.
    This should bypass the RAG pipeline and return a standard greeting/rejection quickly.
    """
    payload = {
        "message": "hello how are you?",
        "use_rag": True,
        "category": "general"
    }
    
    response = client.post("/api/chat", json=payload)
    
    # Check if the request was successful
    assert response.status_code == 200
    
    data = response.json()
    assert "response" in data
    assert "sources" in data
    
    # For off-topic greetings, it shouldn't use context
    # Sometimes it returns context_used=False
    assert data["context_used"] == False
    
def test_chat_api_missing_fields():
    """
    Test the API behavior when required fields are missing.
    The message field is required.
    """
    payload = {
        "use_rag": True
    }
    
    response = client.post("/api/chat", json=payload)
    
    # FastAPI automatically returns 422 Unprocessable Entity for missing required fields
    assert response.status_code == 422
