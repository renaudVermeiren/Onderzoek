# core/ollama_client.py
import requests
import subprocess
import json
import sys
from config import TIMEOUT_SECONDS, LLM_TEMPERATURE, LLM_SEED

OLLAMA_API_BASE = "http://localhost:11434"

def check_ollama_running():
    """Check if Ollama is running locally, exit if not."""
    try:
        response = requests.get(f"{OLLAMA_API_BASE}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Connected to local Ollama instance")
            return True
    except requests.exceptions.ConnectionError:
        pass
    
    print("❌ ERROR: Could not connect to Ollama. Is Ollama running?")
    sys.exit(1)

def get_available_models(configured_models=None):
    """
    Fetch all local models matching `ollama list` output.
    If configured_models is provided, only return models that are in that list.
    """
    models = []
    all_models = []
    
    # Method 1: Ollama REST API (preferred)
    try:
        response = requests.get(f"{OLLAMA_API_BASE}/api/tags", timeout=5)
        if response.status_code == 200:
            all_models = [model["name"] for model in response.json().get("models", [])]
    except Exception:
        pass
    
    # Method 2: Subprocess fallback
    if not all_models:
        print("⚠️ Ollama API unavailable, falling back to `ollama list` subprocess")
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                for line in lines[1:]:
                    if line.strip():
                        model_name = line.split()[0]
                        all_models.append(model_name)
        except Exception as e:
            print(f"❌ ERROR: Failed to fetch Ollama models: {e}")
            sys.exit(1)
    
    # Filter by configured models if specified
    if configured_models:
        models = [m for m in all_models if m in configured_models]
        if not models:
            print(f"❌ ERROR: None of the configured models {configured_models} are available in Ollama.")
            print(f"   Available models: {all_models}")
            sys.exit(1)
    else:
        models = all_models
    
    if not models:
        print("❌ ERROR: No Ollama models found. Use `ollama pull <model>` to download models first.")
        sys.exit(1)
    
    print(f"📋 Models to use: {models}")
    return models

def send_prompt_to_model(model_name, prompt_content, timeout=TIMEOUT_SECONDS):
    """
    Send prompt to Ollama model and return raw response.
    
    Args:
        model_name: Name of the Ollama model
        prompt_content: The prompt text to send
        timeout: Request timeout in seconds
    
    Returns:
        Dictionary with response data
    """
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt_content}],
        "stream": False,
        "options": {
            "temperature": LLM_TEMPERATURE,
            "seed": LLM_SEED
        }
    }
    
    try:
        response = requests.post(
            f"{OLLAMA_API_BASE}/api/chat",
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        raise TimeoutError(f"Model {model_name} timed out after {timeout} seconds")
    except Exception as e:
        raise RuntimeError(f"Failed to send prompt to {model_name}: {e}")

def extract_code_from_response(response_json):
    """
    Extract generated code from Ollama response.
    Removes markdown code block markers and any trailing text.
    
    Args:
        response_json: The JSON response from Ollama
    
    Returns:
        String containing the generated code (cleaned)
    """
    try:
        content = response_json["message"]["content"]
        content = content.strip()
        
        # Remove opening code block marker (```python, ```py, or just ```)
        if content.startswith("```"):
            # Find the first newline after the opening ```
            first_newline = content.find("\n")
            if first_newline != -1:
                content = content[first_newline:].strip()
        
        # Find and remove the closing ``` and everything after it
        # This handles cases where there's text after the code block
        closing_marker = content.rfind("```")
        if closing_marker != -1:
            content = content[:closing_marker].strip()
        
        return content
    except KeyError as e:
        raise ValueError(f"Invalid response format: missing key {e}")
    except Exception as e:
        raise ValueError(f"Failed to extract code from response: {e}")
