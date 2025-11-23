import os
import io
import wave
import struct
import math
import asyncio
from typing import AsyncGenerator
from fastapi import HTTPException
import warnings
from TTS.api import TTS
from pydub import AudioSegment
from pathlib import Path
import torch

# Suppress all warnings
warnings.filterwarnings("ignore")

# Define valid vocabulary (alphanumeric + basic punctuation)
VALID_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,?!")

# Set device (GPU if available, else CPU)
device = "cuda" if torch.cuda.is_available() else "cpu"

# Clean text by replacing invalid characters with spaces
def clean_text(text):
    return ''.join(c if c in VALID_CHARS else ' ' for c in text)

# Split text into chunks for TTS processing
def split_text(text, max_length=1000):
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 <= max_length:
            current_chunk.append(word)
            current_length += len(word) + 1
        else:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = len(word) + 1
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

# Convert text to intermediate audio
def text_to_intermediate_audio(text, temp_output_base="temp_audio", output_dir="temp"):
    """Convert text to audio using TTS model."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=(device == "cuda"))
        chunks = split_text(text)
        temp_files = []
        
        for i, chunk in enumerate(chunks):
            temp_file = f"{output_dir}/{temp_output_base}_{i}.wav"
            tts.tts_to_file(text=chunk, file_path=temp_file)
            temp_files.append(temp_file)
        
        # Combine audio chunks
        combined = AudioSegment.empty()
        for temp_file in temp_files:
            combined += AudioSegment.from_file(temp_file)
            os.remove(temp_file)
        
        combined_output = f"{output_dir}/{temp_output_base}.wav"
        combined.export(combined_output, format="wav")
        
        # Read the final audio file and return bytes
        with open(combined_output, 'rb') as f:
            audio_bytes = f.read()
        
        # Clean up
        os.remove(combined_output)
        if os.path.exists(output_dir) and not os.listdir(output_dir):
            os.rmdir(output_dir)
        
        return audio_bytes
        
    except Exception as e:
        print(f"TTS error: {e}")
        # Fallback to simple tone generation
        return generate_simple_audio(text)

def generate_simple_audio(text: str) -> bytes:
    """Generate simple audio as fallback."""
    try:
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
                    # Simple sine wave
                    t = j / sample_rate
                    sample = int(32767 * 0.3 * math.sin(2 * math.pi * freq * t))
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
        return wav_buffer.getvalue()
        
    except Exception as e:
        print(f"Simple audio generation failed: {e}")
        return b""

def stream_tts_audio_sync(text: str, model_id: str = "local") -> bytes:
    """Synchronous version of TTS audio generation for Streamlit."""
    # Clean the text first
    cleaned_text = clean_text(text)
    
    # Use the intermediate audio function
    audio_bytes = text_to_intermediate_audio(cleaned_text)
    
    return audio_bytes

async def stream_tts_audio(text: str, model_id: str = "local") -> AsyncGenerator[bytes, None]:
    """Stream TTS audio using TTS model."""
    audio_bytes = stream_tts_audio_sync(text, model_id)
    yield audio_bytes