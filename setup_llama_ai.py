#!/usr/bin/env python3
"""
Setup script for Local Llama AI integration

This script helps set up local Llama AI for the Bahar automation system.
It provides multiple options for running Llama locally.
"""

import os
import sys
import subprocess
import requests
from pathlib import Path


def print_header():
    """Print setup header."""
    print("🤖 Local Llama AI Setup for Bahar Automation")
    print("=" * 50)
    print()


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True


def install_package(package_name, install_command=None):
    """Install a Python package."""
    try:
        if install_command:
            subprocess.run(install_command, shell=True, check=True)
        else:
            subprocess.run([sys.executable, "-m", "pip", "install", package_name], check=True)
        print(f"✅ {package_name} installed successfully")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package_name}")
        return False


def test_ollama():
    """Test if Ollama is running."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Ollama is running with {len(models)} models")
            for model in models:
                print(f"   - {model.get('name', 'Unknown')}")
            return True
        else:
            print("❌ Ollama is running but returned an error")
            return False
    except requests.exceptions.RequestException:
        print("❌ Ollama is not running")
        return False


def setup_ollama():
    """Set up Ollama."""
    print("\n🐳 Setting up Ollama...")
    
    # Check if Ollama is installed
    try:
        subprocess.run(["ollama", "--version"], check=True, capture_output=True)
        print("✅ Ollama is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Ollama is not installed")
        print("\n📥 To install Ollama:")
        print("   1. Visit https://ollama.ai")
        print("   2. Download and install for your platform")
        print("   3. Run: ollama pull llama2")
        return False
    
    # Check if Ollama is running
    if not test_ollama():
        print("\n🚀 Starting Ollama...")
        try:
            subprocess.run(["ollama", "serve"], start_new_session=True)
            import time
            time.sleep(3)  # Wait for Ollama to start
            if test_ollama():
                print("✅ Ollama started successfully")
            else:
                print("❌ Failed to start Ollama")
                return False
        except Exception as e:
            print(f"❌ Error starting Ollama: {str(e)}")
            return False
    
    # Check if Llama model is available
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = response.json().get("models", [])
        llama_models = [m for m in models if "llama" in m.get("name", "").lower()]
        
        if llama_models:
            print("✅ Llama model is available")
            return True
        else:
            print("📥 Llama model not found, downloading...")
            subprocess.run(["ollama", "pull", "llama2"], check=True)
            print("✅ Llama model downloaded successfully")
            return True
    except Exception as e:
        print(f"❌ Error checking/downloading model: {str(e)}")
        return False


def setup_llama_cpp():
    """Set up llama-cpp-python."""
    print("\n🐍 Setting up llama-cpp-python...")
    
    # Install llama-cpp-python
    if not install_package("llama-cpp-python"):
        return False
    
    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Check if model file exists
    model_path = os.getenv("LLAMA_MODEL_PATH", "models/llama-2-7b-chat.gguf")
    if Path(model_path).exists():
        print(f"✅ Model found at {model_path}")
        return True
    else:
        print(f"❌ Model not found at {model_path}")
        print("\n📥 To download the model:")
        print("   1. Visit https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF")
        print("   2. Download llama-2-7b-chat.gguf")
        print("   3. Place it in the models/ directory")
        return False


def setup_transformers():
    """Set up transformers library."""
    print("\n🔥 Setting up Transformers...")
    
    # Install required packages
    packages = ["transformers", "torch", "accelerate"]
    for package in packages:
        if not install_package(package):
            return False
    
    # Check Hugging Face token
    token = os.getenv("HUGGINGFACE_TOKEN")
    if not token:
        print("⚠️ HUGGINGFACE_TOKEN not set")
        print("   You'll need a Hugging Face token to download Llama models")
        print("   Get one from: https://huggingface.co/settings/tokens")
        return False
    
    print("✅ Transformers setup completed")
    return True


def test_llama_integration():
    """Test the Llama integration."""
    print("\n🧪 Testing Llama integration...")
    
    try:
        # Import the function
        sys.path.append("jobber_fsm")
        from core.skills.submit_offer_with_ai import call_local_llama
        
        # Test data
        project_info = {
            "title": "Test Web Development Project",
            "description": "Need a website built with modern technologies",
            "budget": "1000 SAR",
            "skills": ["Web Development", "JavaScript", "React"]
        }
        
        user_preferences = {
            "skills": ["Web Development", "JavaScript", "React", "Node.js"],
            "experience": "5 years",
            "rate": "50 USD/hour"
        }
        
        # Test the function
        import asyncio
        result = asyncio.run(call_local_llama(project_info, user_preferences))
        
        if result:
            print("✅ Llama integration test successful")
            print(f"   Generated subject: {result.get('subject', 'N/A')}")
            print(f"   Generated price: {result.get('proposed_price', 'N/A')}")
            return True
        else:
            print("❌ Llama integration test failed - no response generated")
            return False
            
    except Exception as e:
        print(f"❌ Llama integration test error: {str(e)}")
        return False


def create_config_file():
    """Create a sample configuration file."""
    config_content = """# Local Llama AI Configuration
# Choose one of the following options:

# Option 1: Ollama (Recommended for easy setup)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2

# Option 2: llama-cpp-python
# LLAMA_MODEL_PATH=models/llama-2-7b-chat.gguf

# Option 3: Transformers (Hugging Face)
# LLAMA_MODEL_NAME=meta-llama/Llama-2-7b-chat-hf
# HUGGINGFACE_TOKEN=your_huggingface_token_here
"""
    
    config_file = Path(".env.llama")
    with open(config_file, "w") as f:
        f.write(config_content)
    
    print(f"📝 Sample configuration created: {config_file}")
    print("   Copy the relevant settings to your .env file")


def main():
    """Main setup function."""
    print_header()
    
    if not check_python_version():
        return 1
    
    print("Choose your Llama setup option:")
    print("1. Ollama (Recommended - Easy setup)")
    print("2. llama-cpp-python (More control)")
    print("3. Transformers (Hugging Face)")
    print("4. Test existing setup")
    print("5. Create configuration file")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    success = False
    
    if choice == "1":
        success = setup_ollama()
    elif choice == "2":
        success = setup_llama_cpp()
    elif choice == "3":
        success = setup_transformers()
    elif choice == "4":
        success = test_llama_integration()
    elif choice == "5":
        create_config_file()
        success = True
    else:
        print("❌ Invalid choice")
        return 1
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Add the configuration to your .env file")
        print("2. Test the automation: python test_automation_system.py")
        print("3. Run the automation: python jobber_fsm/automation_main.py --cycle")
        return 0
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 