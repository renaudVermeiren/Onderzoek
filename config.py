# config.py

# List of specific models you want to test. 
# The tool will only use models from this list that are also available in `ollama list`.
MODELS_TO_TEST = [
   'deepseek-coder-v2:latest',
   'gemma4:latest',
   'starcoder2:latest',
   'llama3:latest'
]

# Directory for saving generated code outputs
OUTPUT_DIR = "generated_code"

# Directory containing prompt JSON files
PROMPTS_DIR = "prompts"

# Directory for saving evaluation results
RESULTS_DIR = "results"

# Timeout for LLM requests (in seconds)
TIMEOUT_SECONDS = 120
