# Carte des Écoles - Pays de la Loire

Interactive map showing schools in the Pays de la Loire region (France) with quality indicators focused on student well-being and educational environment.

🌐 **[View Live Map](https://guelowrd.github.io/france-schools-map/)** (if deployed)

## Overview

**Region**: Pays de la Loire
**Departments**: Loire-Atlantique (44), Maine-et-Loire (49), Mayenne (53), Sarthe (72), Vendée (85)

**School Types**:
- **Écoles Primaires** (Primary schools, ages 6-11) - Blue markers 🔵
- **Collèges** (Middle schools, ages 11-15) - Yellow markers 🟡
- **Lycées** (High schools, ages 15-18) - Red markers 🔴

**Scope**: General curriculum only (professional/technical-only schools excluded)

## Features

### Interactive Map
- Search by city name
- Filter by school type (Primaire/Collège/Lycée)
- Filter by sector (Public/Privé)
- Click schools for detailed information
- Real-time statistics update based on filters

### Data Displayed

**For All Schools:**
- Name, address, type (primary/middle/high)
- Public or private status
- Number of students & enrollment year
- **IPS** (Social Position Index) with regional/national context
- **Diversity indicator** (IPS standard deviation with interpretation)

**For Primary Schools:**
- Actual class sizes (students per class)
- Number of classes

**For Collèges (Middle Schools):**
- Brevet exam success rate
- Distribution of honors (mentions)
- **Languages taught** (LV1/LV2)

**For Lycées (High Schools):**
- Baccalauréat success rate
- **Access rates** (% of students completing full program from 2nde to Bac) - Key well-being indicator
- **Value added** (performance vs expected based on student profile)
- **Languages taught** (LV1/LV2)

## Data Sources

All data from [data.education.gouv.fr](https://data.education.gouv.fr) (French Ministry of Education open data portal):

1. **Annuaire de l'Éducation** - School directory with addresses and coordinates
2. **IPS** (Indice de Position Sociale) - Socioeconomic index (2024-2025 data)
3. **Effectifs d'élèves** - Student enrollment and class counts (2024 data)
4. **Résultats du Brevet** - Middle school exam results (most recent year)
5. **Indicateurs de Résultats des Lycées** - High school performance indicators
6. **Offre de langues** - Language offerings (LV1/LV2) for secondary schools

## Project Structure

```
france-schools-map/
├── scraper/
│   ├── download_data.py              # Download school directory & exam results
│   ├── download_enrollment_data.py   # Download student counts
│   ├── download_language_data.py     # Download language offerings
│   ├── download_political_data.py    # Download political data (mayors, elections)
│   ├── merge_datasets.py             # Join all data on UAI code
│   └── requirements.txt
├── data/
│   ├── annuaire_pays_loire.json      # Schools directory
│   ├── ips_*_pays_loire.json         # IPS datasets (écoles/collèges/lycées)
│   ├── effectifs_*_pays_loire.json   # Enrollment data
│   ├── language_offerings_pays_loire.json  # Language offerings
│   ├── *_results_pays_loire.json     # Exam results
│   ├── schools.json                  # Final merged data
│   └── political_cache/              # Political data cache
│       ├── insee_mapping.json        # Postal code → INSEE code mapping
│       ├── mayors.json               # Current mayors by commune
│       ├── municipal_2020.json       # Municipal election results
│       ├── presidential_2022.json    # Presidential election results
│       ├── legislative_2024.json     # Legislative election results
│       └── political_data.json       # Final merged political data
├── frontend/
│   ├── index.html                    # Main page
│   ├── app.js                        # Leaflet map & filters
│   ├── styles.css                    # Styling
│   └── data/
│       ├── schools.json              # Copy of final data
│       └── political_data.json       # Political context by commune
├── tests/
│   ├── run_all_tests.py              # Run all tests (34 tests total)
│   ├── test_download_political_data.py  # Unit tests (24 tests)
│   ├── test_integration.py           # Integration tests (10 tests)
│   ├── test_data_validation.py       # Data integrity tests
│   ├── test_frontend.js              # Frontend validation tests
│   ├── run_tests.sh                  # Test runner
│   └── README.md                     # Test documentation
└── README.md
```

## Setup & Usage

### 1. Install Dependencies

```bash
cd scraper
pip install -r requirements.txt
```

### 2. Download Data

```bash
# Download school directory and exam results
python3 download_data.py

# Download enrollment data
python3 download_enrollment_data.py

# Download language offerings
python3 download_language_data.py
```

This will fetch:
- 2,998 general curriculum schools
- 6,598 primary schools with IPS
- 827 middle schools with IPS
- 379 high schools with IPS
- 1,381 primary schools with enrollment
- 492 collèges with enrollment
- 143 lycées with enrollment
- 565 schools with language offerings
- 619 collèges with Brevet results
- 144 lycées with Bac results

**Optional: Download Political Data**

```bash
# Download political context data (mayors, election results)
python3 download_political_data.py
```

This will fetch:
- Current mayors from RNE API (Répertoire National des Élus)
- Municipal 2020 election results (2nd round)
- Presidential 2022 election results (both rounds)
- Legislative 2024 election results (both rounds)
- INSEE commune code mappings for all 1,231 communes in Pays de la Loire

**Note**: Takes ~10-15 minutes with optimized rate limiting (45 requests/second for geo.api.gouv.fr).

Output: `data/political_cache/political_data.json`

### 3. Merge Datasets

```bash
python3 merge_datasets.py
```

Creates `data/schools.json` with 2,990 schools (all with coordinates, deduplicated).

**If you downloaded political data, copy it to frontend:**

```bash
cp data/political_cache/political_data.json frontend/data/
```

### 4. Run Tests

```bash
./tests/run_tests.sh
```

Validates data integrity and frontend compatibility (28 tests).

**Run comprehensive political data tests:**

```bash
python3 tests/run_all_tests.py
```

Validates political data structure, coverage, and quality (34 tests: 24 unit + 10 integration).

### 5. View Map

Open `frontend/index.html` in a web browser:

```bash
cd frontend
open index.html  # macOS
# or
python3 -m http.server 8000  # Then visit http://localhost:8000
```

## Data Coverage

- **Total schools**: 2,990 (after deduplication)
  - Primary (Écoles): 2,310 (77.3%)
  - Middle (Collèges): 522 (17.5%)
  - High (Lycées): 158 (5.3%)

- **IPS data**: 91.8% coverage (2,745 schools)
  - 115 schools have "NS" (Non Significatif) values
- **Enrollment data**: 53.9% coverage (1,613 schools)
  - Actual class sizes for primary schools
- **Exam results**: 18.3% coverage (542 schools)
  - 77.8% of collèges, 86.1% of lycées
- **Language offerings**: 81.5% coverage for collèges/lycées (554 schools)
  - 100% teach English as LV1
  - Spanish (100%) and German (95%) most common for LV2
- **Political context**: Available for 1,231 communes (all Pays de la Loire)
  - Current mayors from RNE API (99.1% coverage)
  - Election results (Municipal 2020, Presidential 2022, Legislative 2024)
  - Matched via INSEE commune codes

## Key Indicators Explained

### IPS (Indice de Position Sociale)
- Range: ~60 (disadvantaged) to ~160 (privileged)
- National average: ~105
- Higher IPS = more privileged family backgrounds
- **Note**: Higher isn't necessarily "better" - diversity matters!
- **Écart-type** (standard deviation) indicates socioeconomic diversity:
  - <20: très homogène (very homogeneous)
  - 20-28: plutôt homogène (rather homogeneous)
  - 28-35: plutôt hétérogène (rather heterogeneous)
  - \>35: très hétérogène (very heterogeneous)

### Access Rates (Lycées)
- **Taux d'accès 2nde → Bac**: % of students who start in 2nde and complete the Bac
- Values: 70-95% typical
- **Key metric for student well-being**: High rate indicates supportive environment where students complete their education
- More important than pure success rate for understanding school climate

### Value Added (Valeur Ajoutée)
- How school performs vs expected (based on student profiles)
- Positive = better than expected
- Negative = less good than expected
- Zero = performing as expected

### Language Offerings
- **LV1** (Première langue vivante): First foreign language, typically English
- **LV2** (Deuxième langue vivante): Second foreign language, typically Spanish or German
- Most schools offer multiple LV2 options (Spanish, German, Italian, Chinese)

### Political Context
Each school popup now displays the political context of its commune, providing insight into the local political landscape:

**Data Displayed (6 lines):**
1. **Current Mayor** - Name and political affiliation (from RNE - Répertoire National des Élus)
2. **Municipal 2020** - 2nd round election results with winning percentage
3. **Presidential 2022 (2nd tour)** - Macron vs Le Pen percentages
4. **Presidential 2022 (1er tour)** - TOP 4 candidates with percentages
5. **Legislative 2024 (2nd tour)** - TOP 4 individual candidates with parties
6. **Legislative 2024 (1er tour)** - TOP 4 individual candidates with parties

**Data Sources:**
- **RNE API** (via Opendatasoft) - Current elected mayors
- **data.gouv.fr** - Official election results (Municipal 2020, Presidential 2022, Legislative 2024)
- **geo.api.gouv.fr** - INSEE commune code mapping for reliable matching

**Coverage:**
- Political data available for 1,231 communes (all Pays de la Loire)
  - Mayors: 99.1% coverage (1,220 communes)
  - Presidential 2022: 99.6% coverage
  - Legislative 2024: 99.8% coverage
  - Municipal 2020: 40.9% coverage (504 communes)
- Schools matched via INSEE commune codes (preserved from annuaire data)
- Missing data shown as "N/A" (never hidden)

## Design Philosophy

This map is **purely informational** rather than ranking-based:
- No color-coding by "quality" - only by school type
- Displays context (national/regional averages) to help users interpret indicators
- Focuses on well-being indicators (access rates, retention) not just academic results
- Shows complete picture: size, diversity, results, environment, language programs

## Testing

Comprehensive test suite to catch regressions:

```bash
# Run all tests
./tests/run_tests.sh

# Run individual test suites
python3 tests/test_data_validation.py    # Data integrity (17 tests)
python3 tests/run_all_tests.py           # Political data (34 tests: 24 unit + 10 integration)
node tests/test_frontend.js              # Frontend validation (11 tests)
```

**Tests cover:**
- Data structure validation
- Geographic bounds checking
- Coverage metrics
- Data quality (no duplicates, reasonable values, dates present)
- Regression prevention (multi-year aggregation bugs, professional lycées)
- Frontend compatibility

See `tests/README.md` for detailed documentation.

## Updating Political Data

Political data should be refreshed periodically to reflect:
- New mayors elected in special elections
- Updated municipal elections (every 6 years)
- New presidential elections (every 5 years)
- New legislative elections (every 5 years)

**To update:**

```bash
cd scraper
python3 download_political_data.py
cp ../data/political_cache/political_data.json ../frontend/data/
```

**What gets updated:**
- Current mayors from RNE API (live data, always current)
- Election results from data.gouv.fr CSV files (static, need new URLs for future elections)

**Note**: Municipal 2020, Presidential 2022, and Legislative 2024 data sources are currently placeholders in the script. To populate them:
1. Find CSV download URLs on [data.gouv.fr](https://www.data.gouv.fr)
2. Update `download_political_data.py` functions to parse the CSVs
3. Filter by departments: 44, 49, 53, 72, 85 (Pays de la Loire)
4. Aggregate results by INSEE commune code

**Rate limits:**
- geo.api.gouv.fr: 1 request/second (strictly enforced)
- RNE API via Opendatasoft: ~1,000 records per request (no rate limit issues)

Expected download time: ~20-25 minutes for full refresh.

## Development

### Adding New Features

When adding new data sources or features:

1. Download new data in `scraper/download_*.py`
2. Update `merge_datasets.py` to integrate data
3. Update frontend (`app.js`, `styles.css`, `index.html`)
4. **Add tests** in `tests/test_data_validation.py` and `tests/test_frontend.js`
5. Run `./tests/run_tests.sh` before committing
6. Update this README

### Data Quality Checks

The test suite catches common issues:
- Duplicate UAI codes (multi-campus schools)
- Multi-year aggregation bugs (inflated student counts)
- Missing dates/years
- Invalid coordinates
- Professional schools slipping through filters

Always run tests before pushing!

## License

Data from data.education.gouv.fr (open data, Licence Ouverte / Open Licence).
Map built with Leaflet.js.

## Possible Future Enhancements

Ideas not yet implemented:
- IPS range slider filter
- School size filter (small/medium/large)
- Color-code markers by IPS level
- Marker clustering for better performance
- Export filtered results as CSV
- Historical trends (multiple years comparison)
- Charts/visualizations panel
- Mobile UI improvements
- Dark mode
- Shareable filter URLs
- Favorites/bookmarks in localStorage

## Contributing

Found a bug or have a suggestion? Please open an issue on GitHub!

---

**Note**: This is an independent project using public French education data. It is not affiliated with or endorsed by the French Ministry of Education.
