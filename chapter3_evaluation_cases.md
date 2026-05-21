# Hoofdstuk 3: Evaluatiecasussen en Testmethodologie

## 3.1 Evaluatieaanpak

Dit onderzoek evalueert door LLM's gegenereerde Python-code op basis van **35 concrete prompts** verdeeld over **8 categorieën**. Elke gegenereerde code wordt geautomatiseerd geëvalueerd op **7 kwaliteitsdimensies**, gebaseerd op ISO/IEC 5055:2021.

### 3.1.1 Gebruikte LLM-modellen
- DeepSeek-Coder-V2, Gemma 4, Llama 3, Mistral, Qwen2.5-Coder

### 3.1.2 Evaluatiedimensies
1. **Syntax** — Geldige Python-syntax via AST-parsing
2. **Style** — Semantische correctheid via Ruff (E, W, F regels)
3. **Security** — Beveiligingslekken via Bandit static analysis
4. **Execution** — Succesvolle uitvoering zonder runtime errors
5. **Performance** — CPU- en geheugengebruik via psutil
6. **Radon** — Complexiteit en onderhoudbaarheid (cyclomatic complexity, maintainability index)
7. **Functional** — Correctheid van de output ten opzichte van verwachte resultaten

## 3.2 Categorieën en Aantallen

| Categorie | Aantal | Focus |
|-----------|--------|-------|
| Data Cleaning | 14 | Missing values, duplicaten, mixed formats, null-like waarden, whitespace |
| Data Transformation | 6 | Window functions, pivot tables, type conversion, rename/select |
| Joins & Aggregation | 5 | Inner join, left join, multi-table join, aggregation |
| Performance Optimization | 4 | Large groupby, memory filtering, avoid loops, chunked processing |
| Data Loading | 2 | Concatenate CSVs, JSON flatten |
| Data Validation | 2 | Schema validation, custom validation |
| Data Filtering | 1 | Complex filter met meerdere voorwaarden |
| Time Series | 1 | Time series resampling |

## 3.3 Voorbeeldcasussen per Categorie

### Casus 1: Missing Value Imputation (Data Cleaning)
**Prompt:** "Schrijf een Python script dat een CSV bestand inleest en missing values behandelt. Vul numerieke kolommen met het gemiddelde, categorische kolommen met de modus. Sla op naar output.csv."

**Input:** `input.csv` met kolommen `name`, `age`, `city` (waarbij enkele age- en city-waarden ontbreken).

**Verwachte output:**
- Numerieke kolom `age`: missing values gevuld met gemiddelde (27.5)
- Categorische kolom `city`: missing values gevuld met modus (Brussels)
- Geen null-waarden in `output.csv`

**Geteste criteria:** Syntax, Style, Security, Execution, Functional

---

### Casus 2: Duplicate Removal (Data Cleaning)
**Prompt:** "Schrijf een Python script dat duplicaten verwijdert gebaseerd op combinatie van `user_id` + `order_id`. Behoud de rij met de nieuwste timestamp. Sla op naar output.csv."

**Input:** `input.csv` met 4 rijen (1 duplicaat op basis van user_id + order_id).

**Verwachte output:**
- Exact 3 rijen in output
- Correcte datetime-parsing en -vergelijking

**Geteste criteria:** Syntax, Style, Execution, Functional

---

### Casus 3: Handle Mixed Numeric Formats (Data Cleaning — Edge Case)
**Prompt:** "Schrijf een Python script dat gemixte numerieke formaten opschoont: verwijder $ en , uit price, % uit percentage, °C uit temperature. Converteer naar float."

**Input:** `input.csv` met waarden zoals `$1,250.00`, `50%`, `25°C`.

**Verwachte output:**
- `price`: float zonder $ of komma's
- `percentage`: float 0-100 zonder %
- `temperature`: float zonder °C

**Geteste criteria:** Syntax, Style, Execution, Functional

---

### Casus 4: Handle Null-Like Values (Data Cleaning — Edge Case)
**Prompt:** "Schrijf een Python script dat null-like waarden behandelt: 'N/A', 'null', 'NULL', 'NaN', '-', en lege strings zijn allemaal missing values. Converteer naar NaN."

**Input:** `input.csv` met diverse null-like representaties.

**Verwachte output:**
- Alle null-like waarden geconverteerd naar echte NaN
- Missing ages gevuld met gemiddelde
- Rijen met lege city verwijderd

**Geteste criteria:** Syntax, Style, Execution, Functional

---

### Casus 5: Inner Join Users and Orders (Joins & Aggregation)
**Prompt:** "Schrijf een Python script dat twee CSV bestanden joined: lees users.csv en orders.csv, voer een INNER JOIN uit op user_id. Sla op naar output.csv."

**Input:** `users.csv` (user_id, name, email) en `orders.csv` (order_id, user_id, product, amount).

**Verwachte output:**
- Alleen gebruikers met minstens 1 order
- Kolommen van beide tabellen aanwezig

**Geteste criteria:** Syntax, Style, Execution, Functional

---

### Casus 6: Multi-Table Join (Joins & Aggregation — Complex)
**Prompt:** "Schrijf een Python script dat 3 CSV bestanden joined: LEFT JOIN tussen users en orders, vervolgens INNER JOIN met products. Behoud ALLE gebruikers."

**Input:** `users.csv`, `orders.csv`, `products.csv` met refererende sleutels.

**Verwachte output:**
- Alle gebruikers aanwezig in output (LEFT JOIN)
- Alleen orders met geldige producten (INNER JOIN)
- Gebruikers zonder orders hebben NULL-waarden

**Geteste criteria:** Syntax, Style, Execution, Functional

---

### Casus 7: Window Functions (Data Transformation)
**Prompt:** "Schrijf een Python script dat window functions toepast: bereken per category een running total (cumsum) en rank van amount. Sla op naar output.csv."

**Input:** `sales.csv` met kolommen sales_id, category, amount.

**Verwachte output:**
- Correcte cumulatieve som per category
- Correcte ranking per category

**Geteste criteria:** Syntax, Style, Execution, Functional

---

### Casus 8: Large Dataset GroupBy (Performance)
**Prompt:** "Schrijf een Python script dat een groot dataset (1000+ rijen) efficient verwerkt: groupby per category, som van sales, sorteer aflopend."

**Input:** `large_sales.csv` met 1000+ rijen.

**Verwachte output:**
- Efficiënte groupby zonder memory issues
- Correcte aggregaties en sortering

**Geteste criteria:** Syntax, Style, **Performance**, Execution, Functional

---

### Casus 9: Chunked File Processing (Performance — Geheugen-efficiëntie)
**Prompt:** "Schrijf een Python script dat een groot CSV bestand in chunks verwerkt met pd.read_csv(..., chunksize=...). Filter value > 500 per chunk."

**Input:** `huge_file.csv` met 100+ rijen.

**Verwachte output:**
- Correct gebruik van chunksize parameter
- Iteratie over chunks
- Combineer gefilterde chunks

**Geteste criteria:** Syntax, Style, **Performance** (laag geheugengebruik), Execution, Functional

---

### Casus 10: Read JSON and Flatten (Data Loading)
**Prompt:** "Schrijf een Python script dat geneste JSON data flat maakt. Gebruik pandas json_normalize. Sla op naar flat_data.csv."

**Input:** `nested_data.json` met geneste address-structuur.

**Verwachte output:**
- JSON correct ingelezen
- Geneste structuur geflattened naar platte kolommen

**Geteste criteria:** Syntax, Style, Execution, Functional

---

### Casus 11: Custom Data Validation (Data Validation)
**Prompt:** "Schrijf een Python script dat data valideert met custom regels: email bevat @ en ., amount > 0, status is 'completed' of 'pending'. Splits in valid_orders.csv en invalid_orders.csv."

**Input:** `orders.csv` met 6 rijen (4 valide, 2 invalide).

**Verwachte output:**
- Correcte validatie en splitsing
- `invalid_orders` met kolom `validation_error`

**Geteste criteria:** Syntax, Style, **Security** (geen eval/exec), Execution, Functional

---

### Casus 12: Time Series Resampling (Time Series)
**Prompt:** "Schrijf een Python script dat tijdreeks data resampled naar uurlijkse gemiddelden. Converteer timestamp naar datetime. Sla op naar hourly_avg.csv."

**Input:** `sensor_data.csv` met timestamps en waarden.

**Verwachte output:**
- Correcte datetime-conversie
- Uurlijkse gemiddelden

**Geteste criteria:** Syntax, Style, Execution, Functional

---

### Casus 13: Complex Filter with Multiple Conditions (Data Filtering)
**Prompt:** "Schrijf een Python script dat complexe filtering toepast: age > 25 AND age < 60, city is 'Brussels' OR 'Antwerp', salary > 3000, department is NOT 'HR'."

**Input:** `data.csv` met 5 rijen.

**Verwachte output:**
- Correcte boolean-logica (AND, OR, NOT)
- Correcte rijverwachting en sortering

**Geteste criteria:** Syntax, Style, Execution, Functional

---

### Casus 14: Validate and Clean Data Ranges (Data Validation)
**Prompt:** "Schrijf een Python script dat data ranges valideert: age moet 0-120 zijn, temperature 35.0-42.0. Vervang invalide waarden door mediaan."

**Input:** `input.csv` met out-of-range waarden.

**Verwachte output:**
- Alle waarden binnen geldige ranges
- Correcte mediaan-vervanging

**Geteste criteria:** Syntax, Style, Execution, Functional

## 3.4 Evaluatieprocedure

Voor elke casus doorloopt het systeem:

1. **Prompt → LLM** (via Ollama API)
2. **Code generatie** → opslag in `generated_code/<model>/<task>.py`
3. **Automatische evaluatie** via `evaluate.py`:
   - Syntax (AST parsing)
   - Style (Ruff linter)
   - Security (Bandit)
   - Execution (subprocess)
   - Performance (psutil)
   - Radon (complexiteit)
   - Functional (output-verificatie)
4. **Resultaten** → JSON/CSV in `results/`
5. **Visualisatie** → grafieken in `graphs/`

## 3.5 Samenvatting

De 35 casussen dekken alle data engineering aspecten uit hoofdstuk 2 als concrete benchmarks. Per casus worden zowel functionele correctheid als codekwaliteit (syntax, security, performance, onderhoudbaarheid) getest. Dit levert een representatief beeld op van welk LLM-model de beste code genereert voor realistische data engineering taken.
