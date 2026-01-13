#!/usr/bin/env python3
"""
Download all education data for Pays de la Loire region
Filters to general curriculum only (excludes professional/technical-only schools)
"""

import requests
import json
import time
from pathlib import Path

# API base URL
BASE_URL = "https://data.education.gouv.fr/api/v2/catalog/datasets"

# Configuration for multiple regions
REGIONS = [
    {
        'name': 'Pays de la Loire',
        'name_upper': 'PAYS DE LA LOIRE',
        'code': '52',
        'departments': ['044', '049', '053', '072', '085'],
        'departments_short': ['44', '49', '53', '72', '85']
    },
    {
        'name': 'Nouvelle-Aquitaine',
        'name_upper': 'NOUVELLE-AQUITAINE',
        'code': '75',
        'departments': ['017', '019', '023', '024', '033', '040', '047', '064', '079', '086', '087'],  # All Nouvelle-Aquitaine
        'departments_short': ['17', '19', '23', '24', '33', '40', '47', '64', '79', '86', '87']  # Missing: 16 (Charente)
    }
]

# Output directory
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def load_or_create(filename):
    """Load existing JSON data or return empty list."""
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath, encoding='utf-8') as f:
            return json.load(f)
    return []


def save_and_merge(filename, new_records, key_field):
    """Merge new records with existing data by key field, then save."""
    existing_records = load_or_create(filename)

    # Index existing by key (extract from nested structure)
    existing_by_key = {}
    for record in existing_records:
        fields = record.get('record', {}).get('fields', {})
        key = fields.get(key_field)
        if key:
            existing_by_key[key] = record

    # Merge new records (overwrites existing with same key)
    for record in new_records:
        fields = record.get('record', {}).get('fields', {})
        key = fields.get(key_field)
        if key:
            existing_by_key[key] = record

    # Save combined
    combined = list(existing_by_key.values())
    filepath = DATA_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    return combined


def fetch_paginated_data(dataset_id, filters=None, limit=100):
    """
    Fetch all records from a dataset with pagination
    """
    print(f"\nFetching data from {dataset_id}...")

    url = f"{BASE_URL}/{dataset_id}/records"
    all_records = []
    offset = 0

    while True:
        params = {
            'limit': limit,
            'offset': offset
        }

        if filters:
            params['where'] = filters

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            records = data.get('records', [])
            if not records:
                break

            all_records.extend(records)
            print(f"  Fetched {len(all_records)} records...", end='\r')

            # Check if we got all records
            total_count = data.get('total_count', 0)
            if len(all_records) >= total_count:
                break

            offset += limit
            time.sleep(0.5)  # Be respectful of API

        except requests.exceptions.RequestException as e:
            print(f"\n❌ Error fetching data: {e}")
            break

    print(f"\n✓ Fetched {len(all_records)} total records")
    return all_records


def download_annuaire():
    """
    Download education directory for NEW regions only (Charente-Maritime)
    Filter to general curriculum only:
    - Écoles élémentaires (keep)
    - Collèges (keep all)
    - Lycées généraux only (voie_generale)
    - Exclude: Lycées professionnels, technological, CFA, etc.
    """
    print("\n" + "="*80)
    print("1. DOWNLOADING ANNUAIRE (Education Directory)")
    print("="*80)

    all_filtered_records = []

    # Only download NEW region (Nouvelle-Aquitaine - all departments)
    new_region = REGIONS[1]  # Nouvelle-Aquitaine only
    print(f"\n→ Downloading annuaire for {new_region['name']} (all departments)...")
    filters = f"libelle_region='{new_region['name']}'"
    records = fetch_paginated_data("fr-en-annuaire-education", filters=filters)

    # Filter to general curriculum
    filtered_records = []
    for record in records:
        fields = record.get('record', {}).get('fields', {})
        type_etab = fields.get('type_etablissement', '') or ''
        libelle_nature = fields.get('libelle_nature', '') or ''

        # Keep elementary schools
        if 'Ecole' in type_etab or 'ECOLE' in libelle_nature.upper():
            # Exclude pure maternelles (pre-school only)
            if fields.get('ecole_elementaire') == 1:  # Has elementary level
                filtered_records.append(record)

        # Keep all collèges (middle schools are general by default)
        elif 'Collège' in type_etab or 'COLLEGE' in libelle_nature.upper():
            filtered_records.append(record)

        # Keep lycées but filter to general track only
        elif 'Lycée' in type_etab or 'LYCEE' in libelle_nature.upper():
            school_name = fields.get('nom_etablissement', '') or ''

            # EXCLUDE professional lycées (check both name and libelle_nature)
            if 'PROFESSIONNEL' in libelle_nature.upper() or 'professionnel' in school_name.lower():
                # Skip professional lycées
                continue

            # Check for general track only
            voie_generale = fields.get('voie_generale')
            voie_pro = fields.get('voie_professionnelle')

            # Keep ONLY if has general track
            if voie_generale:
                filtered_records.append(record)
            # Also keep if voie fields are None (data not specified)
            elif voie_generale is None and voie_pro is None:
                filtered_records.append(record)

    print(f"✓ Filtered to {len(filtered_records)} general curriculum schools for {new_region['name']}")
    print(f"  (from {len(records)} total establishments)")

    all_filtered_records.extend(filtered_records)

    # Merge with existing and save
    combined = save_and_merge("annuaire_pays_loire.json", all_filtered_records, key_field='identifiant_de_l_etablissement')
    print(f"\n✓ Total schools across all regions: {len(combined)}")
    print(f"✓ Saved to {DATA_DIR / 'annuaire_pays_loire.json'}")
    return combined


def download_ips_ecoles():
    """
    Download IPS data for primary schools in NEW regions only (Charente-Maritime)
    """
    print("\n" + "="*80)
    print("2. DOWNLOADING IPS ÉCOLES (Primary Schools Social Index)")
    print("="*80)

    # Only download NEW region (Nouvelle-Aquitaine - all departments)
    new_region = REGIONS[1]  # Nouvelle-Aquitaine only
    print(f"\n→ Downloading IPS écoles for {new_region['name']} (all departments)...")
    filters = f"region='{new_region['name_upper']}'"
    records = fetch_paginated_data("fr-en-ips-ecoles-ap2022", filters=filters)

    # Merge with existing and save
    combined = save_and_merge("ips_ecoles_pays_loire.json", records, key_field='uai')
    print(f"✓ Total IPS écoles across all regions: {len(combined)}")
    print(f"✓ Saved to {DATA_DIR / 'ips_ecoles_pays_loire.json'}")
    return combined


def download_ips_colleges():
    """
    Download IPS data for middle schools (collèges) in NEW regions only (Charente-Maritime)
    Filter by department codes since region filter doesn't work for this dataset
    """
    print("\n" + "="*80)
    print("3. DOWNLOADING IPS COLLÈGES (Middle Schools Social Index)")
    print("="*80)

    # Only download NEW region
    new_region = REGIONS[1]  # Nouvelle-Aquitaine only
    print(f"\n→ Downloading IPS collèges for {new_region['name']}...")

    # Filter by department codes (more reliable than region name)
    dept_filter = " OR ".join([f"code_du_departement='{code}'" for code in new_region['departments_short']])
    records = fetch_paginated_data("fr-en-ips-colleges-ap2023", filters=dept_filter)

    # Merge with existing and save
    combined = save_and_merge("ips_colleges_pays_loire.json", records, key_field='uai')
    print(f"✓ Total IPS collèges across all regions: {len(combined)}")
    print(f"✓ Saved to {DATA_DIR / 'ips_colleges_pays_loire.json'}")
    return combined


def download_ips_lycees():
    """
    Download IPS data for high schools (lycées) in NEW regions only (Charente-Maritime)
    Filter by department codes since region filter doesn't work for this dataset
    """
    print("\n" + "="*80)
    print("4. DOWNLOADING IPS LYCÉES (High Schools Social Index)")
    print("="*80)

    # Only download NEW region
    new_region = REGIONS[1]  # Nouvelle-Aquitaine only
    print(f"\n→ Downloading IPS lycées for {new_region['name']}...")

    # Filter by department codes (more reliable than region name)
    dept_filter = " OR ".join([f"code_du_departement='{code}'" for code in new_region['departments_short']])
    records = fetch_paginated_data("fr-en-ips-lycees-ap2023", filters=dept_filter)

    # Merge with existing and save
    combined = save_and_merge("ips_lycees_pays_loire.json", records, key_field='uai')
    print(f"✓ Total IPS lycées across all regions: {len(combined)}")
    print(f"✓ Saved to {DATA_DIR / 'ips_lycees_pays_loire.json'}")
    return combined


def download_brevet_results():
    """
    Download Brevet exam results for collèges in NEW regions only (Charente-Maritime)
    Get most recent year only
    """
    print("\n" + "="*80)
    print("5. DOWNLOADING BREVET RESULTS (Middle School Exams)")
    print("="*80)

    # Only download NEW region
    new_region = REGIONS[1]  # Nouvelle-Aquitaine only
    print(f"\n→ Downloading Brevet results for {new_region['name']}...")

    # Filter by department codes
    dept_filter = " OR ".join([f"code_departement='{code}'" for code in new_region['departments']])
    records = fetch_paginated_data("fr-en-dnb-par-etablissement", filters=dept_filter)

    # Keep only most recent year per school
    school_records = {}
    for record in records:
        fields = record.get('record', {}).get('fields', {})
        uai = fields.get('numero_d_etablissement')
        session = fields.get('session', '')

        if uai:
            if uai not in school_records or session > school_records[uai].get('record', {}).get('fields', {}).get('session', ''):
                school_records[uai] = record

    latest_records = list(school_records.values())
    print(f"\n✓ Filtered to {len(latest_records)} schools (most recent exam year)")

    # Merge with existing and save
    combined = save_and_merge("brevet_results_pays_loire.json", latest_records, key_field='numero_d_etablissement')
    print(f"✓ Total Brevet results across all regions: {len(combined)}")
    print(f"✓ Saved to {DATA_DIR / 'brevet_results_pays_loire.json'}")
    return combined


def download_bac_results():
    """
    Download Baccalauréat results for lycées in NEW regions only (Charente-Maritime)
    Get most recent year only, general track only
    """
    print("\n" + "="*80)
    print("6. DOWNLOADING BAC RESULTS (High School Exams)")
    print("="*80)

    # Only download NEW region
    new_region = REGIONS[1]  # Nouvelle-Aquitaine only
    print(f"\n→ Downloading Bac results for {new_region['name']}...")

    # Filter by department codes (use short codes without leading zeros)
    dept_filter = " OR ".join([f"code_departement='{code}'" for code in new_region['departments_short']])
    records = fetch_paginated_data("fr-en-indicateurs-de-resultat-des-lycees-gt_v2", filters=dept_filter)

    # Keep only most recent year per school
    school_records = {}
    for record in records:
        fields = record.get('record', {}).get('fields', {})
        uai = fields.get('uai')
        annee = fields.get('annee', '')

        if uai:
            if uai not in school_records or annee > school_records[uai].get('record', {}).get('fields', {}).get('annee', ''):
                school_records[uai] = record

    latest_records = list(school_records.values())
    print(f"\n✓ Filtered to {len(latest_records)} lycées (most recent exam year)")

    # Merge with existing and save
    combined = save_and_merge("bac_results_pays_loire.json", latest_records, key_field='uai')
    print(f"✓ Total Bac results across all regions: {len(combined)}")
    print(f"✓ Saved to {DATA_DIR / 'bac_results_pays_loire.json'}")
    return combined


def main():
    """
    Download datasets for NEW regions and merge with existing data
    """
    print("\n" + "="*80)
    print("DOWNLOADING EDUCATION DATA - ADDING NEW REGIONS")
    print("New region: Nouvelle-Aquitaine (Charente-Maritime)")
    print("Scope: General curriculum only (Écoles, Collèges, Lycées généraux)")
    print("="*80)

    # Download all datasets (will merge with existing)
    annuaire = download_annuaire()
    ips_ecoles = download_ips_ecoles()
    ips_colleges = download_ips_colleges()
    ips_lycees = download_ips_lycees()
    brevet = download_brevet_results()
    bac = download_bac_results()

    print("\n" + "="*80)
    print("DOWNLOAD & MERGE COMPLETE")
    print("="*80)
    print(f"\nTotal after merge:")
    print(f"  - {len(annuaire)} schools (general curriculum)")
    print(f"  - {len(ips_ecoles)} primary schools with IPS")
    print(f"  - {len(ips_colleges)} middle schools with IPS")
    print(f"  - {len(ips_lycees)} high schools with IPS")
    print(f"  - {len(brevet)} collèges with Brevet results")
    print(f"  - {len(bac)} lycées with Bac results")
    print(f"\nNext step: Run merge_datasets.py to join all data on UAI")
    print()


if __name__ == '__main__':
    main()
