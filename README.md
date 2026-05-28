# LLM Prompt Runner & Code Evaluator

Dit project genereert Python code door prompts uit te voeren op lokale LLM (Large Language Model) modellen via Ollama, en evalueert de gegenereerde code.

## Overzicht

Dit systeem:
1. **Genereert code** door prompts uit te voeren op meerdere LLM modellen (via Ollama)
2. **Slaat code op** in een gestructureerde folder hiërarchie
3. **Evalueert code** op zes kwaliteitsaspecten:
   - **Syntax** - Controleert of de code geldige Python syntax heeft
   - **Style** - Detecteert semantische fouten en stijlproblemen met Ruff
   - **Security** - Detecteert beveiligingsproblemen met Bandit
   - **Execution** - Controleert of de code succesvol uitgevoerd kan worden
   - **Performance** - Meet CPU en memory gebruik tijdens executie met psutil
   - **Maintainability** - Analyseert complexiteit en onderhoudbaarheid met Radon

Het systeem is gebaseerd op het onderzoek van Krebs & Mazumdar (2025) dat LLM-gegenereerde code evalueert volgens vier ISO 5055 categorieën.

## Vereisten

- **Python 3.8+** - Programmeertaal
- **Ollama** - Tool voor het lokaal draaien van LLM modellen
- **Sufficient disk space** - Voor modellen (~4-8GB per model) en gegenereerde code

## Installatie

### Stap 1: Ollama Installeren

**Windows:**
1. Download Ollama van [ollama.com/download](https://ollama.com/download/windows)
2. Voer het installatiebestand uit
3. Ollama draait automatisch als achtergrond service

**macOS:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Stap 2: Python Omgeving Opzetten

```bash
# Clone of navigeer naar project directory
cd C:\Users\Renaud\Desktop\Onderzoek

# Maak virtual environment aan
python -m venv .venv

# Activeer virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Installeer benodigde packages
pip install -r requirements.txt
```

### Stap 3: LLM Modellen Downloaden

Download de modellen die je wilt testen:

```bash
# Voorbeeld modellen (kies wat je nodig hebt)
ollama pull llama3
ollama pull codellama
ollama pull mistral
ollama pull deepseek-coder-v2:latest

# Controleer welke modellen je hebt
ollama list
```

**Let op:** Modellen zijn 4-8GB per stuk. Zorg voor voldoende disk space en een goede internetverbinding.

## Project Structuur

```
.
├── config.py                    # Configuratie (modellen, directories, timeouts)
├── main.py                      # Hoofdscript - voert alle prompts uit
├── evaluate.py                  # Evaluatie script - test gegenereerde code
├── analyze_results.py           # Genereert grafieken en analyses
├── evaluation_results.md        # Automatische samenvatting van resultaten
├── prompts/                     # Folder met prompt JSON files
│   ├── etl_basic.json          # Basis ETL transformatie
│   ├── data_analysis_stats.json # Statistische analyse
│   ├── etl_api_extraction.json  # API data extractie
│   ├── data_cleaning_pipeline.json # Data cleaning
│   └── sql_etl.json            # SQL queries
├── prompts/loader.py            # Prompt loading functionaliteit
├── core/                        # Kern functionaliteit
│   ├── ollama_client.py        # Ollama API client
│   ├── code_extractor.py       # Code extractie uit LLM responses
│   └── evaluators/             # Evaluator modules
│       ├── syntax_evaluator.py      # Syntax checking (AST)
│       ├── style_evaluator.py       # Style & semantics checking (Ruff)
│       ├── security_evaluator.py    # Security analysis (Bandit)
│       ├── execution_evaluator.py   # Code execution testing
│       ├── performance_evaluator.py # Performance analysis (psutil)
│       ├── functional_test_evaluator.py # Functional testing
│       └── radon_evaluator.py       # Complexity & maintainability (Radon)
├── generated_code/              # Output: Gegenereerde Python code
│   └── <model_name>/
│       └── <task_id>/
│           ├── generated_script_v1.py
│           ├── generated_script_v2.py
│           ├── generated_script_v3.py
│           └── test.py
├── results/                     # Output: Evaluatie resultaten
│   └── evaluation_<timestamp>/
│       ├── overall_results.json
│       ├── <model_name>/
│       │   ├── <task_id>_result.json
│       │   └── model_summary.json
│       └── ...
└── graphs/                      # Output: Visualisaties
    └── evaluation_<timestamp>/
        ├── 01_evaluator_comparison.png
        ├── 02_task_performance.png
        ├── 03_maintainability.png
        ├── 04_lines_of_code.png
        ├── 05_execution_times.png
        ├── 06_security_issues.png
        ├── 07_model_ranking.png
        ├── 08_sample_consistency.png
        └── 09_generation_speed.png
```

## Configuratie

Bewerk `config.py` om het systeem aan te passen aan jouw behoeften:

```python
# config.py

# Modellen om te testen (moeten geïnstalleerd zijn in Ollama)
# Voeg hier de namen toe van de modellen die je wilt gebruiken
MODELS_TO_TEST = [
    "llama3",                    # Meta's Llama 3
    "codellama",                 # Code-specialized Llama
    "mistral",                   # Mistral AI model
    "deepseek-coder-v2:latest"   # DeepSeek Coder v2
]

# Directory waar gegenereerde code wordt opgeslagen
OUTPUT_DIR = "generated_code"

# Directory waar evaluatie resultaten worden opgeslagen
RESULTS_DIR = "results"

# Directory met prompt JSON files
PROMPTS_DIR = "prompts"

# Timeout voor LLM requests (in seconden)
# Verhoog dit als je langere prompts gebruikt
TIMEOUT_SECONDS = 120
```

### Configuratie Tips:

1. **Modellen toevoegen**: Zet de exacte naam zoals `ollama list` deze toont
2. **Directories aanpassen**: Wijzig `OUTPUT_DIR` en `RESULTS_DIR` als je andere locaties wilt
3. **Timeout aanpassen**: Verhoog `TIMEOUT_SECONDS` voor complexere prompts of langzamere modellen
4. **Multi-sample evaluatie**: Stel `NUM_SAMPLES` in `config.py` in om meerdere samples per task te genereren (standaard: 3)

## Gebruik

### Stap 1: Code Genereren

Voer `main.py` uit om prompts op alle geconfigureerde modellen uit te voeren:

```bash
python main.py
```

**Wat er gebeurt:**
1. Verbinding met lokale Ollama instance
2. Laden van alle prompts uit de `prompts/` folder
3. Voor elk model:
   - Voer elke prompt uit **3 keer** (met verschillende random seeds)
   - Sla gegenereerde code op als `generated_script_v1.py`, `v2.py`, `v3.py`
   - Kopieer input bestanden en `test.py` naar de task folder
4. Metadata opslaan over de run (timestamps, tokens/s, seed waarden)

**Output:**
```
generated_code/
├── llama3/
│   ├── task_01/
│   │   ├── generated_script_v1.py
│   │   ├── generated_script_v2.py
│   │   ├── generated_script_v3.py
│   │   └── test.py
│   └── task_02/
│       └── ...
├── codellama/
│   └── ...
└── metadata_20260115_143022.json
```

### Stap 2: Code Evalueren

Voer `evaluate.py` uit om de gegenereerde code te testen:

```bash
python evaluate.py
```

**Wat er gebeurt:**
1. Zoekt alle Python files in `generated_code/`
2. Voert alle geregistreerde evaluatoren uit:
   - **SyntaxEvaluator**: Checkt Python syntax met AST parser
   - **StyleEvaluator**: Detecteert semantische fouten en stijlproblemen met Ruff
   - **SecurityEvaluator**: Analyseert security met Bandit
   - **ExecutionEvaluator**: Controleert of code uitgevoerd kan worden
   - **PerformanceEvaluator**: Meet CPU/memory met psutil
   - **RadonEvaluator**: Analyseert complexiteit en maintainability met Radon
3. Resultaten per evaluator:
   - Slaat JSON resultaten op
   - Genereert CSV samenvattingen
4. Print samenvatting in console

**Output:**
```
results/evaluation_20260502_143530/
├── overall_results.json              # Alle resultaten gecombineerd
├── <model_name>/
│   ├── model_summary.json            # Samenvatting per model
│   └── <task_id>_result.json        # Details per task
└── ...
```

**Resultaten structuur:**
- **overall_results.json**: Bevat alle evaluaties, per model, per task, per sample
- **model_summary.json**: Samenvatting per model (gemiddelde scores, pass rates)
- **<task_id>_result.json**: Details per task met sample-level evaluaties
- **statistics**: Per task worden mean, std dev, pass rate berekend over de 3 samples

## Evaluatoren Uitleg

### 1. Syntax Evaluator
- **Doel**: Controleert of code geldige Python syntax heeft
- **Methode**: Python AST (Abstract Syntax Tree) parser
- **Score**: 1.0 (valid) of 0.0 (invalid)
- **Output**: Syntax errors met regelnummer

### 2. Security Evaluator (Bandit)
- **Doel**: Detecteert beveiligingsproblemen
- **Methode**: Bandit static analysis tool
- **Detecteert**:
  - SQL injection risico's
  - Hard-coded wachtwoorden/sleutels
  - Misbruik van onveilige functies (eval, exec)
  - CWE (Common Weakness Enumeration) violations
- **Score**: Volgens ISO 5055 formule: S = 1/3(SVs + Warnings + Errors)
  - Security Violations (HIGH severity): zwaarst gewogen
  - Warnings (MEDIUM severity): middelmatig gewogen
  - Errors (LOW severity): licht gewogen

### 3. Execution Evaluator
- **Doel**: Controleert of de code succesvol uitgevoerd kan worden
- **Methode**: Voert code uit in subprocess met timeout
- **Belangrijk**: Deze evaluator maakt onderscheid tussen:
  - **"Code kan niet uitgevoerd worden"** - Runtime errors, exceptions
  - **"Code kan wel uitgevoerd worden"** - En kan daarna getest worden op performance
- **Resultaat**: Duidelijke pass/fail indicatie
  - **PASS (score 1.0)**: Code executed successfully (return code 0)
  - **FAIL (score 0.0)**: Code failed to execute
- **Error Details**: Wanneer executie faalt, toont:
  - Type error (runtime_error, timeout, syntax_error)
  - Error message (uit stderr)
  - Return code
  - Timeout status
- **Timeout**: 30 seconden (voorkomt hangen bij oneindige loops)
- **Gebruik**: Draait VOOR PerformanceEvaluator om verwarring te voorkomen:
  - Als ExecutionEvaluator faalt → code heeft runtime errors
  - Als ExecutionEvaluator slaagt maar PerformanceEvaluator laag is → code is traag

### 4. Performance Evaluator (psutil)
- **Doel**: Meet resource gebruik tijdens executie
- **Methode**: psutil library voor real-time monitoring
- **Metingen** (per iteratie, default 3 iteraties):
  - Gemiddeld CPU percentage tijdens executie
  - Peak memory gebruik (MB)
  - Executie tijd (seconden)
- **Score**: Volgens ISO 5055 formule: PE = 1/2(CPU + Memory)
  - Lager CPU/memory gebruik = hogere score
  - Genormaliseerd naar 0-1 range
- **Timeout**: 30 seconden (voorkomt hangen bij oneindige loops)

### 5. Radon Evaluator (Complexity & Maintainability)
- **Doel**: Analyseert code complexiteit en onderhoudbaarheid
- **Methode**: Radon static analysis tool
- **Metrics**:
  - **Cyclomatic Complexity (CC)**: Aantal beslissingspunten in de code
    - CC < 5: Eenvoudig (goed)
    - CC 5-10: Matig
    - CC 10-20: Complex (aandacht nodig)
    - CC > 20: Zeer complex (refactoring aanbevolen)
  - **Maintainability Index (MI)**: Score 0-100 gebaseerd op complexiteit, grootte, documentatie
    - MI > 80: Uitstekend onderhoudbaar
    - MI 60-80: Goed onderhoudbaar
    - MI 40-60: Matig onderhoudbaar
    - MI < 40: Moeilijk onderhoudbaar
  - **Halstead Metrics**: Complexiteit metrics gebaseerd op operands/operators
    - Estimated delivered bugs
    - Volume, difficulty, effort
  - **Raw Metrics**: Basis statistieken
    - Lines of Code (LOC)
    - Source Lines of Code (SLOC)
    - Commentaar regels
    - Blank lines
    - Comments-to-LOC ratio
- **Score**: Gebaseerd op Maintainability Index + Complexiteit
  - MI >= 80: score 1.0 (excellent)
  - MI >= 60: score 0.8 (good)
  - MI >= 40: score 0.6 (fair)
  - MI >= 20: score 0.4 (poor)
  - MI < 20: score 0.2 (very poor)
  - Hoge complexiteit (>10) verlaagt score
- **Installatie**: `pip install radon`

### 6. Functional Test Evaluator
- **Doel**: Controleert of de gegenereerde code de correcte functionele logica implementeert
- **Methode**: Voert task-specifieke `test.py` bestanden uit in een geïsoleerde omgeving
- **Proces**:
  1. Kopieert task folder naar tijdelijke directory
  2. Voert gegenereerde script uit om output bestanden te produceren
  3. Voert `test.py` uit om output te valideren
  4. Controleert of resultaten voldoen aan verwachtingen
- **Resultaat**: Pass/fail op basis van test.py return code
  - **PASS**: Alle assertions geslaagd, output correct
  - **FAIL**: Assertions faalden of script crashed
- **Belangrijk**: Dit is de meest stringent evaluator - controleert of code daadwerkelijk doet wat gevraagd wordt

### 7. Style Evaluator (Ruff)
- **Doel**: Detecteert semantische fouten en stijlproblemen die AST parsing alleen mist
- **Methode**: Ruff linter met E, W, F regels (pycodestyle + Pyflakes)
- **Detecteert**:
  - Ongedefinieerde variabelen en imports (F-rules)
  - Ongebruikte imports en variabelen (F-rules)
  - Syntax-gerelateerde fouten (E9-rules)
  - Stijlproblemen (E-rules, W-rules)
- **Score**: Gebaseerd op aantal fouten vs waarschuwingen
  - Geen fouten/waarschuwingen: score 1.0 (excellent)
  - Alleen waarschuwingen: score verlaagd met 0.05 per waarschuwing
  - Fouten aanwezig: score verlaagd met 0.15 per fout
  - **PASS**: Alleen als er geen semantische fouten (F-rules) zijn
- **Installatie**: `pip install ruff`

## Prompts Beheren

### Bestaande Prompts

- **etl_basic**: CSV inlezen, transformeren, wegschrijven
- **data_analysis_stats**: Synthetische data genereren, statistieken berekenen
- **etl_api_extraction**: REST API data ophalen en verwerken
- **data_cleaning_pipeline**: Vervuilde data opschonen
- **sql_etl**: SQL queries uitvoeren en resultaten verwerken

### Nieuwe Prompt Toevoegen

1. Maak een nieuw JSON bestand in `prompts/`:

```json
{
  "id": "mijn_prompt_id",
  "name": "Mijn Prompt Naam",
  "description": "Korte beschrijving wat de prompt doet",
  "prompt": "Schrijf een Python script dat...\n\n1. Eerste taak\n2. Tweede taak\n\nBELANGRIJK: Geef ALLEEN de Python code terug. Geen markdown formatting, geen ```python blokken, geen uitleg tekst.",
  "category": "etl",
  "expected_output_type": "python_script"
}
```

2. **Vereiste velden**:
   - `id`: Unieke identifier (gebruik underscores, geen spaties)
   - `name`: Menselijke naam voor weergave
   - `prompt`: De volledige instructie naar het LLM
   - `category`: Categorie (etl, data_analysis, data_cleaning, etc.)

3. **Belangrijke prompt instructie**: 
   Eindig de prompt altijd met:
   ```
   BELANGRIJK: Geef ALLEEN de Python code terug. Geen markdown formatting, geen ```python blokken, geen uitleg tekst, geen introductie, geen conclusie. Alleen de ruwe Python code die direct in een .py bestand kan worden opgeslagen.
   ```

4. Run `python main.py` om de nieuwe prompt te gebruiken

## Evaluatoren Uitbreiden

### Nieuwe Evaluator Maken

1. Maak een nieuw bestand in `core/evaluators/`:

```python
# core/evaluators/mijn_evaluator.py
from typing import Dict, Any
from datetime import datetime
from core.evaluators import BaseEvaluator, EvaluationResult


class MijnEvaluator(BaseEvaluator):
    """Mijn eigen evaluator."""
    
    def __init__(self):
        super().__init__("MijnEvaluator")
    
    def evaluate(self, file_path: str, code_content: str, metadata: Dict[str, Any]) -> EvaluationResult:
        """
        Evalueer de code.
        
        Args:
            file_path: Pad naar het bestand
            code_content: De code als string
            metadata: Dict met model_name, prompt_id, etc.
        
        Returns:
            EvaluationResult met resultaten
        """
        # Je evaluatie logica hier
        passed = True  # of False
        score = 1.0    # 0.0 tot 1.0
        details = {
            "metric": "value",
            "count": 42
        }
        error_message = ""  # of error beschrijving
        
        return EvaluationResult(
            file_path=file_path,
            prompt_id=metadata.get("prompt_id", "unknown"),
            model_name=metadata.get("model_name", "unknown"),
            evaluator_name=self.name,
            passed=passed,
            score=score,
            details=details,
            timestamp=datetime.now().isoformat(),
            error_message=error_message
        )
```

2. Voeg toe aan `core/evaluators/__init__.py`:

```python
from core.evaluators.mijn_evaluator import MijnEvaluator

__all__ = [..., 'MijnEvaluator']
```

3. Registreer in `evaluate.py`:

```python
from core.evaluators.mijn_evaluator import MijnEvaluator

runner.register_evaluator(MijnEvaluator())
```

4. Run `python evaluate.py`



## Resultaten Interpreteren

### JSON Resultaten

```json
{
  "file_path": "generated_code/llama3/etl_basic_20250115_143022.py",
  "prompt_id": "etl_basic",
  "model_name": "llama3",
  "evaluator": "SecurityEvaluator",
  "passed": true,
  "score": 0.95,
  "details": {
    "security_violations": 0,
    "warnings": 1,
    "errors": 0,
    "high_severity": 0,
    "medium_severity": 1,
    "low_severity": 0
  },
  "error_message": "",
  "timestamp": "2026-01-15T14:30:22"
}
```

### CSV Samenvatting

Open `summary.csv` in Excel of Google Sheets voor een overzicht van alle resultaten per model, prompt en evaluator.

## Verwijderen van Output

Om gegenereerde code en resultaten te verwijderen:

```bash
# Verwijder gegenereerde code
rm -rf generated_code/*

# Verwijder resultaten
rm -rf results/*

# Of alles tegelijk (let op: niet verwijderen wat je wilt houden!)
rm -rf generated_code/* results/*
```

**Let op**: Deze folders staan in `.gitignore` en worden niet meegecommit naar git.

## Data Analyse

Na evaluatie kun je de resultaten analyseren:

1. **Per model**: Vergelijk welk model de beste code genereert
2. **Per prompt**: Zie welke taken moeilijker zijn voor LLMs
3. **Per evaluator**: Analyseer specifieke kwaliteitsaspecten

Gebruik de CSV bestanden in de results folder voor analyse in Excel, Python pandas, of andere tools.

### Visualization & Analysis

Na de evaluatie kun je automatische grafieken genereren:

```bash
python analyze_results.py [results/evaluation_TIMESTAMP]
```

**Wat er gebeurt:**
1. Laad evaluatie resultaten uit de results folder
2. Genereert 9 vergelijkingsgrafieken:
   - **01_evaluator_comparison.png**: Pass rates per evaluator per model
   - **02_task_performance.png**: Gemiddelde scores per taakcategorie
   - **03_maintainability.png**: Maintainability index per model
   - **04_lines_of_code.png**: Lines of code distributie
   - **05_execution_times.png**: Executie tijd distributie
   - **06_security_issues.png**: Security issues per severity
   - **07_model_ranking.png**: Overall model ranking
   - **08_sample_consistency.png**: Consistentie over 3 samples
   - **09_generation_speed.png**: Generatie snelheid (tokens/s)

**Output**: Grafieken worden opgeslagen in `graphs/evaluation_TIMESTAMP/`

### Resultaten Samenvatting

Een automatisch gegenereerde samenvatting is beschikbaar in `evaluation_results.md` na analyse. Dit bevat:
- Uitleg van alle grafieken
- Gedetailleerde model analyse
- Rankings en conclusies
- Aanbevelingen voor model selectie

## Bekende Bugs & Fixes

### Opgelost: Markdown Code Blokken in Generatie
**Probleem**: Sommige modellen (met name mistral) genereerden markdown code blokken (````python`) en uitleg tekst in de gegenereerde code.

**Fix**: Code extraction logica is bijgewerkt om automatisch:
- Markdown code markers (```python, ```) te verwijderen
- Niet-code tekst ("Hier volgt het Python script...") te verwijderen
- Alleen ruwe Python code op te slaan

**Controle**: Check of de gegenereerde code in `generated_code/` geen markdown of uitleg tekst bevat.

### Opgelost: Execution Evaluator Task Folder Detectie
**Probleem**: Execution en Performance evaluators herkenden task folders niet correct (controleerden alleen op `generated_script.py` in plaats van `generated_script_v1.py` etc.). Hierdoor konden scripts de input CSV bestanden niet vinden.

**Fix**: Bijgewerkt naar `generated_script*.py` patroon herkenning.

**Impact**: Execution scores zijn nu significant hoger en accurater omdat scripts in de juiste context draaien.

### Opgelost: Statistieken Berekening in Evaluator
**Probleem**: `compute_sample_statistics()` in `evaluate.py` zocht naar `sample["quality"]["evaluations"]["Syntax"]` maar de data structuur slaat het op als `sample["quality"]["Syntax"]`.

**Fix**: Statistiek berekening bijgewerkt om correcte data structuur te gebruiken.

**Impact**: Task-level statistieken bevatten nu correcte mean/std/pass rate voor alle evaluatoren.

### Opgelost: Grafiek Visualisatie
**Probleem**: Sommige grafieken toonden incorrecte std dev waarden (>100%) of hadden lege data.

**Fix**: 
- `analyze_results.py` bijgewerkt om sample-level data correct te lezen
- Std dev error bars verwijderd van grafieken 1, 2, 3, 7 (niet betrouwbaar voor pass rates)
- Data structuur consistentie hersteld

## Referenties

- **Onderzoek**: Krebs, R., & Mazumdar, S. (2025). Analyzing LLM-Generated Code According to Four ISO/IEC 5055:2021 Categories. IEEE Access, 13, 202482-202499. https://doi.org/10.1109/ACCESS.2025.3637569

- **ISO/IEC 5055:2021**: Software engineering — Systems and software Quality Requirements and Evaluation (SQuaRE) — Automated source code quality measures

- **Ollama**: https://ollama.com

- **Bandit**: https://bandit.readthedocs.io/

- **psutil**: https://psutil.readthedocs.io/

## Licentie

Dit project is bedoeld voor onderzoeksdoeleinden naar LLM-gegenereerde code kwaliteit.

---

**Veel succes met het evalueren van LLM-gegenereerde code! 🚀**

Voor vragen of problemen, raadpleeg de documentatie of check de console output voor foutmeldingen.
