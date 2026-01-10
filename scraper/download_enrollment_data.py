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

# Pays de la Loire departments
DEPARTMENT_NAMES = ['LOIRE-ATLANTIQUE', 'MAINE-ET-LOIRE', 'MAYENNE', 'SARTHE', 'VENDEE']
DEPARTMENT_CODES_SHORT = ['44', '49', '53', '72', '85']

# Output directory
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


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
    Download enrollment data for primary schools (écoles)
    Includes total students and number of classes!
    """
    print("\n" + "="*80)
    print("1. DOWNLOADING ÉCOLES ENROLLMENT DATA")
    print("="*80)

    # Filter by department names
    dept_filter = " OR ".join([f"departement='{dept}'" for dept in DEPARTMENT_NAMES])
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

    # Save to file
    output_file = DATA_DIR / "effectifs_ecoles_pays_loire.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(latest_records, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved to {output_file}")
    return latest_records


def download_colleges_effectifs():
    """
    Download enrollment data for collèges
    """
    print("\n" + "="*80)
    print("2. DOWNLOADING COLLÈGES ENROLLMENT DATA")
    print("="*80)

    # Filter by department codes
    dept_filter = " OR ".join([f"code_dept='{code}'" for code in DEPARTMENT_CODES_SHORT])
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

    # Save to file
    output_file = DATA_DIR / "effectifs_colleges_pays_loire.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(latest_records, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved to {output_file}")
    return latest_records


def download_lycees_effectifs():
    """
    Download enrollment data for lycées (general & technological)
    """
    print("\n" + "="*80)
    print("3. DOWNLOADING LYCÉES ENROLLMENT DATA")
    print("="*80)

    # Filter by department codes
    dept_filter = " OR ".join([f"code_departement_pays='{code}'" for code in DEPARTMENT_CODES_SHORT])
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

    # Save to file
    output_file = DATA_DIR / "effectifs_lycees_pays_loire.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(aggregated_records, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved to {output_file}")
    return aggregated_records


def main():
    """
    Download enrollment data for all school types
    """
    print("\n" + "="*80)
    print("DOWNLOADING ENROLLMENT DATA FOR PAYS DE LA LOIRE")
    print("="*80)

    ecoles = download_ecoles_effectifs()
    colleges = download_colleges_effectifs()
    lycees = download_lycees_effectifs()

    print("\n" + "="*80)
    print("DOWNLOAD COMPLETE")
    print("="*80)
    print(f"\nDownloaded:")
    print(f"  - {len(ecoles)} primary schools with enrollment data")
    print(f"  - {len(colleges)} collèges with enrollment data")
    print(f"  - {len(lycees)} lycées with enrollment data")
    print(f"\nNext step: Run merge_datasets.py again to integrate enrollment data")
    print()


if __name__ == '__main__':
    main()
