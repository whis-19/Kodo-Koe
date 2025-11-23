# Code to Audio System

A unified system that converts code into spoken audio summaries using FastAPI with built-in web interface. **Works without any API keys!**

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Web Interface  │────▶│  FastAPI App    │────▶│  Local TTS    │
│  (Built-in)     │◀────┤  (Single Server)│◀────│  & Analysis  │
└─────────────────┘     └─────────────────┘     └──────────────┘
```

## Features

- **🔓 No API Keys Required**: Works completely offline with local synthesis
- **🎯 Zero Dependencies**: Only basic Python packages needed
- **🚀 Single File Deployment**: One unified application
- **🌐 Modern Web Interface**: Clean, responsive UI
- **⚡ Instant Setup**: Install and run in seconds

## Quick Start

1. **Install dependencies** (minimal set):
   ```bash
   pip install fastapi uvicorn python-dotenv requests pydantic
   ```

2. **Run the application**:
   ```bash
   python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Open browser**: http://localhost:8000

That's it! No API keys, no complex setup, no external services needed.

## Project Structure

```
├── app.py                    # Main FastAPI application with web interface
├── backend/
│   ├── models.py             # Pydantic models
│   └── services/
│       ├── __init__.py       # Package initialization
│       ├── tts.py            # Local TTS service
│       └── code_processor.py # Rule-based code analysis
├── backend/tests/
│   └── test_app.py           # Unit tests
├── requirements.txt           # Minimal dependencies (with optional ones)
├── .env.example              # Optional: For Hugging Face API (better quality)
├── start.sh                   # Linux/Mac startup script
├── start.bat                  # Windows startup script
├── test_setup.py              # Setup verification script
└── README.md                  # This file
```

## How It Works (Open Source Models)

### Code Documentation
- **FLAN-T5**: Google's instruction-tuned T5 model for better code understanding
- **T5**: Original T5 model for text-to-text generation
- **Rule-based fallback**: Extracts functions, classes, imports using regex

### Text-to-Speech
- **XTTS (Coqui)**: High-quality multilingual TTS, runs locally
- **pyttsx3**: System TTS using built-in operating system voices
- **Basic Synthesis**: NumPy/SciPy based speech-like audio generation
- **Simple Tones**: Ultimate fallback using sine wave synthesis

## Installation Options

### Option 1: Basic Installation (Fast Setup)
```bash
pip install fastapi uvicorn python-dotenv requests pydantic
```
- Uses rule-based documentation
- Uses simple tone generation for TTS
- Setup time: 30 seconds

### Option 2: Recommended (Open Source Models)
```bash
pip install fastapi uvicorn python-dotenv requests pydantic transformers torch numpy scipy
```
- Uses FLAN-T5/T5 for documentation
- Uses NumPy/SciPy for better TTS
- Setup time: 2-3 minutes

### Option 3: Full Installation (Best Quality)
```bash
pip install fastapi uvicorn python-dotenv requests pydantic transformers torch numpy scipy TTS pyttsx3
```
- Uses all open-source models
- XTTS for high-quality TTS
- System TTS as fallback
- Setup time: 5-10 minutes

### Option 4: With Hugging Face (Optional)
```bash
# Add your HF token to .env for cloud-based models
echo "HUGGINGFACE_API_TOKEN=your_token" >> .env
```
- Access to high-quality cloud TTS models
- Fallback to local models if API fails

## API Endpoints

- `GET /`: Web interface for code to audio conversion
- `POST /synthesize`: Convert code to audio (API endpoint)
  - Request body: `{"code": "your code here", "model_id": "tts-model-id"}`
  - Response: Streaming audio with documentation and summary headers
- `GET /health`: Health check endpoint
  - Response: `{"status": "healthy"}`

## Testing

Run the tests:
```bash
pytest -v
```

Verify setup:
```bash
python test_setup.py
```

## Environment Variables (Optional)

- `HUGGINGFACE_API_TOKEN`: Your Hugging Face API token (optional, for better quality)

## Supported TTS Models

### Local Open Source Models (No API Required)
- **XTTS (Coqui)**: High-quality multilingual TTS
- **pyttsx3**: System TTS using OS built-in voices
- **Basic Synthesis**: NumPy/SciPy based audio generation
- **Simple Tones**: Ultimate sine wave fallback

### Cloud Models (API Required)
- **facebook/fastspeech2-en-ljspeech**: FastSpeech2 (LJSpeech)
- **espnet/kan-bayashi_ljspeech_fastspeech2**: ESPNet FastSpeech2
- **microsoft/speecht5_tts**: SpeechT5

## Supported Documentation Models

### Local Open Source Models
- **FLAN-T5 Small**: Google's instruction-tuned model (fast)
- **FLAN-T5 Base**: Larger instruction-tuned model (better quality)
- **T5 Small**: Original T5 model (fallback)

### Cloud Models (API Required)
- **Hugging Face T5**: Via API if token provided

## Supported Modes

### Local Mode (Default)
- **Documentation**: Rule-based code analysis
- **TTS**: Local wave synthesis
- **Requirements**: Basic Python packages only

### Enhanced Mode (Optional)
- **Documentation**: T5 model via Hugging Face
- **TTS**: High-quality TTS models via Hugging Face
- **Requirements**: API token + optional packages

## Features Comparison

| Feature | Local Mode | Enhanced Mode |
|---------|------------|---------------|
| **Setup Time** | 30 seconds | 2-5 minutes |
| **Dependencies** | 5 packages | 8+ packages |
| **API Keys** | Not required | Optional |
| **Audio Quality** | Basic synthesis | Professional TTS |
| **Documentation** | Rule-based | AI-generated |
| **Offline Use** | ✅ Yes | ❌ Requires internet |

## Troubleshooting

1. **Application not starting**: Check if port 8000 is available
2. **Audio not playing**: Check browser console for errors
3. **No sound with local TTS**: Try different browsers or download the audio file
4. **Want better quality**: Install optional packages and add Hugging Face token

## License

MIT