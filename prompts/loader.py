# prompts/loader.py
import json
from pathlib import Path

def load_all_prompts(prompts_dir="prompts"):
    """
    Scans the prompts directory for .json files and loads them.
    Returns a list of prompt dictionaries.
    
    Each prompt dictionary should have:
    - id: unique identifier
    - name: human-readable name
    - description: brief description
    - prompt: the actual prompt text to send to the LLM
    - category: category of the prompt (etl, data_analysis, etc.)
    - expected_output_type: what type of output is expected
    """
    prompt_list = []
    dir_path = Path(prompts_dir)
    
    if not dir_path.exists():
        print(f"⚠️ Warning: Prompts directory '{prompts_dir}' not found.")
        return prompt_list

    for json_file in dir_path.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Validate required fields
                required_fields = ['id', 'name', 'prompt']
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    print(f"⚠️ Warning: Prompt file {json_file} missing required fields: {missing_fields}")
                    continue
                prompt_list.append(data)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in prompt file {json_file}: {e}")
        except Exception as e:
            print(f"❌ Error loading prompt file {json_file}: {e}")
    
    # Sort by id for consistent ordering
    prompt_list.sort(key=lambda x: x.get('id', ''))
            
    return prompt_list

def get_prompt_by_id(prompts, prompt_id):
    """
    Find a prompt by its ID.
    
    Args:
        prompts: List of prompt dictionaries
        prompt_id: The ID to search for
    
    Returns:
        The prompt dictionary or None if not found
    """
    for prompt in prompts:
        if prompt.get('id') == prompt_id:
            return prompt
    return None

def get_prompts_by_category(prompts, category):
    """
    Filter prompts by category.
    
    Args:
        prompts: List of prompt dictionaries
        category: Category to filter by
    
    Returns:
        List of prompts in the specified category
    """
    return [p for p in prompts if p.get('category') == category]
