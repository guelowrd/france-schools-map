# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working Principles

### 1. Plan before implementation
Before writing or modifying non-trivial code, propose a short plan or architecture first. Do not jump straight into implementation. If requirements are vague, ask clarifying questions before proceeding.

### 2. Be specific, not creative
Optimize for correctness and alignment with the request, not creativity. Do not add abstractions, files, patterns, or flexibility unless explicitly asked. Prefer the simplest solution that satisfies the requirements.

### 3. Treat this file as source-of-truth memory
Follow the conventions, constraints, and workflows defined in this file over general best practices. If the same correction is made twice, suggest adding it here.

## Project Overview

Interactive map of schools in France's Pays de la Loire region with education quality indicators (IPS, exam results, enrollment) and political context (mayors, election results). Data sourced from French government open data portals (data.education.gouv.fr, data.gouv.fr).

## Build & Test Commands

### Data Pipeline (run in order)
```bash
cd scraper

# 1. Download education data (~2 min)
python3 download_data.py

# 2. Download enrollment data (~1 min)
python3 download_enrollment_data.py

# 3. Download language offerings (~30 sec)
python3 download_language_data.py

# 4. [OPTIONAL] Download political data (~10-15 min)
python3 download_political_data.py

# 5. Merge all datasets into schools.json
python3 merge_datasets.py

# 6. Copy to frontend (if political data downloaded)
cp ../data/political_cache/political_data.json ../frontend/data/
```

### Testing
```bash
# Run all tests (34 tests: 24 unit + 10 integration)
python3 tests/run_all_tests.py

# Run specific test suites
python3 tests/test_download_political_data.py  # 24 unit tests
python3 tests/test_integration.py              # 10 integration tests
python3 tests/test_data_validation.py          # Data integrity tests

# Frontend tests
cd tests && ./run_tests.sh
```

### Development Server
```bash
cd frontend
python3 -m http.server 8000
# Visit http://localhost:8000
```

## Architecture

### Data Flow

```
Government APIs → scrapers → data/*.json → merge_datasets.py → schools.json
                                                                      ↓
                                                           frontend/data/schools.json
                                                                      ↓
                                                            Leaflet map (app.js)
```

**Key insight**: All school data merges on **UAI code** (unique school identifier). Political data joins in frontend via **INSEE commune code**.

### Core Components

#### 1. Scraper Pipeline (`scraper/`)

**Four independent downloaders**:
- `download_data.py` - School directory + IPS + exam results (uses region filters)
- `download_enrollment_data.py` - Student counts per school (department filters)
- `download_language_data.py` - Language offerings for secondary schools
- `download_political_data.py` - Mayors + election results (department filters)

**Merger**:
- `merge_datasets.py` - Joins all sources on UAI code, outputs `schools.json`

**Critical**: Each scraper is idempotent (re-running overwrites cache files safely).

#### 2. Political Data System (`scraper/download_political_data.py`)

**Five-stage pipeline**:
1. `build_insee_mapping()` - Postal code → INSEE code via geo.api.gouv.fr
2. `download_mayors()` - Current mayors from RNE CSV (557k records)
3. `download_municipal_2020()` - Municipal elections (both rounds, different delimiters)
4. `download_presidential_2022()` - Presidential elections (different encodings per round)
5. `download_legislative_2024()` - Legislative elections (wide CSV format)
6. `merge_political_data()` - Combines all above into `political_data.json`

**Output**: `data/political_cache/political_data.json` keyed by INSEE code, copied to `frontend/data/`

#### 3. Frontend (`frontend/`)

**Stack**: Vanilla JS + Leaflet.js (no build step)

**Key files**:
- `app.js` - Map initialization, school markers, filters, popup generation
- `index.html` - Map container, search box, filter controls
- `styles.css` - Mobile-responsive layout

**Data loading**: Two JSON files loaded at startup:
- `schools.json` (2.4 MB) - All school data
- `political_data.json` (1.7 MB) - Political context by commune

**Join logic**: Schools have `address.insee_code`, matched against `politicalData[insee_code]` in `formatPoliticalContext()` function.

### Critical Data Structures

#### UAI Code (Unité Administrative Immatriculée)
8-character unique school identifier (e.g., `0440985G`). Used to join all education datasets.

#### INSEE Code
5-digit commune identifier (2-digit department + 3-digit commune, e.g., `44109` = Nantes). Used to join political data to schools.

#### schools.json Structure
```json
{
  "uai": "0440985G",
  "name": "École primaire",
  "type": "Primaire|Collège|Lycée",
  "address": {
    "insee_code": "44109",  // CRITICAL for political data join
    "postal_code": "44190",
    "city": "Clisson"
  },
  "ips": { "value": "111.8", ... },
  "exam_results": { ... },
  // ... other fields
}
```

#### political_data.json Structure
```json
{
  "44109": {  // INSEE code as key
    "mayor": { "first_name": "Jean", "last_name": "Dupont", "party": "Divers droite" },
    "presidential_2022": {
      "round_1": [{"candidate": "Macron", "percentage": 29.6}, ...],
      "round_2": {"macron": 58.2, "le_pen": 41.8}
    },
    "legislative_2024": { "round_1": [...], "round_2": [...] },
    "municipal_2020": { "percentage": 67.8, ... }
  }
}
```

## Region Configuration

**Currently hardcoded** to Pays de la Loire in 4 scraper files:

1. `scraper/download_data.py` (lines 16-20):
   - `REGION_NAME = "Pays de la Loire"`
   - `REGION_CODE = "52"`
   - `DEPARTMENT_CODES = ['044', '049', '053', '072', '085']`

2. `scraper/download_enrollment_data.py` (line 17):
   - `DEPARTMENT_CODES_SHORT = ['44', '49', '53', '72', '85']`

3. `scraper/download_language_data.py` (line 15):
   - `REGION_NAME = "Pays de la Loire"`

4. `scraper/download_political_data.py` (line 28):
   - `DEPARTMENTS = ["44", "49", "53", "72", "85"]`

**To add new region/department**: Change these constants and re-run scrapers. Test suite (34 tests) will catch data quality issues.

## Critical Bugs Documented in Tests

The test suite (`tests/test_download_political_data.py`) documents 6 critical bugs fixed during development:

1. **Presidential Round 1 percentage bug** (test_presidential_round1_no_accumulation):
   - ❌ Don't accumulate `exprimés` per candidate (each row has SAME total)
   - ✅ Set total once per commune

2. **Presidential Round 2 calculation** (test_presidential_round2_le_pen_calculation):
   - CSV only has Macron data
   - Calculate Le Pen as: `exprimes - macron_votes`

3. **Legislative Round 2 candidate limit** (test_legislative_round2_limit_to_two):
   - Round 2 is runoff election
   - Limit to 2 candidates maximum (not 4)

4. **Encoding differences** (test_utf8_preserves_accents):
   - Presidential Round 1: UTF-8
   - Presidential Round 2: latin-1
   - Municipal Round 1: TAB delimiter
   - Municipal Round 2: semicolon delimiter

5. **INSEE code construction** (test_legislative_uses_full_insee):
   - Legislative CSVs already contain full INSEE code
   - ❌ Don't concatenate department code again

6. **BOM character handling** (test_bom_removal):
   - Remove UTF-8 BOM (`\ufeff`) from CSV start before parsing

**These bugs will reoccur when adapting to new regions** - always run full test suite.

## Data Quality Notes

### IPS Coverage
- 95.1% of primary schools have IPS
- 4.9% missing due to: very small schools, new schools, data privacy

### Political Data Coverage (Pays de la Loire)
- Mayors: 99.1% (1,220/1,231 communes)
- Presidential 2022: 99.6%
- Legislative 2024: 99.8%
- Municipal 2020: 40.9% (many mayors elected in round 1, no round 2 data)

### Party Labels
`PARTY_LABELS` dictionary in `download_political_data.py` (lines 33-66) maps 24 party codes (LDVD, LDVG, LUG, etc.) to readable French labels ("Divers droite", "Union de la gauche", etc.).

## Rate Limiting

- **geo.api.gouv.fr**: 50 req/sec limit, using 45 req/sec (0.022s delay)
- **data.gouv.fr**: No rate limit (direct CSV downloads)
- **RNE mayors CSV**: Direct download (557k records, ~20 MB)

## Deployment

GitHub Pages serves `frontend/` directly. Push to `main` branch auto-deploys.

**Pre-deployment checklist**:
1. Run `python3 tests/run_all_tests.py` (must pass all 34 tests)
2. Verify `frontend/data/schools.json` exists
3. Verify `frontend/data/political_data.json` exists (if using political feature)
4. Test locally: `cd frontend && python3 -m http.server 8000`
