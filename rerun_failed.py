#!/usr/bin/env python3
"""
Standalone script to re-run a single failed generation.
Re-generates code for deepseek-coder-v2 task_01 and saves it properly.
"""

import json
import shutil
from pathlib import Path

# Import existing utilities
from core.ollama_client import send_prompt_to_model, extract_code_from_response


def rerun_single_generation(model_name: str, task_folder: str, output_base: str = "generated_code"):
    """Re-run code generation for a single task."""
    
    task_path = Path(task_folder)
    prompt_file = task_path / "prompt.json"
    
    if not prompt_file.exists():
        print(f"ERROR: Prompt file not found: {prompt_file}")
        return False
    
    # Load prompt
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_data = json.load(f)
    
    prompt_content = prompt_data["prompt"]
    task_id = prompt_data["id"]
    task_name = prompt_data["name"]
    
    print(f"Re-running: {model_name} - {task_id}: {task_name}")
    print(f"Task folder: {task_path}")
    
    # Create output directory
    safe_model_name = model_name.replace(":", "_")
    output_dir = Path(output_base) / safe_model_name / task_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy input files
    input_files = prompt_data.get("input_files", [])
    for input_file in input_files:
        src = task_path / input_file
        if src.exists():
            dst = output_dir / input_file
            shutil.copy2(src, dst)
            print(f"  Copied: {input_file}")
    
    # Generate code
    print(f"  Sending to {model_name}...")
    try:
        raw_response = send_prompt_to_model(model_name, prompt_content)
        
        if not raw_response:
            print(f"  ERROR: No response from {model_name}")
            return False
        
        # Extract code
        extracted_code = extract_code_from_response(raw_response)
        
        if not extracted_code or len(extracted_code.strip()) < 10:
            print(f"  WARNING: No code extracted, saving raw response")
            extracted_code = raw_response
        else:
            print(f"  Extracted {len(extracted_code)} characters of code")
        
        # Save generated script
        script_file = output_dir / "generated_script.py"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(extracted_code)
        
        print(f"  Saved to: {script_file}")
        print(f"  SUCCESS!")
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("RE-RUN FAILED GENERATION")
    print("=" * 70)
    
    model = "deepseek-coder-v2:latest"
    task = "prompts/task_01_missing_values"
    
    success = rerun_single_generation(model, task)
    
    print("=" * 70)
    if success:
        print("SUCCESS: Re-generation complete!")
    else:
        print("FAILED: Re-generation failed. Check the error above.")
    print("=" * 70)
