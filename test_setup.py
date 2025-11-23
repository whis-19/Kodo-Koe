#!/usr/bin/env python3
"""
Test script to verify the Code to Audio System setup
"""

import sys
import os
import requests
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\nChecking dependencies...")
    
    # Required dependencies
    required_deps = [
        "fastapi", "uvicorn", "requests", "pydantic", 
        "python-dotenv"
    ]
    
    # Optional dependencies
    optional_deps = [
        ("transformers", "for better documentation generation"),
        ("pyttsx3", "for better local text-to-speech"),
        ("torch", "for local model support")
    ]
    
    for dep in required_deps:
        try:
            __import__(dep)
            print(f"✅ {dep} installed")
        except ImportError:
            print(f"❌ {dep} not installed (required)")
            return False
    
    for dep, description in optional_deps:
        try:
            __import__(dep)
            print(f"✅ {dep} installed ({description})")
        except ImportError:
            print(f"⚠️  {dep} not installed ({description}) - optional")
    
    return True

def check_env_file():
    """Check if .env file exists"""
    print("\nChecking environment file...")
    
    env_file = Path(".env")
    
    if not env_file.exists():
        print("⚠️  .env not found (optional)")
        print("   You can create .env from .env.example if you want to use Hugging Face API")
    else:
        print("✅ .env exists")
    
    return True

def check_api_keys():
    """Check if API keys are configured (optional)"""
    print("\nChecking API configuration...")
    
    # Load .env if it exists
    from dotenv import load_dotenv
    if Path(".env").exists():
        load_dotenv(".env")
    
    hf_token = os.getenv("HUGGINGFACE_API_TOKEN")
    
    if hf_token:
        print("✅ HUGGINGFACE_API_TOKEN configured (will use Hugging Face TTS)")
    else:
        print("✅ No HUGGINGFACE_API_TOKEN (will use local TTS synthesis)")
    
    return True

def test_application_health():
    """Test if the application is running"""
    print("\nTesting application connection...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Application is running and healthy")
            return True
        else:
            print(f"❌ Application returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Application is not running (connection refused)")
        print("   Start with: python -m uvicorn app:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error connecting to application: {e}")
        return False

def test_web_interface():
    """Test if the web interface is accessible"""
    print("\nTesting web interface...")
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200 and "Code to Audio System" in response.text:
            print("✅ Web interface is accessible")
            return True
        else:
            print(f"❌ Web interface not accessible (status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Error accessing web interface: {e}")
        return False

def main():
    """Run all checks"""
    print("=== Code to Audio System Setup Check ===\n")
    
    all_good = True
    
    all_good &= check_python_version()
    all_good &= check_dependencies()
    all_good &= check_env_file()
    all_good &= check_api_keys()
    
    if all_good:
        print("\n✅ All checks passed!")
        print("\nTo start the system:")
        print("  1. Start application: python -m uvicorn app:app --reload")
        print("  2. Or use: start.bat (Windows) or start.sh (Linux/Mac)")
        print("\nThen visit: http://localhost:8000")
        print("\nNote: The system works without any API keys!")
        print("  - Without Hugging Face token: Uses local text-to-speech synthesis")
        print("  - With Hugging Face token: Uses high-quality TTS models")
        
        # Test application if it's running
        test_application_health()
        test_web_interface()
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
