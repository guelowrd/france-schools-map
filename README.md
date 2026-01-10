# Carte des Écoles - Pays de la Loire

Interactive map showing schools in the Pays de la Loire region (France) with quality indicators focused on student well-being and educational environment.

## Overview

**Region**: Pays de la Loire
**Departments**: Loire-Atlantique (44), Maine-et-Loire (49), Mayenne (53), Sarthe (72), Vendée (85)

**School Types**:
- **Écoles Primaires** (Primary schools, ages 6-11) - Green markers
- **Collèges** (Middle schools, ages 11-15) - Orange markers
- **Lycées** (High schools, ages 15-18) - Purple markers

**Scope**: General curriculum only (technical/professional-only schools excluded)

## Data Sources

All data from [data.education.gouv.fr](https://data.education.gouv.fr) (French Ministry of Education open data portal):

1. **Annuaire de l'Éducation** - School directory with addresses and coordinates
2. **IPS** (Indice de Position Sociale) - Socioeconomic index for all school types
3. **Résultats du Brevet** - Middle school exam results
4. **Indicateurs de Résultats des Lycées** - High school performance indicators

## Information Displayed

### For All Schools
- Name, address, type (primary/middle/high)
- Public or private status
- Number of students
- Estimated class size
- **IPS** (Social Position Index) with regional/national context
- **Diversity indicator** (IPS standard deviation)

### For Collèges (Middle Schools)
- Brevet exam success rate
- Distribution of honors (mentions)

### For Lycées (High Schools)
- Baccalauréat success rate
- **Access rates** (% of students completing full program from 2nde to Bac) - Key well-being indicator
- **Value added** (performance vs expected based on student profile)

## Project Structure

```
france-schools-map/
├── scraper/
│   ├── explore_data_sources.py    # API exploration
│   ├── download_data.py           # Download all datasets
│   ├── merge_datasets.py          # Join data on UAI code
│   └── requirements.txt
├── data/
│   ├── annuaire_pays_loire.json   # Schools directory
│   ├── ips_*_pays_loire.json      # IPS datasets
│   ├── *_results_pays_loire.json  # Exam results
│   └── schools.json               # Final merged data
├── frontend/
│   ├── index.html
│   ├── app.js                     # Leaflet map
│   ├── styles.css
│   └── data/
│       └── schools.json           # Copy of final data
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
python3 download_data.py
```

This will fetch:
- 3,086 general curriculum schools
- 6,598 primary schools with IPS
- 827 middle schools with IPS
- 379 high schools with IPS
- 619 collèges with Brevet results
- 144 lycées with Bac results

### 3. Merge Datasets

```bash
python3 merge_datasets.py
```

Creates `data/schools.json` with 3,082 schools (all with coordinates).

### 4. View Map

Open `frontend/index.html` in a web browser:

```bash
cd frontend
open index.html  # macOS
# or
python3 -m http.server 8000  # Then visit http://localhost:8000
```

## Data Coverage

- **Total schools**: 3,082
  - Primary (Écoles): 2,310 (75%)
  - Middle (Collèges): 522 (17%)
  - High (Lycées): 250 (8%)

- **IPS data**: 90.8% coverage
- **Exam results**: 17.7% coverage (mainly collèges and lycées)

## Key Indicators Explained

### IPS (Indice de Position Sociale)
- Range: ~60 (disadvantaged) to ~160 (privileged)
- National average: ~105
- Higher IPS = more privileged family backgrounds
- **Note**: Higher isn't necessarily "better" - diversity matters!
- **Écart-type** (standard deviation) indicates socioeconomic diversity

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

## Design Philosophy

This map is **purely informational** rather than ranking-based:
- No color-coding by "quality" - only by school type
- Displays context (national/regional averages) to help users interpret indicators
- Focuses on well-being indicators (access rates, retention) not just academic results
- Shows complete picture: size, diversity, results, environment

## License

Data from data.education.gouv.fr (open data, Licence Ouverte / Open Licence).
Map built with Leaflet.js.

## Future Enhancements

Potential additions (not implemented):
- Filter by public/private
- Search by school name or city
- Show historical trends (multiple years)
- Student-teacher ratio (if data becomes available)
- School climate surveys (if available in open data)
