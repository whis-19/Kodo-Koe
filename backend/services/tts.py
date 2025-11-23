import os
import io
import wave
import struct
import tempfile
import math
import asyncio
from typing import AsyncGenerator
from fastapi import HTTPException

def stream_tts_audio_sync(text: str, model_id: str = "local") -> bytes:
    """Synchronous version of TTS audio generation for Streamlit."""
    # Run the async version in an event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Collect all chunks from async generator
        audio_data = b''
        async def collect_chunks():
            data = b''
            async for chunk in stream_tts_audio(text, model_id):
                data += chunk
            return data
        
        audio_data = loop.run_until_complete(collect_chunks())
        return audio_data
    finally:
        loop.close()

async def stream_tts_audio(text: str, model_id: str = "local") -> AsyncGenerator[bytes, None]:
    """Stream TTS audio using local open-source models."""
    
    # Try different TTS methods in order of preference
    try:
        # 1. Try XTTS (high quality local TTS)
        async for chunk in stream_tts_xtts(text, model_id):
            yield chunk
        return
    except Exception as e:
        print(f"XTTS failed: {e}")
    
    try:
        # 2. Try pyttsx3 (system TTS)
        async for chunk in stream_tts_pyttsx3(text, model_id):
            yield chunk
        return
    except Exception as e:
        print(f"pyttsx3 failed: {e}")
    
    try:
        # 3. Try basic speech synthesis
        async for chunk in stream_tts_basic(text, model_id):
            yield chunk
        return
    except Exception as e:
        print(f"Basic TTS failed: {e}")
    
    # 4. Fallback to simple tone generation
    try:
        async for chunk in stream_tts_simple(text, model_id):
            yield chunk
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"All TTS methods failed: {str(e)}")

async def stream_tts_xtts(text: str, model_id: str = "local") -> AsyncGenerator[bytes, None]:
    """Stream TTS audio using XTTS (Coqui) - high quality local TTS."""
    try:
        from TTS.api import TTS
        import torch
        
        # Check if CUDA is available for faster processing
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Try different XTTS models
        models_to_try = [
            "tts_models/multilingual/multi-dataset/xtts_v2",  # Best multilingual
            "tts_models/en/ljspeech/tacotron2-DDC",  # English only
            "tts_models/en/ljspeech/fast_pitch",  # Fast
        ]
        
        for model_name in models_to_try:
            try:
                print(f"Loading {model_name}...")
                tts = TTS(model_name=model_name).to(device)
                
                # Generate speech to temporary file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_path = temp_file.name
                
                # XTTS works better with longer text
                if len(text) < 10:
                    text = text + ". "  # Add punctuation for better prosody
                
                tts.tts_to_file(text=text, speaker=tts.speakers[0] if hasattr(tts, 'speakers') else None, 
                             language="en", file_path=temp_path)
                
                # Read the file and yield in chunks
                with open(temp_path, 'rb') as f:
                    while True:
                        chunk = f.read(1024)
                        if not chunk:
                            break
                        yield chunk
                
                # Clean up
                os.unlink(temp_path)
                return
                
            except Exception as e:
                print(f"Failed to load {model_name}: {e}")
                continue
        
        raise Exception("All XTTS models failed")
        
    except ImportError:
        raise Exception("TTS/Coqui not installed")
    except Exception as e:
        raise Exception(f"XTTS error: {e}")

async def stream_tts_pyttsx3(text: str, model_id: str = "local") -> AsyncGenerator[bytes, None]:
    """Stream TTS audio using pyttsx3 (system TTS)."""
    try:
        import pyttsx3
        
        # Initialize TTS engine
        engine = pyttsx3.init()
        
        # Create temporary file for audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Save speech to file
        engine.save_to_file(text, temp_path)
        engine.runAndWait()
        
        # Read the file and yield in chunks
        with open(temp_path, 'rb') as f:
            while True:
                chunk = f.read(1024)
                if not chunk:
                    break
                yield chunk
        
        # Clean up
        os.unlink(temp_path)
        
    except ImportError:
        raise Exception("pyttsx3 not installed")
    except Exception as e:
        raise Exception(f"pyttsx3 error: {e}")

async def stream_tts_basic(text: str, model_id: str = "local") -> AsyncGenerator[bytes, None]:
    """Stream TTS audio using basic speech synthesis."""
    try:
        import numpy as np
        from scipy.io import wavfile
        
        # Generate basic speech-like audio
        sample_rate = 22050
        duration = min(len(text) * 0.1, 5.0)
        
        # Create time array
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Generate carrier frequency (modulated by text)
        carrier_freq = 200  # Base frequency
        
        # Create amplitude envelope based on text
        audio = np.zeros_like(t)
        
        for i, char in enumerate(text):
            if char == ' ':
                # Silence for spaces
                amplitude = 0
            else:
                # Different amplitude for different characters
                amplitude = 0.3 + 0.2 * (ord(char.lower()) % 10) / 10
            
            # Time window for this character
            char_start = i * len(t) // len(text)
            char_end = (i + 1) * len(t) // len(text)
            char_end = min(char_end, len(t))
            
            # Apply amplitude with some modulation
            char_t = t[char_start:char_end]
            if len(char_t) > 0:
                # Add some frequency modulation for more natural sound
                freq_mod = carrier_freq * (1 + 0.1 * np.sin(2 * np.pi * 5 * char_t))
                audio[char_start:char_end] = amplitude * np.sin(2 * np.pi * freq_mod * char_t)
        
        # Apply envelope for smoother start/stop
        envelope = np.ones_like(audio)
        fade_samples = int(0.1 * sample_rate)  # 100ms fade
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        audio *= envelope
        
        # Normalize
        audio = audio / np.max(np.abs(audio)) * 0.8
        
        # Convert to 16-bit integers
        audio_int16 = (audio * 32767).astype(np.int16)
        
        # Write to temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        wavfile.write(temp_path, sample_rate, audio_int16)
        
        # Read the file and yield in chunks
        with open(temp_path, 'rb') as f:
            while True:
                chunk = f.read(1024)
                if not chunk:
                    break
                yield chunk
        
        # Clean up
        os.unlink(temp_path)
        
    except ImportError:
        raise Exception("numpy/scipy not installed")
    except Exception as e:
        raise Exception(f"Basic TTS error: {e}")

async def stream_tts_simple(text: str, model_id: str = "local") -> AsyncGenerator[bytes, None]:
    """Stream TTS audio using simple tone generation (ultimate fallback)."""
    
    # Create a simple mono WAV file
    sample_rate = 22050  # Hz
    duration = min(len(text) * 0.1, 5.0)  # 0.1 seconds per character, max 5 seconds
    
    # Generate a simple tone pattern based on text
    audio_samples = []
    for i, char in enumerate(text):
        if char == ' ':
            # Silence for spaces
            freq = 0
        else:
            # Different frequency for different characters
            char_code = ord(char.lower()) % 26 + 1  # A-Z mapped to 1-26
            freq = 200 + (char_code * 20)  # 200-720 Hz range
        
        # Generate samples for this character
        char_duration = 0.1  # 100ms per character
        char_samples = int(sample_rate * char_duration)
        
        for j in range(char_samples):
            if freq == 0:
                # Silence
                sample = 0
            else:
                # Simple sine wave with some modulation
                t = j / sample_rate
                sample = int(32767 * 0.3 * (1 + 0.5 * (i % 3)) * 
                           (0.5 + 0.5 * (j % 1000) / 1000) *  # Fade in/out
                           math.sin(2 * math.pi * freq * t))  # Use math for sine
            audio_samples.append(sample)
    
    # Convert to WAV format
    wav_buffer = io.BytesIO()
    
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        # Pack samples into bytes
        packed_samples = struct.pack('<' + 'h' * len(audio_samples), *audio_samples)
        wav_file.writeframes(packed_samples)
    
    wav_buffer.seek(0)
    audio_data = wav_buffer.getvalue()
    
    # Yield the audio data in chunks
    chunk_size = 1024
    for i in range(0, len(audio_data), chunk_size):
        yield audio_data[i:i + chunk_size]

# Fallback: Use Hugging Face API if token is available
async def stream_tts_audio_huggingface(text: str, model_id: str = "facebook/fastspeech2-en-ljspeech") -> AsyncGenerator[bytes, None]:
    """Stream TTS audio from Hugging Face Inference API (if token available)."""
    api_token = os.getenv("HUGGINGFACE_API_TOKEN")
    if not api_token:
        # No token, fallback to local
        async for chunk in stream_tts_audio(text, model_id):
            yield chunk
        return
    
    try:
        import requests
        
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        with requests.post(
            f"https://api-inference.huggingface.co/models/{model_id}",
            headers=headers,
            json={"inputs": text},
            stream=True
        ) as response:
            if response.status_code != 200:
                # API failed, fallback to local
                async for chunk in stream_tts_audio(text, model_id):
                    yield chunk
                return
            
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk
                    
    except Exception:
        # Any error, fallback to local
        async for chunk in stream_tts_audio(text, model_id):
            yield chunk