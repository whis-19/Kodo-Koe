from pydantic import BaseModel
from typing import Optional, Dict, Any

class CodeRequest(BaseModel):
    """Request model for code synthesis endpoint."""
    code: str
    model_id: str = "facebook/fastspeech2-en-ljspeech"
    voice: Optional[str] = None

class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str

class ErrorResponse(BaseModel):
    """Standard error response model."""
    detail: str

class SynthesisResponse:
    """Response class for synthesis endpoint (streaming)."""
    # This is a marker class for API documentation
    # The actual response is a StreamingResponse with audio/wav content
    # and custom headers for documentation and summary
    pass