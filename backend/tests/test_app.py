import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app import app
from models import CodeRequest

client = TestClient(app)

@patch('services.tts.requests.post')
@patch('services.code_processor.requests.post')
def test_synthesize_endpoint(mock_hf_api, mock_tts):
    # Mock Hugging Face T5 response for documentation
    mock_hf_response = MagicMock()
    mock_hf_response.status_code = 200
    mock_hf_response.json.return_value = [
        {"generated_text": "This function prints hello world to the console.\nIt's a simple demonstration function."}
    ]
    mock_hf_api.return_value = mock_hf_response
    
    # Mock TTS response
    mock_tts.return_value.__enter__.return_value = MagicMock(
        status_code=200,
        iter_content=lambda chunk_size: [b"fake_audio_data"]
    )
    
    response = client.post(
        "/synthesize",
        json={
            "code": "def test(): pass",
            "model_id": "test-model"
        }
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert "This function prints hello world" in response.headers["Documentation"]
    assert "This function prints hello world" in response.headers["Summary"]

def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_code_request_model():
    """Test CodeRequest model validation."""
    # Valid request
    request = CodeRequest(code="print('hello')")
    assert request.code == "print('hello')"
    assert request.model_id == "facebook/fastspeech2-en-ljspeech"
    assert request.voice is None
    
    # Custom model_id
    request = CodeRequest(
        code="print('hello')", 
        model_id="custom/model",
        voice="male"
    )
    assert request.model_id == "custom/model"
    assert request.voice == "male"