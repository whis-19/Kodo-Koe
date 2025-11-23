import streamlit as st
import requests
import io
import wave
import sys
import os

# Add backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services import tts, code_processor
from models import CodeRequest

# Configure Streamlit page
st.set_page_config(
    page_title="Code to Audio System",
    page_icon="🔊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .result-section {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .documentation {
        background: white;
        border: 1px solid #e1e5e9;
        border-radius: 4px;
        padding: 1rem;
        font-family: 'Monaco', 'Courier New', monospace;
        white-space: pre-wrap;
        max-height: 300px;
        overflow-y: auto;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
        font-weight: 600;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🔊 Code to Audio System</h1>
    <p>Convert your code into spoken audio summaries</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for settings
st.sidebar.header("Settings")

# TTS Model selection
model_options = [
    ("xtts", "XTTS (Coqui) - High Quality Local"),
    ("pyttsx3", "System TTS - Built-in Voice"),
    ("basic", "Basic Synthesis - NumPy/SciPy"),
    ("simple", "Simple Tones - Fallback"),
    ("facebook/fastspeech2-en-ljspeech", "FastSpeech2 (HF API)"),
    ("espnet/kan-bayashi_ljspeech_fastspeech2", "ESPNet FastSpeech2"),
    ("microsoft/speecht5_tts", "SpeechT5"),
]

selected_model = st.sidebar.selectbox(
    "TTS Model:",
    options=[option[1] for option in model_options],
    index=0,
    help="Choose the text-to-speech model to use"
)

# Get the model ID from selection
model_id = model_options[[option[1] for option in model_options].index(selected_model)][0]

# Main content
col1, col2 = st.columns([3, 1])

with col1:
    st.header("Code Input")
    code_input = st.text_area(
        "Enter your code:",
        height=300,
        placeholder="def hello_world():\n    print('Hello, world!')",
        help="Paste or type your Python code here"
    )

with col2:
    st.header("Quick Info")
    st.info("""
    **How it works:**
    1. Analyze your code
    2. Generate documentation
    3. Create audio summary
    4. Play or download
    
    **Models available:**
    - Local (no API needed)
    - Cloud (optional)
    """)

# Generate button
generate_button = st.button("🚀 Generate Audio", type="primary", use_container_width=True)

# Results section
if generate_button or 'results_generated' in st.session_state:
    if not code_input.strip():
        st.error("Please enter some code first!")
    else:
        # Show loading
        with st.spinner("🔄 Generating documentation and audio..."):
            try:
                # Generate documentation
                doc_result = code_processor.generate_documentation(code_input)
                
                # Generate audio (using sync version for Streamlit)
                audio_data = tts.stream_tts_audio_sync(doc_result["summary"], model_id)
                
                # Store results in session state
                st.session_state.results_generated = True
                st.session_state.documentation = doc_result["documentation"]
                st.session_state.summary = doc_result["summary"]
                st.session_state.audio_data = audio_data
                
                # Clear any previous errors
                if 'error' in st.session_state:
                    del st.session_state.error
                    
            except Exception as e:
                st.session_state.error = str(e)
                st.error(f"Error: {e}")

# Display results
if 'results_generated' in st.session_state:
    # Documentation section
    st.markdown('<div class="result-section">', unsafe_allow_html=True)
    st.subheader("📝 Documentation")
    st.markdown(f'<div class="documentation">{st.session_state.documentation}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Summary section
    st.subheader("📄 Summary")
    st.info(st.session_state.summary)
    
    # Audio section
    st.subheader("🔊 Audio Summary")
    
    # Create audio player
    if 'audio_data' in st.session_state and st.session_state.audio_data:
        # Convert bytes to audio file for Streamlit
        audio_bytes = st.session_state.audio_data
        st.audio(audio_bytes, format='audio/wav')
        
        # Download button
        st.download_button(
            label="📥 Download Audio",
            data=audio_bytes,
            file_name="code_summary.wav",
            mime="audio/wav"
        )
    else:
        st.warning("Audio generation failed")

# Error display
if 'error' in st.session_state:
    st.error(st.session_state.error)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🔊 Code to Audio System - Powered by Open Source Models</p>
    <p>Works offline with local TTS and documentation generation</p>
</div>
""", unsafe_allow_html=True)

# Health check in sidebar
if st.sidebar.button("🔍 Check System Health"):
    try:
        # Test basic functionality
        test_code = "print('Hello')"
        doc_result = code_processor.generate_documentation(test_code)
        audio_data = tts.stream_tts_audio_sync("Test", "simple")
        
        st.sidebar.success("✅ System healthy!")
        st.sidebar.info(f"📝 Documentation: {len(doc_result['documentation'])} chars")
        st.sidebar.info(f"🔊 Audio generated: {len(audio_data)} bytes")
        
    except Exception as e:
        st.sidebar.error(f"❌ System error: {e}")

# Model info in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### Model Information")
if "xtts" in model_id:
    st.sidebar.info("🎯 **XTTS**: High-quality multilingual TTS by Coqui")
elif "pyttsx3" in model_id:
    st.sidebar.info("🖥️ **System TTS**: Uses your OS built-in voices")
elif "basic" in model_id:
    st.sidebar.info("🔬 **Basic**: NumPy/SciPy based synthesis")
elif "simple" in model_id:
    st.sidebar.info("🎵 **Simple**: Sine wave tone generation")
else:
    st.sidebar.info("☁️ **Cloud**: Hugging Face API model")
