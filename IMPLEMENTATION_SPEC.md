# ISO/IEC 5055:2021 Ollama Code Evaluator - Implementation Specification

## Project Overview
Build a modular Python tool that evaluates Python code against the ISO/IEC 5055:2021 standard using local Ollama models. The tool automatically runs all available Ollama models to compare their evaluation performance, includes static analysis (Radon/Pylint/Bandit), and saves results to CSV.

## Core Requirements

### Mandatory Features
1. **Exclusive Ollama Provider**: Only use local Ollama, no external APIs
2. **Model Gating**: Only use models from `ollama list` command output
3. **All Models Evaluation**: Automatically iterate through every locally available Ollama model
4. **Single File Input**: Evaluate one Python file passed via CLI argument
5. **Static Analysis**: Include Radon (maintainability/complexity), Pylint (coding standards), Bandit (security)
6. **Prompt Storage**: Dedicated editable file for adding evaluation prompts
7. **CSV Output**: Save all results to timestamped CSV with rows per (model, prompt)
8. **Progress Printing**: Mandatory print statements at every execution step
9. **Error Handling**: Exit with error if any static tool is missing

### ISO 5055 Alignment
All metrics map to 4 ISO/IEC 5055:2021 categories:
- **Maintainability**: Code modification difficulty (Radon MI, complexity)
- **Reliability**: Runtime fault risks (Pylint errors, cyclomatic complexity)
- **Performance Efficiency**: Resource consumption issues (code statistics)
- **Security**: Vulnerability weaknesses (Bandit findings, CWE references)

## Project Structure

All files in single directory (`C:\Users\Renaud\Desktop\Onderzoek\` or equivalent):

```
project_root/
├── requirements.txt       # All dependencies
├── prompts.py             # Editable prompt storage
├── ollama_utils.py        # Ollama integration
├── static_analysis.py     # Radon/Pylint/Bandit
├── csv_writer.py          # CSV export
└── main.py                # Entry point
```

## File Specifications

### 1. requirements.txt
**Purpose**: List all Python dependencies with versions

**Content**:
```
certifi==2026.4.22
charset-normalizer==3.4.7
idna==3.13
requests==2.33.1
urllib3==2.6.3
ollama>=0.1.0
radon>=6.0.1
pylint>=3.0.0
bandit>=1.7.5
pandas>=2.0.0
```

**Note**: Must include all static analysis tools. Tool exits with error if any are missing.

---

### 2. prompts.py
**Purpose**: Dedicated editable storage for evaluation prompts. Users add prompts here without modifying other files.

**Content**:
```python
# prompts.py
"""
Editable prompt storage for ISO/IEC 5055:2021 evaluations.
Add new prompts to the ISO5055_PROMPTS list below - no other files need modification.
Each prompt must have:
- id: Unique string identifier
- name: Human-readable name for CSV output
- content: Full prompt text (must include {code} placeholder for code insertion)
- focus_categories: List of ISO 5055 categories covered (for reference)
"""

ISO5055_PROMPTS = [
    # Default pre-loaded prompt (public domain ISO 5055 summary, no copyrighted content)
    {
        "id": "default_iso5055",
        "name": "Full ISO/IEC 5055 Evaluation",
        "description": "Evaluates code against all 4 ISO 5055 categories: Maintainability, Reliability, Performance Efficiency, Security",
        "content": """You are a code quality evaluator. Evaluate the provided Python code against the ISO/IEC 5055:2021 standard, which measures 4 quality characteristics:
1. Maintainability: Weaknesses that make code harder to modify/test (e.g., high cyclomatic complexity, poor documentation, CWE-1121)
2. Reliability: Weaknesses that cause runtime faults (e.g., unhandled exceptions, CWE-703)
3. Performance Efficiency: Weaknesses that cause excessive resource use (e.g., algorithmic complexity, CWE-407)
4. Security: Weaknesses that introduce vulnerabilities (e.g., injection flaws, CWE-89)

Return ONLY valid JSON in this exact format, no extra text:
{
    "maintainability_issues": <integer count>,
    "reliability_issues": <integer count>,
    "performance_efficiency_issues": <integer count>,
    "security_issues": <integer count>,
    "key_findings": ["top", "3", "findings"]
}

Code to evaluate:
{code}
""",
        "focus_categories": ["maintainability", "reliability", "performance_efficiency", "security"]
    }
    # Add your custom prompts below this line, e.g.:
    # {
    #     "id": "security_focus",
    #     "name": "Security-Only Evaluation",
    #     "description": "Evaluates only security weaknesses per ISO 5055",
    #     "content": "Evaluate only security flaws in this code: {code}\nReturn JSON with security_issues count",
    #     "focus_categories": ["security"]
    # }
]
```

**How to Add Prompts**:
1. Copy the commented example template
2. Uncomment and fill in: id, name, description, content, focus_categories
3. Ensure content includes `{code}` placeholder where the input code should be inserted
4. LLM must return valid JSON with fields: maintainability_issues, reliability_issues, performance_efficiency_issues, security_issues, key_findings
5. Save file - no restart needed, prompts loaded dynamically

---

### 3. ollama_utils.py
**Purpose**: All Ollama integration - check connection, fetch models, send prompts, parse responses.

**Critical Requirements**:
- Only use models from `ollama list` output
- Try REST API first, fall back to subprocess if unavailable
- Exit with error if no models found or Ollama not running
- 60-second timeout per model request
- Validate JSON response has all required fields

**Content**:
```python
# ollama_utils.py
import requests
import subprocess
import json
import sys

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

def get_available_models():
    """Fetch all local models matching `ollama list` output, with subprocess fallback."""
    models = []
    
    # Method 1: Ollama REST API (preferred)
    try:
        response = requests.get(f"{OLLAMA_API_BASE}/api/tags", timeout=5)
        if response.status_code == 200:
            models = [model["name"] for model in response.json().get("models", [])]
    except Exception:
        pass
    
    # Method 2: Subprocess fallback (matches `ollama list` CLI output)
    if not models:
        print("⚠️ Ollama API unavailable, falling back to `ollama list` subprocess")
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Parse ollama list output (skip header line, extract first column)
                lines = result.stdout.strip().split("\n")
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        model_name = line.split()[0]
                        models.append(model_name)
        except Exception as e:
            print(f"❌ ERROR: Failed to fetch Ollama models: {e}")
            sys.exit(1)
    
    if not models:
        print("❌ ERROR: No Ollama models found. Use `ollama pull <model>` to download models first.")
        sys.exit(1)
    
    print(f"📋 Available Ollama models (matches `ollama list`): {models}")
    return models

def send_prompt_to_model(model_name, prompt_content, timeout=60):
    """
    Send prompt to Ollama model and return raw response.
    Raises TimeoutError if model takes longer than timeout seconds.
    """
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt_content}],
        "stream": False,
        "format": "json"  # Request JSON output directly from Ollama
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

def parse_model_response(response_json):
    """Parse Ollama response to extract ISO 5055 metrics, validate required fields."""
    try:
        # Ollama returns message content in response_json["message"]["content"]
        content = response_json["message"]["content"]
        # If Ollama returned raw JSON string, parse it
        if isinstance(content, str):
            metrics = json.loads(content)
        else:
            metrics = content
        
        # Validate required fields
        required_fields = [
            "maintainability_issues", "reliability_issues",
            "performance_efficiency_issues", "security_issues"
        ]
        for field in required_fields:
            if field not in metrics:
                raise ValueError(f"Missing required field: {field}")
        
        # Ensure key_findings exists
        if "key_findings" not in metrics:
            metrics["key_findings"] = []
        
        return metrics
    except json.JSONDecodeError:
        raise ValueError("Model returned invalid JSON")
    except Exception as e:
        raise ValueError(f"Failed to parse response: {e}")
```

---

### 4. static_analysis.py
**Purpose**: Run static analysis tools and map results to ISO 5055 categories. Must exit with error if any tool is not installed.

**Critical Requirements**:
- Import Radon, Pylint, Bandit at module level
- Check each import and exit with error if missing
- Run Radon: maintainability index, cyclomatic complexity
- Run Pylint: score out of 10
- Run Bandit: high/medium/low vulnerability counts
- Print progress for each tool
- Return metrics dict with all results

**Content**:
```python
# static_analysis.py
import subprocess
import json
import sys

# Exit immediately if any static tool is not installed (per user requirement)
try:
    from radon.raw import analyze
    from radon.complexity import cc_visit, average_complexity
    from radon.metrics import mi_visit
    print("✅ Radon installed")
except ImportError:
    print("❌ ERROR: Radon is not installed. Install with: pip install radon")
    sys.exit(1)

try:
    import pylint
    print("✅ Pylint installed")
except ImportError:
    print("❌ ERROR: Pylint is not installed. Install with: pip install pylint")
    sys.exit(1)

try:
    import bandit
    print("✅ Bandit installed")
except ImportError:
    print("❌ ERROR: Bandit is not installed. Install with: pip install bandit")
    sys.exit(1)

def run_static_analysis(input_file, code_content):
    """
    Run Radon, Pylint, Bandit on input code.
    Returns dict of static metrics mapped to ISO 5055 categories.
    """
    print(f"\n🔍 Running static analysis (Radon, Pylint, Bandit) on {input_file}...")
    metrics = {}
    
    # 1. Radon Metrics (Maintainability + Complexity)
    try:
        raw_metrics = analyze(code_content)
        sloc = raw_metrics.sloc
        cc_blocks = cc_visit(code_content)
        avg_cc = average_complexity(cc_blocks)
        mi = mi_visit(code_content, multi=True)  # Count multi-line strings as comments
        
        metrics["maintainability_index"] = round(mi, 2)
        metrics["cyclomatic_complexity"] = round(avg_cc, 2)
        print(f"   Radon: Maintainability Index = {mi:.2f}, Avg Cyclomatic Complexity = {avg_cc:.2f}")
    except Exception as e:
        print(f"   ⚠️ Radon analysis failed: {e}")
        metrics["maintainability_index"] = None
        metrics["cyclomatic_complexity"] = None
    
    # 2. Pylint (Reliability + Coding Standards)
    try:
        pylint_cmd = ["pylint", input_file]
        result = subprocess.run(pylint_cmd, capture_output=True, text=True, timeout=30)
        pylint_score = None
        for line in result.stdout.split("\n"):
            if "Your code has been rated at" in line:
                score_str = line.split(" ")[6].split("/")[0]
                pylint_score = float(score_str)
                break
        metrics["pylint_score"] = pylint_score
        if pylint_score is not None:
            print(f"   Pylint: Score = {pylint_score}/10")
        else:
            print("   Pylint: No score generated")
    except Exception as e:
        print(f"   ⚠️ Pylint analysis failed: {e}")
        metrics["pylint_score"] = None
    
    # 3. Bandit (Security)
    try:
        bandit_cmd = ["bandit", "-f", "json", input_file]
        result = subprocess.run(bandit_cmd, capture_output=True, text=True, timeout=30)
        bandit_json = json.loads(result.stdout) if result.stdout else {"results": []}
        bandit_high = sum(1 for res in bandit_json.get("results", []) if res.get("issue_severity") == "HIGH")
        bandit_medium = sum(1 for res in bandit_json.get("results", []) if res.get("issue_severity") == "MEDIUM")
        bandit_low = sum(1 for res in bandit_json.get("results", []) if res.get("issue_severity") == "LOW")
        
        metrics["bandit_high"] = bandit_high
        metrics["bandit_medium"] = bandit_medium
        metrics["bandit_low"] = bandit_low
        print(f"   Bandit: High = {bandit_high}, Medium = {bandit_medium}, Low = {bandit_low} vulnerabilities")
    except Exception as e:
        print(f"   ⚠️ Bandit analysis failed: {e}")
        metrics["bandit_high"] = None
        metrics["bandit_medium"] = None
        metrics["bandit_low"] = None
    
    return metrics
```

---

### 5. csv_writer.py
**Purpose**: Save all results to timestamped CSV file using pandas.

**Content**:
```python
# csv_writer.py
import pandas as pd
import datetime
import os

def write_results_to_csv(results, output_dir="."):
    """
    Save evaluation results to timestamped CSV.
    Returns absolute path to saved file.
    """
    if not results:
        print("⚠️ No results to save")
        return None
    
    df = pd.DataFrame(results)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"iso5055_evaluation_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)
    
    df.to_csv(filepath, index=False)
    return os.path.abspath(filepath)
```

---

### 6. main.py
**Purpose**: Entry point that orchestrates entire workflow. Must print progress at every step.

**Critical Requirements**:
- Parse CLI argument for input Python file
- Validate input file exists and is .py extension
- Check Ollama running, fetch all models
- Run static analysis once per file
- Load all prompts from prompts.py
- Loop through all models × all prompts
- Print progress for each evaluation
- Handle errors gracefully (timeout, invalid JSON)
- Save results to timestamped CSV
- Print completion summary

**Content**:
```python
# main.py
import argparse
import datetime
import sys
import os

# Import project modules
import ollama_utils
import static_analysis
import prompts
import csv_writer

def main():
    # Print startup header
    print("=" * 60)
    print("=== Ollama ISO/IEC 5055 Model Comparison Evaluator ===")
    print(f"Timestamp: {datetime.datetime.now().isoformat()}")
    print("=" * 60)
    
    # 1. CLI Argument Parsing
    parser = argparse.ArgumentParser(description="Evaluate Python code against ISO/IEC 5055:2021 using all local Ollama models.")
    parser.add_argument("input_file", help="Path to single Python file to evaluate")
    args = parser.parse_args()
    
    input_file = args.input_file
    if not os.path.exists(input_file):
        print(f"❌ ERROR: Input file {input_file} does not exist")
        sys.exit(1)
    if not input_file.endswith(".py"):
        print(f"❌ ERROR: Input file must be a Python file (.py)")
        sys.exit(1)
    
    print(f"📂 Input file: {input_file}")
    
    # 2. Check Ollama + Fetch Models
    ollama_utils.check_ollama_running()
    available_models = ollama_utils.get_available_models()
    print(f"🚀 Evaluating {len(available_models)} models: {available_models}")
    
    # 3. Read Input Code
    with open(input_file, "r", encoding="utf-8") as f:
        code_content = f.read()
    
    # 4. Run Static Analysis (Once per file)
    static_metrics = static_analysis.run_static_analysis(input_file, code_content)
    
    # 5. Load Prompts
    prompts_list = prompts.ISO5055_PROMPTS
    print(f"\n📝 Loaded {len(prompts_list)} evaluation prompts: {[p['name'] for p in prompts_list]}")
    
    # 6. Evaluate All Models x All Prompts
    results = []
    total_evaluations = len(available_models) * len(prompts_list)
    eval_count = 0
    
    for model_idx, model_name in enumerate(available_models, 1):
        print(f"\n--- Evaluating model {model_idx}/{len(available_models)}: {model_name} ---")
        
        for prompt_idx, prompt in enumerate(prompts_list, 1):
            eval_count += 1
            print(f"   [{eval_count}/{total_evaluations}] Running prompt: {prompt['name']}")
            
            # Prepare prompt with code inserted
            try:
                prompt_with_code = prompt["content"].format(code=code_content)
            except KeyError as e:
                print(f"   ❌ ERROR: Prompt {prompt['id']} missing {e} placeholder, skipping")
                continue
            
            # Send to Ollama model
            llm_metrics = None
            status = "pending"
            try:
                response = ollama_utils.send_prompt_to_model(model_name, prompt_with_code)
                llm_metrics = ollama_utils.parse_model_response(response)
                status = "success"
                print(f"   ✅ Results: Maintainability={llm_metrics['maintainability_issues']}, Reliability={llm_metrics['reliability_issues']}, Performance={llm_metrics['performance_efficiency_issues']}, Security={llm_metrics['security_issues']}")
            except TimeoutError as e:
                status = "timeout"
                print(f"   ⚠️ Timeout: {e}")
            except ValueError as e:
                status = "invalid_json"
                print(f"   ⚠️ Invalid response: {e}")
            except Exception as e:
                status = "error"
                print(f"   ⚠️ Error: {e}")
            
            # Append result row
            result_row = {
                "timestamp": datetime.datetime.now().isoformat(),
                "input_file": input_file,
                "model_name": model_name,
                "prompt_id": prompt["id"],
                "prompt_name": prompt["name"],
                "static_maintainability_index": static_metrics.get("maintainability_index"),
                "static_cyclomatic_complexity": static_metrics.get("cyclomatic_complexity"),
                "pylint_score": static_metrics.get("pylint_score"),
                "bandit_high_vulns": static_metrics.get("bandit_high"),
                "bandit_medium_vulns": static_metrics.get("bandit_medium"),
                "bandit_low_vulns": static_metrics.get("bandit_low"),
                "llm_maintainability_issues": llm_metrics["maintainability_issues"] if llm_metrics else None,
                "llm_reliability_issues": llm_metrics["reliability_issues"] if llm_metrics else None,
                "llm_performance_issues": llm_metrics["performance_efficiency_issues"] if llm_metrics else None,
                "llm_security_issues": llm_metrics["security_issues"] if llm_metrics else None,
                "key_findings": str(llm_metrics["key_findings"]) if llm_metrics else None,
                "evaluation_status": status
            }
            results.append(result_row)
    
    # 7. Save Results to CSV
    print("\n" + "=" * 60)
    csv_path = csv_writer.write_results_to_csv(results)
    if csv_path:
        print(f"✅ Results saved to: {csv_path}")
    else:
        print("❌ No results saved")
    
    print("=" * 60)
    print("=== Evaluation Complete ===")
    print("=" * 60)

if __name__ == "__main__":
    main()
```

---

## Installation Instructions

### Prerequisites
1. **Python 3.8+** installed
2. **Ollama** installed and running locally
3. At least one Ollama model pulled (e.g., `ollama pull codellama`)

### Setup Steps
```bash
# 1. Navigate to project directory
cd C:\Users\Renaud\Desktop\Onderzoek\

# 2. Install all dependencies
pip install -r requirements.txt

# 3. Verify Ollama is running
ollama list

# 4. Run the evaluator on a Python file
python main.py path/to/your/test_script.py
```

---

## Usage

### Basic Usage
```bash
python main.py my_code.py
```

This will:
1. Check Ollama is running and fetch all available models
2. Run static analysis (Radon/Pylint/Bandit) once
3. Evaluate the code with every Ollama model using every prompt in prompts.py
4. Save results to `iso5055_evaluation_YYYYMMDD_HHMMSS.csv`

### CSV Output Format
The CSV contains one row per (model, prompt) combination with columns:
- `timestamp`: When evaluation ran
- `input_file`: Path to evaluated Python file
- `model_name`: Ollama model used
- `prompt_id`, `prompt_name`: Which prompt was used
- `static_maintainability_index`: Radon MI score
- `static_cyclomatic_complexity`: Average CC
- `pylint_score`: Pylint rating (0-10)
- `bandit_high_vulns`, `bandit_medium_vulns`, `bandit_low_vulns`: Security findings
- `llm_maintainability_issues`: LLM-reported maintainability count
- `llm_reliability_issues`: LLM-reported reliability count
- `llm_performance_issues`: LLM-reported performance count
- `llm_security_issues`: LLM-reported security count
- `key_findings`: Top findings from LLM
- `evaluation_status`: success/timeout/invalid_json/error

---

## Adding Custom Prompts

### Step-by-Step
1. Open `prompts.py`
2. Add new dictionary to `ISO5055_PROMPTS` list:
```python
{
    "id": "unique_identifier",
    "name": "Human Readable Name",
    "description": "What this prompt evaluates",
    "content": """Your prompt text here. Must include {code} placeholder.
    
    Instructions for LLM...
    
    Return JSON format:
    {
        "maintainability_issues": <int>,
        "reliability_issues": <int>,
        "performance_efficiency_issues": <int>,
        "security_issues": <int>,
        "key_findings": ["finding1", "finding2"]
    }
    
    Code to evaluate:
    {code}
    """,
    "focus_categories": ["maintainability", "security"]  # Which ISO categories
}
```
3. Save file - prompts loaded dynamically on next run

### Prompt Requirements
- Must include `{code}` placeholder for code insertion
- Must instruct LLM to return valid JSON
- Must include all 4 required integer fields
- No copyrighted content (use public domain ISO 5055 summaries only)

---

## Error Handling

### Tool Exits With Error If:
- Ollama is not running
- No Ollama models are available (`ollama list` empty)
- Radon, Pylint, or Bandit is not installed
- Input file does not exist or is not .py file

### Warnings (Tool Continues):
- Individual model timeout (skips that model)
- Invalid JSON from model (skips that evaluation)
- Static analysis tool fails on specific file (returns None for those metrics)

---

## ISO 5055:2021 Category Mapping

| ISO 5055 Category | Static Tools | LLM Focus |
|-------------------|--------------|-----------|
| **Maintainability** | Radon MI, complexity, Pylint refactoring | Code structure, documentation, complexity |
| **Reliability** | Pylint errors/warnings, Radon bugs metric | Error handling, fault tolerance, edge cases |
| **Performance Efficiency** | Radon raw metrics (LOC, SLOC) | Algorithmic complexity, resource usage |
| **Security** | Bandit vulnerabilities | Injection flaws, input validation, CWEs |

---

## Testing the Implementation

Create a test Python file (`test_input.py`):
```python
# Test file with intentional issues
def bad_function(x):
    if x > 0:
        if x > 10:
            if x > 100:
                return "big"
            return "medium"
        return "small"
    return "negative"

# Hardcoded password (security issue)
password = "secret123"
```

Run the tool:
```bash
python main.py test_input.py
```

Expected output should show:
- High cyclomatic complexity
- Security warning about hardcoded password
- LLM-reported issues across all 4 categories

---

## Notes for Implementation

1. **No External APIs**: Tool must never use OpenAI, Anthropic, or other external LLM APIs
2. **Local Only**: Everything runs on user's machine using local Ollama
3. **Public Domain**: Use only public domain ISO 5055 summaries (official standard is copyrighted)
4. **Mandatory Output**: Print statements must appear exactly as specified for user visibility
5. **Single Directory**: All Python files in same directory, no subdirectories or packages
6. **CSV Only**: Results must be CSV format, no JSON or other formats
7. **All Models**: Must evaluate every model returned by `ollama list`, no model selection
8. **All Prompts**: Must run every prompt in prompts.py, no prompt selection

---

**End of Specification**
