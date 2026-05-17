# config.py

# List of specific models you want to test. 
# The tool will only use models from this list that are also available in `ollama list`.
MODELS_TO_TEST = [
   'deepseek-coder-v2:latest',
   'gemma4:latest',
  # 'starcoder2:latest',
   'mistral:latest',
   'llama3:latest',
   'qwen2.5-coder:latest'
]

# Directory for saving generated code outputs
OUTPUT_DIR = "generated_code"

# Directory containing prompt JSON files
PROMPTS_DIR = "prompts"

# Directory for saving evaluation results
RESULTS_DIR = "results"

# Timeout for LLM requests (in seconds)
TIMEOUT_SECONDS = 120

# Reproducibility settings for LLM generation
# Temperature: 0.0 = deterministic, higher = more creative
LLM_TEMPERATURE = 0.0
# Seed: fixed value for reproducible outputs across runs
LLM_SEED = 42
