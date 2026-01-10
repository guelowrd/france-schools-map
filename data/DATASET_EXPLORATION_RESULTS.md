# France Schools Map - Dataset Exploration Results

**Date**: 2026-01-10
**Region**: Pays de la Loire (Departments: 44, 49, 53, 72, 85)

## Summary

Successfully identified and tested 6 datasets from data.education.gouv.fr API. All datasets are accessible and contain relevant information for building a school quality map.

## 1. Annuaire de l'Éducation (Education Directory)

**Dataset ID**: `fr-en-annuaire-education`
**Records in Pays de la Loire**: 3,894 schools
**API URL**: https://data.education.gouv.fr/api/v2/catalog/datasets/fr-en-annuaire-education/records

**Key Fields** (72 total):
- `identifiant_de_l_etablissement` (UAI) - Unique identifier for joining
- `nom_etablissement` - School name
- `type_etablissement` - Type (Ecole, Collège, Lycée)
- `statut_public_prive` - Public/Private status
- `latitude`, `longitude` - **Already geocoded!**
- `code_departement`, `libelle_departement` - Department info
- `code_commune`, `nom_commune` - Municipality info
- `adresse_1`, `code_postal` - Address details
- `nombre_d_eleves` - Number of students (sometimes null)
- `telephone`, `mail`, `web` - Contact info
- `ecole_elementaire`, `ecole_maternelle` - School level flags
- `precision_localisation` - Geocoding precision ("Numéro de rue", etc.)

**Filter Applied**: `libelle_region='Pays de la Loire'`

**Notes**:
- This is the base dataset with all school information
- Already geocoded - no need for manual geocoding!
- Contains both primary and secondary schools
- Need to filter by `type_etablissement` to get only Écoles, Collèges, Lycées

---

## 2. IPS des Écoles (Primary Schools Social Index)

**Dataset ID**: `fr-en-ips-ecoles-ap2022`
**Records Nationwide**: 97,080
**API URL**: https://data.education.gouv.fr/api/v2/catalog/datasets/fr-en-ips-ecoles-ap2022/records

**Key Fields** (23 total):
- `uai` - Unique identifier (join with Annuaire on `identifiant_de_l_etablissement`)
- `nom_de_l_etablissement` - School name
- `ips` - Social Position Index (main metric)
- `rentree_scolaire` - School year (2022-2023, 2023-2024, etc.)
- `region` - Region name (filter: "PAYS DE LA LOIRE")
- `code_region` - Region code (17 for Pays de la Loire)
- `academie` - Academy (NANTES)
- `code_du_departement` - Department code
- `departement` - Department name
- `nom_de_la_commune` - Municipality name
- `secteur` - Sector ("public", "privé sous contrat")
- `ips_academique`, `ips_departemental`, `ips_national` - Comparison benchmarks

**IPS Values**: Range from ~60 (disadvantaged) to ~160 (privileged), average ~105

**Filter Needed**: `region='PAYS DE LA LOIRE'` or `code_region='17'`

**Notes**:
- Data starts from 2022 school year (methodology changed)
- Includes both public and private schools
- Has benchmark IPS values for comparison (académie, department, national levels)

---

## 3. IPS des Collèges (Middle Schools Social Index)

**Dataset ID**: `fr-en-ips_colleges`
**Records Nationwide**: 41,701
**API URL**: https://data.education.gouv.fr/api/v2/catalog/datasets/fr-en-ips_colleges/records

**Key Fields** (11 total):
- `uai` - Unique identifier
- `nom_de_l_etablissment` - School name (note: typo in field name)
- `ips` - Social Position Index
- `ecart_type_de_l_ips` - Standard deviation (diversity indicator)
- `rentree_scolaire` - School year (2018-2019 to 2021-2022)
- `academie` - Academy
- `code_du_departement` - Department code
- `departement` - Department name
- `nom_de_la_commune` - Municipality
- `secteur` - Sector ("public", "private")

**Filter Needed**: Need to filter by department codes (44, 49, 53, 72, 85)

**Notes**:
- Data covers 2016-2021 period (older methodology)
- **TODO**: Check if newer version exists (like `fr-en-ips-colleges-ap2022` or `ap2023`)
- Standard deviation can indicate socioeconomic diversity

---

## 4. IPS des Lycées (High Schools Social Index)

**Dataset ID**: `fr-en-ips_lycees`
**Records Nationwide**: 21,777
**API URL**: https://data.education.gouv.fr/api/v2/catalog/datasets/fr-en-ips_lycees/records

**Key Fields** (15 total):
- `uai` - Unique identifier
- `nom_de_l_etablissment` - School name
- `ips_ensemble_gt_pro` - Overall IPS (all tracks)
- `ips_voie_gt` - IPS for general/technological track
- `ips_voie_pro` - IPS for professional track
- `ecart_type_de_l_ips_voie_gt`, `ecart_type_de_l_ips_voie_pro` - Standard deviations
- `rentree_scolaire` - School year (2021-2022)
- `type_de_lycee` - Type ("LP" = professional, "LEGT" = general/tech, "LPO" = polyvalent)
- `academie`, `code_du_departement`, `departement` - Geographic info
- `nom_de_la_commune` - Municipality
- `secteur` - Sector ("public", "private")

**Filter Needed**: Department codes (44, 49, 53, 72, 85)

**Notes**:
- Data from 2021-2022 (older methodology)
- **TODO**: Check if newer version exists (`fr-en-ips-lycees-ap2022` or `ap2023`)
- Separate IPS for professional vs general tracks is useful

---

## 5. Résultats du Brevet (Middle School Exam Results)

**Dataset ID**: `fr-en-dnb-par-etablissement`
**Records Nationwide**: 139,580
**API URL**: https://data.education.gouv.fr/api/v2/catalog/datasets/fr-en-dnb-par-etablissement/records

**Key Fields** (21 total):
- `numero_d_etablissement` - UAI (join key)
- `patronyme` - School name
- `type_d_etablissement` - Type (COLLEGE)
- `secteur_d_enseignement` - Sector (PUBLIC/PRIVE)
- `session` - Exam year (2018, 2019, etc.)
- `inscrits` - Registered students
- `presents` - Students present for exam
- `admis` - Students admitted
- `taux_de_reussite` - Success rate (e.g., "94,20%")
- `admis_sans_mention` - Admitted without honors
- `nombre_d_admis_mention_ab` - Assez Bien honors
- `admis_mention_bien` - Bien honors
- `admis_mention_tres_bien` - Très Bien honors
- `code_region`, `libelle_region` - Region info
- `code_departement`, `libelle_departement` - Department info
- `commune`, `libelle_commune` - Municipality info

**Filter Needed**: Filter by region or department codes

**Notes**:
- Historical data across multiple years
- Success rate includes students who passed with/without honors
- Can calculate proportion of high honors (mention TB) as quality indicator

---

## 6. Indicateurs de Résultats des Lycées (High School Performance)

**Dataset ID**: `fr-en-indicateurs-de-resultat-des-lycees-gt_v2`
**Records Nationwide**: 30,139
**API URL**: https://data.education.gouv.fr/api/v2/catalog/datasets/fr-en-indicateurs-de-resultat-des-lycees-gt_v2/records

**Key Fields** (89 total):
- `uai` - Unique identifier
- `libelle_uai` - School name
- `annee` - Year
- `secteur` - Sector (public/private)
- `code_region`, `libelle_region` - Region
- `code_departement`, `libelle_departement` - Department
- `code_commune`, `libelle_commune` - Municipality

**Student Numbers**:
- `eff_2nde`, `eff_1ere`, `eff_term` - Enrollment in each grade

**Success Rates** (by track: ES, L, S, STMG, STI2D, etc.):
- `taux_reu_*` - Success rate for each track
- `taux_reu_total` - Overall success rate
- `presents_*` - Students present for exam by track

**Access Rates** (retention/progression):
- `taux_acces_2nde` - % of 2nde students who reach Terminale
- `taux_acces_1ere` - % of 1ere students who reach Terminale
- `taux_acces_term` - % of Term students who pass bac

**Value Added** (performance vs expected):
- `va_reu_*` - Value added for success rate
- `va_acces_*` - Value added for access rate
- Positive value = better than expected, negative = worse

**Honors** (by track):
- `taux_men_*` - Mention rate (honors) by track
- `nb_mentions_*` - Count of honors by level (AB, B, TB)

**Filter Needed**: Region or department codes

**Notes**:
- This dataset only covers général et technologique (GT) lycées
- **TODO**: Also check professional lycées dataset (`fr-en-indicateurs-de-resultat-des-lycees-pro_v2`)
- Value-added metrics are excellent for comparing schools fairly
- Access rates show if school retains students through completion

---

## Data Join Strategy

### Primary Key: UAI (Unité Administrative Immatriculée)

All datasets can be joined on the UAI code:

1. **Annuaire** (`identifiant_de_l_etablissement`) → Base dataset with coordinates
2. **IPS Écoles** (`uai`) → Join for primary schools
3. **IPS Collèges** (`uai`) → Join for middle schools
4. **IPS Lycées** (`uai`) → Join for high schools
5. **Brevet** (`numero_d_etablissement`) → Join for collèges exam results
6. **Bac GT** (`uai`) → Join for lycées exam results

### Proposed Merge Process:

```
1. Download Annuaire data for Pays de la Loire (3,894 schools)
2. Filter to keep only: Ecole, Collège, Lycée types
3. Download IPS data for all three school types (filtered by region)
4. Download exam results (filtered by region/department)
5. Join all datasets on UAI
6. For each school type:
   - Écoles: Join with IPS écoles
   - Collèges: Join with IPS collèges + Brevet results
   - Lycées: Join with IPS lycées + Bac results
7. Calculate composite quality indicators
8. Export to JSON for frontend map
```

---

## Quality Indicators to Calculate

Based on user request for **student well-being and happiness** (not pure academics):

### For All Schools:
1. **IPS Score** (with context):
   - Not "higher is better" - diversity matters
   - Show IPS vs regional/national average
   - Standard deviation indicates diversity (higher = more mixed backgrounds)

### For Collèges:
2. **Brevet Success Rate** - Reasonable academic support
3. **Honors Rate** - Students achieving excellence
4. **IPS + Success Correlation** - Schools that help all students succeed regardless of background

### For Lycées:
5. **Access Rates** (key metric!):
   - `taux_acces_2nde` - Do students stay through to graduation?
   - High access rate = supportive environment, students don't drop out
6. **Value Added** - Are students achieving more than expected?
7. **Overall Success Rate** - Reasonable academic outcomes

### Potential Additional Indicators (if data available):
8. **School Size** - Not too large (impersonal) or too small (limited resources)
9. **Public vs Private** - User preference
10. **Student-Teacher Ratio** (if available in Annuaire)

---

## Next Steps

1. ✅ Explore API and identify datasets
2. ⏳ Check for newer IPS collèges/lycées datasets (ap2022, ap2023 versions)
3. ⏳ Write download script for Annuaire data (Pays de la Loire only)
4. ⏳ Write download scripts for IPS datasets (filtered by region)
5. ⏳ Write download scripts for exam results (filtered by region/department)
6. ⏳ Create merge script to join all datasets on UAI
7. ⏳ Design quality scoring algorithm focused on student well-being
8. ⏳ Build frontend map (similar to Portugal project)
9. ⏳ Deploy to GitHub Pages

---

## API Rate Limits & Best Practices

- No explicit rate limit mentioned in API docs
- Use pagination: `limit=100` (max per request), `offset` for pagination
- Add delays between requests (e.g., 0.5-1 second) to be respectful
- Cache downloaded data locally to avoid re-downloading

---

## Sources

- [IPS Écoles Dataset (2022+)](https://data.education.gouv.fr/explore/dataset/fr-en-ips-ecoles-ap2022/)
- [IPS Collèges Dataset (2016-2021)](https://data.education.gouv.fr/explore/dataset/fr-en-ips_colleges/)
- [IPS Lycées Dataset (2016-2021)](https://data.education.gouv.fr/explore/dataset/fr-en-ips_lycees/)
- [Annuaire de l'Éducation](https://data.education.gouv.fr/explore/dataset/fr-en-annuaire-education/)
- [Brevet Results](https://data.education.gouv.fr/explore/dataset/fr-en-dnb-par-etablissement/)
- [Bac GT Results](https://data.education.gouv.fr/explore/dataset/fr-en-indicateurs-de-resultat-des-lycees-gt_v2/)
