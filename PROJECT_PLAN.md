# France Schools Map - Pays de la Loire

Interactive map showing schools in Pays de la Loire region with quality indicators focused on student well-being.

## Scope

**Region**: Pays de la Loire (5 departments: Loire-Atlantique, Maine-et-Loire, Mayenne, Sarthe, Vendée)

**School Types**:
- Écoles Primaires (Primary schools, ages 6-11)
- Collèges (Middle schools, ages 11-15)
- Lycées (High schools, ages 15-18)

**Focus**: Student well-being and school quality beyond pure academic results

## Data Sources

### Primary Sources (Confirmed)

#### 1. Annuaire de l'Éducation (Education Directory)
**URL**: https://data.education.gouv.fr/explore/dataset/fr-en-annuaire-education/

**Fields to Extract**:
- `identifiant_de_l_etablissement` (UAI/RNE - unique identifier)
- `nom_etablissement` (School name)
- `type_etablissement` (Type: École élémentaire, Collège, Lycée, etc.)
- `statut_public_prive` (Public/Private)
- `adresse_1`, `code_postal`, `nom_commune` (Address)
- `latitude`, `longitude` (Coordinates - already geocoded!)
- `code_departement` (Department code)
- `libelle_academie`, `libelle_departement`, `libelle_region` (Administrative divisions)
- `nombre_d_eleves` (Number of students, if available)
- `telephone`, `mail`, `web` (Contact info)

**Filters**:
- `libelle_region = "Pays de la Loire"`
- `type_etablissement` in [École élémentaire, Collège, Lycée, ...]

#### 2. IPS (Indice de Position Sociale)
**URL**: https://data.education.gouv.fr/explore/dataset/fr-en-ips_ecoles/
**URL**: https://data.education.gouv.fr/explore/dataset/fr-en-ips_colleges/
**URL**: https://data.education.gouv.fr/explore/dataset/fr-en-ips_lycees/

**What is IPS**: Socioeconomic index (0-180+) measuring social background of students. Higher = more privileged families.

**Fields to Extract**:
- `uai` or `code_etablissement` (UAI/RNE to join with directory)
- `ips` (IPS value)
- `rentree_scolaire` (School year, e.g., "2023")
- `ecart_type_de_l_ips` (Standard deviation, indicates diversity)
- `secteur` (Public/Private)

**Note**: 3 separate datasets for écoles, collèges, and lycées

### Additional Potential Sources

#### 3. Résultats du Brevet (Middle School Exam Results)
**URL**: https://data.education.gouv.fr/explore/dataset/fr-en-dnb-par-etablissement/

**Why Useful**: While not academic-focused, success rates can indicate school support quality
- `taux_reussite` (Success rate)
- `taux_mention_tb` (Excellent mention rate)

#### 4. Résultats du Baccalauréat (High School Exam Results)
**URL**: https://data.education.gouv.fr/explore/dataset/fr-en-baccalaureat-general-technologique-professionnel/

**Fields**:
- `taux_reussite` (Success rate)
- `taux_acces_seconde_bac` (Proportion of students who complete from 2nde to Bac)
- `taux_mention_brut` (Mention rate)

#### 5. Climat Scolaire (School Climate - if available)
**Status**: To investigate - may not be in open data
- Student surveys on well-being
- Feeling of safety
- Relationship with teachers

#### 6. Taux d'Encadrement (Student-Teacher Ratio)
**Status**: May be in education statistics
- Lower ratio = more individual attention

#### 7. Équipements et Infrastructures (Facilities)
**Status**: May be in establishment characteristics
- Sports facilities
- Libraries
- Computer labs
- Canteen quality

### Data Not Likely Available (but would be ideal)
- Student satisfaction surveys
- Bullying/harassment rates
- Mental health support availability
- Extra-curricular activities offered
- Parent satisfaction
- Teacher turnover rates

## Technical Stack

### Data Processing
- **Language**: Python 3.9+
- **Libraries**:
  - `requests` - API calls
  - `pandas` - Data manipulation
  - `json` - Data storage

### Frontend
- **Framework**: Vanilla JavaScript + Leaflet.js
- **Hosting**: GitHub Pages (free)
- **Data Format**: JSON

### Deployment
- GitHub Actions for automatic deployment

## Data Processing Pipeline

### Step 1: Download Base Data
```python
# scraper/download_education_data.py
# - Fetch annuaire data (filtered by region)
# - Fetch IPS data (all 3 datasets)
# - Fetch exam results (optional)
# - Save as CSV/JSON
```

### Step 2: Join Datasets
```python
# scraper/merge_datasets.py
# - Join annuaire + IPS on UAI
# - Join exam results on UAI
# - Calculate composite indicators
# - Save to schools.json
```

### Step 3: Quality Indicators

**Composite Score Components** (ideas):
1. **IPS Score** (20-30%): Diversity is good, but very low IPS may indicate challenges
2. **Success Rates** (20-30%): Reasonable academic results
3. **Completion Rate** (20-30%): Students finishing their education cycle
4. **School Size** (10-20%): Not too large (impersonal) or too small (limited resources)
5. **Student-Teacher Ratio** (if available)

**Color Coding** (similar to Portugal):
- 🔵 Blue: Top performers (multiple good indicators)
- 🟢 Green: Good quality
- 🟡 Yellow: Average
- 🟠 Orange: Below average
- 🔴 Red: Needs attention

### Step 4: Frontend Display

**Map Features**:
- Clustered markers for density
- Color-coded by quality score
- Filter by school type (Primaire/Collège/Lycée)
- Filter by public/private
- Search by commune/school name

**Popup Info**:
- School name
- Address
- Type and status (Public/Private)
- Number of students
- IPS score (with context)
- Success rates (if available)
- Quality indicators

## Project Structure

```
france-schools-map/
├── scraper/
│   ├── download_education_data.py   # Fetch from data.gouv.fr APIs
│   ├── merge_datasets.py            # Join on UAI
│   ├── calculate_indicators.py      # Compute quality scores
│   └── requirements.txt
├── data/
│   ├── annuaire.json                # Raw directory data
│   ├── ips_ecoles.json              # IPS for primary
│   ├── ips_colleges.json            # IPS for middle
│   ├── ips_lycees.json              # IPS for high schools
│   └── schools.json                 # Final merged data
├── frontend/
│   ├── index.html
│   ├── app.js                       # Leaflet map
│   ├── styles.css
│   └── data/
│       └── schools.json             # Copy of final data
└── README.md
```

## API Access Notes

### data.education.gouv.fr API

**Base URL**: `https://data.education.gouv.fr/api/v2/catalog/datasets/{dataset_id}/records`

**Parameters**:
- `limit`: Max 100 per request (use pagination)
- `offset`: For pagination
- `where`: SQL-like filters (e.g., `libelle_region='Pays de la Loire'`)
- `select`: Choose fields to return
- `refine`: Filter by facet

**Example**:
```
https://data.education.gouv.fr/api/v2/catalog/datasets/fr-en-annuaire-education/records?where=libelle_region='Pays de la Loire'&limit=100
```

## Next Steps

1. ✅ Create project structure
2. ⏳ Explore data.education.gouv.fr API
3. ⏳ Download and analyze annuaire data for Pays de la Loire
4. ⏳ Download IPS datasets
5. ⏳ Merge datasets on UAI
6. ⏳ Define quality scoring algorithm
7. ⏳ Build frontend map
8. ⏳ Deploy to GitHub Pages

## Questions to Resolve

1. **IPS Interpretation**: What's a "good" IPS? High diversity vs homogeneous privileged?
2. **Quality Score**: How to weight different indicators?
3. **Data Freshness**: Which school year to use? (Most recent available)
4. **School Types**: Exact filters for type_etablissement (École élémentaire? Maternelle? Primaire?)
5. **Public vs Private**: Show both or separate views?

## Useful Links

- data.education.gouv.fr: https://data.education.gouv.fr
- Leaflet.js docs: https://leafletjs.com
- Pays de la Loire departments: 44, 49, 53, 72, 85
