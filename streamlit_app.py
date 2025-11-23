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

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    .result-section {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #e1e5e9;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .result-section h3 {
        margin: 0 0 1rem 0;
        color: #2c3e50;
        font-size: 1.3rem;
        font-weight: 600;
    }
    .documentation {
        background: white;
        border: 2px solid #e1e5e9;
        border-radius: 8px;
        padding: 1.5rem;
        font-family: 'Monaco', 'Courier New', monospace;
        white-space: pre-wrap;
        max-height: 400px;
        overflow-y: auto;
        font-size: 0.95rem;
        line-height: 1.5;
        color: #2c3e50;
    }
    .stTextArea textarea {
        border: 2px solid #e1e5e9;
        border-radius: 8px;
        font-family: 'Monaco', 'Courier New', monospace;
        font-size: 0.95rem;
    }
    .stTextArea textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    .stSelectbox > div > div {
        background: white;
        border: 2px solid #e1e5e9;
        border-radius: 8px;
    }
    .stSelectbox > div > div:focus {
        border-color: #667eea;
    }
    .sidebar-content {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .metric-card {
        background: white;
        border: 1px solid #e1e5e9;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        text-align: center;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #667eea;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
        margin-top: 0.25rem;
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
st.sidebar.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
st.sidebar.header("⚙️ Settings")

# Check for Gemini API key from environment
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Show API status
if gemini_api_key:
    st.sidebar.success("🤖 Gemini API configured")
else:
    st.sidebar.info("🔧 Using rule-based analysis (no API key)")

st.sidebar.markdown("---")

# TTS Model info (fixed now)
st.sidebar.markdown("### 🔊 TTS Model")
st.sidebar.info("🎯 **Tacotron2-DDC**: High-quality TTS by Coqui")

# Get the model ID (fixed to use our TTS model)
model_id = "tts_models/en/ljspeech/tacotron2-DDC"

# Quick stats in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Quick Stats")

if 'results_generated' in st.session_state:
    doc_length = len(st.session_state.get('documentation', ''))
    audio_size = len(st.session_state.get('audio_data', b''))
    
    st.sidebar.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{doc_length}</div>
        <div class="metric-label">Documentation Characters</div>
    </div>
    <div class="metric-card">
        <div class="metric-value">{audio_size}</div>
        <div class="metric-label">Audio Bytes</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.info("👆 Generate audio to see stats")

st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Main content area
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown('<div class="result-section">', unsafe_allow_html=True)
    st.header("💻 Code Input")
    code_input = st.text_area(
        "Enter your Python code:",
        height=300,
        placeholder="def hello_world():\n    print('Hello, world!')\n    return 'success'",
        help="Paste or type your Python code here for analysis and audio generation"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    st.header("🚀 Quick Actions")
    
    # Generate button with better styling
    if st.button("🔥 Generate Audio", type="primary", use_container_width=True):
        if not code_input.strip():
            st.error("⚠️ Please enter some code first!")
            st.session_state.error = "Please enter some code first!"
        else:
            # Set a flag to trigger generation
            st.session_state.generate_triggered = True
    
    # Quick example code
    st.markdown("---")
    st.subheader("📝 Example Code")
    
    if st.button("📋 Load Example", use_container_width=True):
        example_code = """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Test the function
for i in range(5):
    print(f"F({i}) = {fibonacci(i)}")"""
        st.session_state.example_code = example_code
    
    if 'example_code' in st.session_state:
        st.code(st.session_state.example_code, language='python')
        if st.button("📤 Use This Code", use_container_width=True):
            st.session_state.code_to_use = st.session_state.example_code
    
    st.markdown('</div>', unsafe_allow_html=True)

# Initialize code_input if not defined
if 'code_input' not in locals():
    code_input = ""

# Use example code if selected
if 'code_to_use' in st.session_state:
    code_input = st.session_state.code_to_use
    st.session_state.code_to_use = None  # Clear after use

# Results section
if 'generate_triggered' in st.session_state or ('results_generated' in st.session_state and code_input.strip()):
    if not code_input.strip():
        st.error("⚠️ Please enter some code first!")
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
                st.session_state.last_code = code_input
                
                # Clear any previous errors and triggers
                if 'error' in st.session_state:
                    del st.session_state.error
                if 'generate_triggered' in st.session_state:
                    del st.session_state.generate_triggered
                    
            except Exception as e:
                st.session_state.error = str(e)
                st.error(f"❌ Error: {e}")
                if 'generate_triggered' in st.session_state:
                    del st.session_state.generate_triggered

# Display results
if 'results_generated' in st.session_state and st.session_state.last_code == code_input:
    # Documentation section
    st.markdown('<div class="result-section">', unsafe_allow_html=True)
    st.subheader("📝 Documentation")
    st.markdown(f'<div class="documentation">{st.session_state.documentation}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Summary section
    st.markdown('<div class="result-section">', unsafe_allow_html=True)
    st.subheader("📄 Summary")
    st.info(st.session_state.summary)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Audio section
    st.markdown('<div class="result-section">', unsafe_allow_html=True)
    st.subheader("🔊 Audio Summary")
    
    # Create audio player
    if 'audio_data' in st.session_state and st.session_state.audio_data:
        # Convert bytes to audio file for Streamlit
        audio_bytes = st.session_state.audio_data
        st.audio(audio_bytes, format='audio/wav')
        
        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.download_button(
                label="📥 Download WAV",
                data=audio_bytes,
                file_name="code_summary.wav",
                mime="audio/wav",
                use_container_width=True
            )
        with col2:
            if st.button("🔄 Regenerate Audio", use_container_width=True):
                st.session_state.generate_triggered = True
        with col3:
            if st.button("🗑️ Clear Results", use_container_width=True):
                # Clear session state
                keys_to_clear = ['results_generated', 'documentation', 'summary', 'audio_data', 'last_code']
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    else:
        st.warning("🔇 Audio generation failed")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Error display
if 'error' in st.session_state:
    st.error(f"❌ {st.session_state.error}")
    if st.button("🔄 Retry"):
        st.session_state.generate_triggered = True
        if 'error' in st.session_state:
            del st.session_state.error

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
        
        # Test documentation generation
        doc_result = code_processor.generate_documentation(test_code)
        
        # Test TTS
        audio_data = tts.stream_tts_audio_sync("Test", "simple")
        
        # Check if Gemini is available
        gemini_status = "✅ Configured" if gemini_api_key else "🔧 Not configured"
        
        st.sidebar.success("✅ System healthy!")
        st.sidebar.info(f"📝 Documentation: {len(doc_result['documentation'])} chars")
        st.sidebar.info(f"🔊 Audio generated: {len(audio_data)} bytes")
        st.sidebar.info(f"🤖 Gemini API: {gemini_status}")
        
    except Exception as e:
        st.sidebar.error(f"❌ System error: {e}")

# Model info in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### Model Information")
st.sidebar.info("🎯 **Tacotron2-DDC**: High-quality TTS by Coqui\n\n🤖 **Gemini Pro**: AI-powered documentation generation when API key is provided")
