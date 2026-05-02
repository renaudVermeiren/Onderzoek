# LLM Prompt Runner

Dit project voert prompts uit op lokale LLM modellen via Ollama. De prompts bevatten programmeervragen voor data-analyse en ETL-processen, en de gegenereerde code wordt opgeslagen voor latere evaluatie.

## Structuur

```
.
├── config.py              # Configuratie (modellen, directories, timeouts)
├── main.py               # Hoofdscript - voert alle prompts uit
├── prompts/              # Folder met prompt JSON files
│   ├── etl_basic.json
│   ├── data_analysis_stats.json
│   ├── etl_api_extraction.json
│   ├── data_cleaning_pipeline.json
│   └── sql_etl.json
├── prompts/loader.py     # Prompt loading functionaliteit
├── core/
│   ├── __init__.py
│   └── ollama_client.py  # Ollama API client
├── utils/
│   └── __init__.py
└── generated_code/       # Output folder (wordt automatisch aangemaakt)
    ├── llama3/
│   ├── etl_basic_20250115_143022.py
│   └── ...
├── codellama/
│   └── ...
└── mistral/
    └── ...
```

## Configuratie

Bewerk `config.py` om te configureren:

```python
# Modellen om te testen (moeten geïnstalleerd zijn in Ollama)
MODELS_TO_TEST = [
    "llama3",
    "codellama", 
    "mistral"
]

# Output directory voor gegenereerde code
OUTPUT_DIR = "generated_code"

# Timeout voor LLM requests (seconden)
TIMEOUT_SECONDS = 120
```

## Prompts Toevoegen

Maak een nieuw JSON bestand in de `prompts/` folder met dit formaat:

```json
{
  "id": "unieke_id",
  "name": "Menselijke Naam",
  "description": "Beschrijving van de prompt",
  "prompt": "De volledige prompt tekst die naar het LLM wordt gestuurd...",
  "category": "etl|data_analysis|data_cleaning|etc",
  "expected_output_type": "python_script"
}
```

## Gebruik

1. Zorg dat Ollama draait lokaal
2. Installeer benodigde modellen: `ollama pull llama3` etc.
3. Run het script:

```bash
python main.py
```

Het script zal:
- Alle prompts laden uit de `prompts/` folder
- Verbinden met je lokale Ollama instance
- Elke prompt uitvoeren op elk geconfigureerd model
- Gegenereerde code opslaan in `generated_code/<model_naam>/`
- Metadata opslaan over de run

## Output

Voor elk prompt/model combinatie wordt een Python bestand aangemaakt:
```
generated_code/
├── llama3/
│   ├── etl_basic_20250115_143022.py
│   ├── data_analysis_1_20250115_143045.py
│   └── ...
├── codellama/
│   └── ...
└── mistral/
    └── ...
```

Ook wordt een metadata JSON bestand aangemaakt met informatie over de run.

## Vereisten

- Python 3.8+
- Ollama geïnstalleerd en draaiend
- Modellen geïnstalleerd in Ollama
- Python packages: `requests`

Installatie:
```bash
pip install requests
```

## Huidige Prompts

- **etl_basic**: Basis ETL transformatie met CSV
- **data_analysis_stats**: Statistische analyse op synthetische data
- **etl_api_extraction**: Data ophalen via API en verwerken
- **data_cleaning_pipeline**: Data cleaning op vervuilde dataset
- **sql_etl**: SQL queries en DataFrame verwerking
