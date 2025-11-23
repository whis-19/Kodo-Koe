from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import os
from services import tts, code_processor
from models import CodeRequest, HealthResponse

app = FastAPI(title="Code to Audio System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
@app.post("/synthesize")
async def synthesize_audio(request: CodeRequest):
    """Generate and stream audio for code documentation."""
    try:
        # Generate documentation and summary
        doc_result = code_processor.generate_documentation(request.code)
        
        # Stream TTS audio
        audio_stream = tts.stream_tts_audio(
            text=doc_result["summary"],
            model_id=request.model_id
        )
        
        return StreamingResponse(
            audio_stream,
            media_type="audio/wav",
            headers={
                "Documentation": doc_result["documentation"],
                "Summary": doc_result["summary"]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy")

# Web Interface
@app.get("/", response_class=HTMLResponse)
async def web_interface():
    """Serve the web interface."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Code to Audio System</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            
            .header p {
                font-size: 1.2em;
                opacity: 0.9;
            }
            
            .main-content {
                padding: 40px;
            }
            
            .input-section {
                margin-bottom: 30px;
            }
            
            .settings {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .setting-group {
                display: flex;
                flex-direction: column;
            }
            
            label {
                font-weight: 600;
                margin-bottom: 8px;
                color: #333;
            }
            
            select, textarea {
                padding: 12px;
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            
            select:focus, textarea:focus {
                outline: none;
                border-color: #667eea;
            }
            
            textarea {
                width: 100%;
                min-height: 200px;
                font-family: 'Monaco', 'Courier New', monospace;
                resize: vertical;
            }
            
            .button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 18px;
                font-weight: 600;
                border-radius: 8px;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            
            .button:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }
            
            .button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .results {
                margin-top: 30px;
            }
            
            .result-section {
                background: #f8f9fa;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
            }
            
            .result-section h3 {
                color: #333;
                margin-bottom: 15px;
            }
            
            .documentation {
                background: white;
                border: 1px solid #e1e5e9;
                border-radius: 4px;
                padding: 15px;
                font-family: 'Monaco', 'Courier New', monospace;
                white-space: pre-wrap;
                max-height: 300px;
                overflow-y: auto;
            }
            
            .audio-player {
                width: 100%;
                margin-top: 10px;
            }
            
            .loading {
                display: flex;
                align-items: center;
                gap: 10px;
                color: #667eea;
            }
            
            .spinner {
                width: 20px;
                height: 20px;
                border: 2px solid #f3f3f3;
                border-top: 2px solid #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .error {
                background: #fee;
                color: #c33;
                padding: 15px;
                border-radius: 8px;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔊 Code to Audio System</h1>
                <p>Convert your code into spoken audio summaries</p>
            </div>
            
            <div class="main-content">
                <div class="input-section">
                    <div class="settings">
                        <div class="setting-group">
                            <label for="model">TTS Model:</label>
                            <select id="model">
                                <option value="xtts">XTTS (Coqui) - High Quality Local</option>
                                <option value="pyttsx3">System TTS - Built-in Voice</option>
                                <option value="basic">Basic Synthesis - NumPy/SciPy</option>
                                <option value="simple">Simple Tones - Fallback</option>
                                <option value="facebook/fastspeech2-en-ljspeech">FastSpeech2 (HF API)</option>
                                <option value="espnet/kan-bayashi_ljspeech_fastspeech2">ESPNet FastSpeech2</option>
                                <option value="microsoft/speecht5_tts">SpeechT5</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="setting-group">
                        <label for="code">Enter your code:</label>
                        <textarea id="code" placeholder="def hello_world():&#10;    print('Hello, world!')"></textarea>
                    </div>
                    
                    <button class="button" onclick="generateAudio()">Generate Audio</button>
                </div>
                
                <div id="loading" class="loading" style="display: none;">
                    <div class="spinner"></div>
                    <span>Generating documentation and audio...</span>
                </div>
                
                <div id="error" class="error" style="display: none;"></div>
                
                <div id="results" class="results" style="display: none;">
                    <div class="result-section">
                        <h3>📝 Documentation</h3>
                        <div id="documentation" class="documentation"></div>
                    </div>
                    
                    <div class="result-section">
                        <h3>🔊 Audio Summary</h3>
                        <audio id="audio" class="audio-player" controls></audio>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            async function generateAudio() {
                const code = document.getElementById('code').value;
                const model = document.getElementById('model').value;
                
                if (!code.trim()) {
                    showError('Please enter some code');
                    return;
                }
                
                // Show loading
                document.getElementById('loading').style.display = 'flex';
                document.getElementById('error').style.display = 'none';
                document.getElementById('results').style.display = 'none';
                
                try {
                    const response = await fetch('/synthesize', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            code: code,
                            model_id: model
                        })
                    });
                    
                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.detail || 'Failed to generate audio');
                    }
                    
                    // Get headers
                    const documentation = response.headers.get('Documentation');
                    const summary = response.headers.get('Summary');
                    
                    // Get audio blob
                    const audioBlob = await response.blob();
                    const audioUrl = URL.createObjectURL(audioBlob);
                    
                    // Display results
                    document.getElementById('documentation').textContent = documentation || 'No documentation generated';
                    document.getElementById('audio').src = audioUrl;
                    
                    // Hide loading, show results
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('results').style.display = 'block';
                    
                } catch (error) {
                    showError(error.message);
                    document.getElementById('loading').style.display = 'none';
                }
            }
            
            function showError(message) {
                const errorDiv = document.getElementById('error');
                errorDiv.textContent = message;
                errorDiv.style.display = 'block';
            }
            
            // Add keyboard shortcut
            document.addEventListener('keydown', function(e) {
                if (e.ctrlKey && e.key === 'Enter') {
                    generateAudio();
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
