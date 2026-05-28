# LLM Code Generation Evaluation Results

## Overview

This evaluation compares **6 large language models** on their ability to generate Python code for **35 ETL (Extract, Transform, Load) tasks**. Each model generated **3 samples** (with different random seeds) for each task, resulting in **630 total code evaluations**.

## Evaluation Methodology

### Models Evaluated
- **deepseek-coder-v2:latest** (Red)
- **gemma4:latest** (Blue)
- **llama3:latest** (Green)
- **mistral:latest** (Orange)
- **phi4-mini:latest** (Teal)
- **qwen2.5-coder:latest** (Purple)

### Evaluation Criteria
Each generated script was evaluated on 7 dimensions:

1. **Syntax**: Code must be valid Python (AST parseable)
2. **Style**: Code style quality (PEP 8 compliance via ruff)
3. **Security**: Security issues check (via bandit)
4. **Execution**: Code must run without errors in the task context
5. **Performance**: CPU and memory efficiency during execution
6. **Radon**: Code maintainability index (cyclomatic complexity, Halstead metrics)
7. **Functional**: Task-specific functional tests (test.py)

### Evaluation Setup
- **35 ETL tasks** covering: Data Cleaning, Data Transformation, Joins & Aggregation, Performance Optimization, and Data Operations
- **3 samples per task** (with different random seeds for diversity)
- **Execution environment**: Python scripts run in isolated task directories with input CSV files
- **Timeout**: 30 seconds per execution
- **Metrics**: Pass/fail per evaluator + quality scores (0.0 to 1.0)

---

## Graph Descriptions

### 1. Model Performance Comparison by Evaluator
**File**: `01_evaluator_comparison.png`

- **Type**: Grouped bar chart
- **Content**: Mean pass rate per evaluator across all 35 tasks
- **X-axis**: Evaluators (Syntax, Style, Security, Execution, Performance, Radon, Functional)
- **Y-axis**: Mean Pass Rate (%)
- **Colors**: Each model has a consistent color
- **Setup**: Pass rate calculated as percentage of samples (out of 105 total) that passed each evaluator
- **Key insight**: Shows which models excel at specific evaluation dimensions

### 2. Average Task Performance by Category
**File**: `02_task_performance.png`

- **Type**: Grouped bar chart
- **Content**: Average quality score per task category (Data Cleaning, Data Operations, Data Transformation, Joins & Aggregation, Performance Optimization)
- **X-axis**: Task categories with task count
- **Y-axis**: Average Quality Score (%)
- **Setup**: Mean of all evaluator scores (excluding Functional) per category
- **Key insight**: Shows model performance across different types of ETL operations

### 3. Maintainability Index
**File**: `03_maintainability.png`

- **Type**: Bar chart with reference lines
- **Content**: Mean maintainability index per model (0-100 scale)
- **Reference lines**: 
  - Excellent (≥80): Green dashed line
  - Good (≥60): Orange dashed line
  - Fair (≥40): Red dashed line
- **Setup**: Radon maintainability index averaged across all tasks
- **Key insight**: All models score excellent (>95), indicating clean, readable code

### 4. Lines of Code Distribution
**File**: `04_lines_of_code.png`

- **Type**: Boxplot
- **Content**: Lines of code distribution per model
- **Elements**: 
  - Red line: Mean
  - Box: Quartiles (25th-75th percentile)
  - Whiskers: Min/max range
- **Setup**: Lines of code counted per generated script
- **Key insight**: Shows code verbosity; lower is often more concise

### 5. Execution Time Distribution
**File**: `05_execution_times.png`

- **Type**: Boxplot
- **Content**: Execution time distribution per model
- **Elements**: 
  - Red line: Mean execution time
  - Box: Quartiles
  - Whiskers: Min/max range
- **Setup**: Execution time in seconds measured across all tasks
- **Key insight**: Shows runtime efficiency; lower is generally better



### 7. Model Performance Ranking
**File**: `07_model_ranking.png`

- **Type**: Horizontal bar chart
- **Content**: Overall ranking by average quality score across all evaluators
- **Y-axis**: Models sorted by performance (best at top)
- **X-axis**: Average Quality Score (%)
- **Setup**: Mean of all evaluator scores (excluding Functional) across all tasks
- **Key insight**: Overall leaderboard of model performance

### 8. Sample Consistency
**File**: `08_sample_consistency.png`

- **Type**: Grouped bar chart with pass fractions
- **Content**: Consistency of passing across 3 samples per evaluator
- **Labels**: Pass fractions (e.g., 2/3 = 2 out of 3 samples passed)
- **Setup**: Pass rate calculated per evaluator, showing how consistent each model is
- **Key insight**: Lower variance = more reliable code generation

### 9. Generation Speed
**File**: `09_generation_speed.png`

- **Type**: Bar chart
- **Content**: Code generation speed per model
- **Y-axis**: Tokens per second
- **Labels**: Speed value + token count
- **Setup**: Derived from timing data during code generation
- **Key insight**: Shows which models generate code faster

---

## Performance Analysis & Conclusions

### Overall Rankings

Based on the evaluation, the models ranked by overall quality score (average of all evaluators):

1. **llama3:latest** - 96.1% average quality score
2. **deepseek-coder-v2:latest** - 95.7% average quality score
3. **qwen2.5-coder:latest** - 95.6% average quality score
4. **mistral:latest** - 94.6% average quality score
5. **phi4-mini:latest** - 89.0% average quality score
6. **gemma4:latest** - 86.9% average quality score

---

### Detailed Model Analysis

#### **qwen2.5-coder:latest** (Purple)
- **Strengths**: 
  - **Perfect style compliance** (100% pass rate) - only model with 100% style score
  - Excellent syntax (100%), security (100%), and Radon (100%)
  - Strong execution performance (81.9%)
- **Weaknesses**: 
  - Functional pass rate at 57.1% (middle of the pack)
- **Overall**: Top performer for code quality and style. Generates the cleanest, most PEP-8 compliant code.

#### **deepseek-coder-v2:latest** (Red)
- **Strengths**:
  - **Highest overall quality score** (0.903 average)
  - Perfect syntax (100%), security (100%), and Radon (100%)
  - Strong execution (82.9%) and performance (81.9%)
  - **Functional pass rate**: 57.1% (tied for highest)
- **Weaknesses**:
  - Style compliance at 78.1% (below Qwen and Llama)
- **Overall**: Strong all-rounder with excellent execution and functional correctness. Best balance of quality and functionality.

#### **gemma4:latest** (Blue)
- **Strengths**:
  - Good execution performance (82.9%)
  - Perfect security (100%)
  - **Highest functional pass rate**: 58.1% (slightly above others)
- **Weaknesses**:
  - **Lowest average quality score** (0.865)
  - **Poor style compliance** (54.3%) - lowest among all models
  - Lower syntax (some failures) and Radon scores
- **Overall**: Prioritizes functional correctness over code style. Generates working code but less clean/PEP-8 compliant.

#### **llama3:latest** (Green)
- **Strengths**:
  - **Highest overall ranking** (96.1%)
  - Good style compliance (81.9%)
  - Perfect security (100%)
- **Weaknesses**:
  - **Lower execution pass rate** (62.9%)
  - **Lower functional pass rate** (41.0%) - significant gap
  - Moderate performance scores
- **Overall**: Strong on code quality metrics but struggles with execution and functional correctness. May generate syntactically correct but semantically problematic code.

#### **phi4-mini:latest** (Teal)
- **Strengths**:
  - Good style compliance (86.7%)
  - Perfect security (100%)
  - Moderate execution (68.6%)
- **Weaknesses**:
  - **Lower functional pass rate** (36.2%)
  - Some syntax failures (95.2%)
  - Lower average quality score (0.854)
- **Overall**: Middle performer with decent style but struggles with functional correctness.

#### **mistral:latest** (Orange)
- **Strengths**:
  - Good overall quality score (94.6%)
  - Decent style compliance (76.2%)
  - Perfect security (100%)
- **Weaknesses**:
  - **Lowest functional pass rate** (29.5%)
  - **Lowest execution pass rate** (51.4%)
  - Some syntax issues (98.1%)
- **Overall**: Generates aesthetically pleasing code but struggles with functional correctness. Large gap between code quality and actual task completion.

---

## Key Findings

### 1. Code Quality vs. Functional Correctness Gap
There is a significant gap between **code quality scores** (Syntax, Style, Radon: 80-100%) and **functional correctness** (30-58%). This suggests that while all models can generate syntactically correct Python, **implementing the correct ETL logic is much harder**. All models struggle with functional tests, indicating the complexity of real-world data processing tasks.

### 2. Style Compliance Variation
- **qwen2.5-coder** is the only model with perfect style compliance (100%)
- **gemma4** has notably poor style (54.3%) despite functional success
- This suggests some models prioritize functionality over code style

### 3. Execution Environment Matters
After fixing the execution evaluator bug (proper task directory detection), all models showed improved execution scores. This confirms that **context-aware execution** (running in the correct directory with input files) is crucial for accurate evaluation.

### 4. Security is Universal
All models scored **100% on security** (Bandit analysis), with zero high or medium severity issues. This is expected as ETL tasks typically don't involve security-sensitive operations (no SQL injection, command execution, etc.).

### 5. Maintainability is Excellent
All models scored **>95% on maintainability** (Radon metrics), indicating the generated code is well-structured, readable, and maintainable regardless of the model.

---

## Recommendations

### For Best Overall Performance
**qwen2.5-coder** or **deepseek-coder-v2** are the top choices. Both offer excellent code quality with strong functional correctness.

### For Style-First Development
**qwen2.5-coder** is the clear winner with perfect PEP-8 compliance. Choose this if code readability and maintainability are paramount.

### For Functional Correctness
**gemma4** achieved the highest functional pass rate (58.1%) but with a style trade-off. Consider this if you need working code quickly and can refactor later.

### For Avoiding
**mistral** shows the largest gap between code quality and functional correctness. While the code looks good, it often fails to implement the required logic correctly.

---

## Methodology Notes

- **Evaluation date**: 2026-05-28
- **Total evaluations**: 630 (6 models × 35 tasks × 3 samples)
- **Evaluation framework**: Custom Python evaluation suite with 7 evaluators
- **Known limitations**: 
  - Some models generated markdown code blocks (now fixed)
  - Execution environment requires proper task directory context
  - Performance metrics are relative to system load

---

*Generated from evaluation results: results/evaluation_20260528_160118*
