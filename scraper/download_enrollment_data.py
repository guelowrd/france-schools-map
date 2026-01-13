#!/usr/bin/env python3
"""
Download enrollment data (effectifs) for all school types
Provides actual student counts and number of classes
"""

import requests
import json
import time
from pathlib import Path

# API base URL
BASE_URL = "https://data.education.gouv.fr/api/v2/catalog/datasets"

# Department configuration (multiple regions)
DEPARTMENTS = [
    # Pays de la Loire (existing - don't re-download)
    ('LOIRE-ATLANTIQUE', '44'),
    ('MAINE-ET-LOIRE', '49'),
    ('MAYENNE', '53'),
    ('SARTHE', '72'),
    ('VENDEE', '85'),
    # Nouvelle-Aquitaine (NEW - download only this)
    ('CHARENTE-MARITIME', '17')
]

# NEW departments to download (all Nouvelle-Aquitaine)
NEW_DEPARTMENTS = [
    ('CHARENTE', '16'),
    ('CHARENTE-MARITIME', '17'),
    ('CORREZE', '19'),
    ('CREUSE', '23'),
    ('DORDOGNE', '24'),
    ('GIRONDE', '33'),
    ('LANDES', '40'),
    ('LOT-ET-GARONNE', '47'),
    ('PYRENEES-ATLANTIQUES', '64'),
    ('DEUX-SEVRES', '79'),
    ('VIENNE', '86'),
    ('HAUTE-VIENNE', '87')
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
            time.sleep(0.3)  # Be respectful of API

        except requests.exceptions.RequestException as e:
            print(f"\n❌ Error fetching data: {e}")
            break

    print(f"\n✓ Fetched {len(all_records)} total records")
    return all_records


def download_ecoles_effectifs():
    """
    Download enrollment data for primary schools (écoles) - NEW regions only
    Includes total students and number of classes!
    """
    print("\n" + "="*80)
    print("1. DOWNLOADING ÉCOLES ENROLLMENT DATA")
    print("="*80)

    # Filter by NEW department names only (Charente-Maritime)
    new_dept_names = [name for name, code in NEW_DEPARTMENTS]
    print(f"\n→ Downloading enrollment for: {', '.join(new_dept_names)}...")
    dept_filter = " OR ".join([f"departement='{dept}'" for dept in new_dept_names])
    records = fetch_paginated_data("fr-en-ecoles-effectifs-nb_classes", filters=dept_filter)

    # Keep most recent year per school
    school_records = {}
    for record in records:
        fields = record.get('record', {}).get('fields', {})
        uai = fields.get('numero_ecole')
        rentree = fields.get('rentree_scolaire', '')

        if uai:
            if uai not in school_records or rentree > school_records[uai].get('record', {}).get('fields', {}).get('rentree_scolaire', ''):
                school_records[uai] = record

    latest_records = list(school_records.values())
    print(f"\n✓ Filtered to {len(latest_records)} schools (most recent year)")

    # Merge with existing and save
    combined = save_and_merge("effectifs_ecoles_pays_loire.json", latest_records, key_field='numero_ecole')
    print(f"✓ Total écoles enrollment across all regions: {len(combined)}")
    print(f"✓ Saved to {DATA_DIR / 'effectifs_ecoles_pays_loire.json'}")
    return combined


def download_colleges_effectifs():
    """
    Download enrollment data for collèges - NEW regions only
    """
    print("\n" + "="*80)
    print("2. DOWNLOADING COLLÈGES ENROLLMENT DATA")
    print("="*80)

    # Filter by NEW department codes only (Charente-Maritime)
    new_dept_codes = [code for name, code in NEW_DEPARTMENTS]
    print(f"\n→ Downloading enrollment for departments: {', '.join(new_dept_codes)}...")
    dept_filter = " OR ".join([f"code_dept='{code}'" for code in new_dept_codes])
    records = fetch_paginated_data("fr-en-college-effectifs-niveau-sexe-lv", filters=dept_filter)

    # Keep most recent year per school
    school_records = {}
    for record in records:
        fields = record.get('record', {}).get('fields', {})
        uai = fields.get('numero_college')
        rentree = fields.get('rentree_scolaire', '')

        if uai:
            if uai not in school_records or rentree > school_records[uai].get('record', {}).get('fields', {}).get('rentree_scolaire', ''):
                school_records[uai] = record

    latest_records = list(school_records.values())
    print(f"\n✓ Filtered to {len(latest_records)} collèges (most recent year)")

    # Merge with existing and save
    combined = save_and_merge("effectifs_colleges_pays_loire.json", latest_records, key_field='numero_college')
    print(f"✓ Total collèges enrollment across all regions: {len(combined)}")
    print(f"✓ Saved to {DATA_DIR / 'effectifs_colleges_pays_loire.json'}")
    return combined


def download_lycees_effectifs():
    """
    Download enrollment data for lycées (general only) - NEW regions only
    """
    print("\n" + "="*80)
    print("3. DOWNLOADING LYCÉES ENROLLMENT DATA")
    print("="*80)

    # Filter by NEW department codes only (Charente-Maritime)
    new_dept_codes = [code for name, code in NEW_DEPARTMENTS]
    print(f"\n→ Downloading enrollment for departments: {', '.join(new_dept_codes)}...")
    dept_filter = " OR ".join([f"code_departement_pays='{code}'" for code in new_dept_codes])
    records = fetch_paginated_data("fr-en-lycee_gt-effectifs-niveau-sexe-lv", filters=dept_filter)

    # Keep only most recent year per school (data already aggregated by year)
    school_data = {}
    for record in records:
        fields = record.get('record', {}).get('fields', {})
        uai = fields.get('numero_lycee')
        rentree = fields.get('rentree_scolaire', '')

        if not uai:
            continue

        # Keep most recent year only
        if uai not in school_data or rentree > school_data[uai]['rentree']:
            school_data[uai] = {
                'uai': uai,
                'name': fields.get('denomination_principale', ''),
                'rentree': rentree,
                'total_students': fields.get('nombre_d_eleves', 0) or 0
            }

    aggregated_records = list(school_data.values())
    print(f"\n✓ Filtered to {len(aggregated_records)} lycées (most recent year)")

    # Merge with existing and save
    combined = save_and_merge("effectifs_lycees_pays_loire.json", aggregated_records, key_field='uai')
    print(f"✓ Total lycées enrollment across all regions: {len(combined)}")
    print(f"✓ Saved to {DATA_DIR / 'effectifs_lycees_pays_loire.json'}")
    return combined


def main():
    """
    Download enrollment data for NEW regions and merge with existing
    """
    print("\n" + "="*80)
    print("DOWNLOADING ENROLLMENT DATA - ADDING NEW REGIONS")
    print("New region: Nouvelle-Aquitaine (Charente-Maritime)")
    print("="*80)

    ecoles = download_ecoles_effectifs()
    colleges = download_colleges_effectifs()
    lycees = download_lycees_effectifs()

    print("\n" + "="*80)
    print("DOWNLOAD & MERGE COMPLETE")
    print("="*80)
    print(f"\nTotal after merge:")
    print(f"  - {len(ecoles)} primary schools with enrollment data")
    print(f"  - {len(colleges)} collèges with enrollment data")
    print(f"  - {len(lycees)} lycées with enrollment data")
    print(f"\nNext step: Run merge_datasets.py again to integrate enrollment data")
    print()


if __name__ == '__main__':
    main()
