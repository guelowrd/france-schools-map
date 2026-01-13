#!/usr/bin/env python3
"""
Download language offerings data for Pays de la Loire region
"""

import requests
import json
import time
from pathlib import Path

# API base URL
BASE_URL = "https://data.education.gouv.fr/api/v2/catalog/datasets"

# Regions configuration
REGIONS = [
    "Pays de la Loire",  # Existing - don't re-download
    "Nouvelle-Aquitaine"  # NEW - download only this
]

# NEW region to download
NEW_REGION = "Nouvelle-Aquitaine"

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

    # Index existing by key (handle both flat and nested structures)
    existing_by_key = {}
    for record in existing_records:
        # Try flat structure first
        key = record.get(key_field)
        if not key:
            # Try nested structure
            fields = record.get('record', {}).get('fields', {})
            key = fields.get(key_field)
        if key:
            existing_by_key[key] = record

    # Merge new records (overwrites existing with same key)
    for record in new_records:
        # Try flat structure first
        key = record.get(key_field)
        if not key:
            # Try nested structure
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


def download_language_offerings():
    """
    Download language offerings for collèges and lycées - NEW regions only
    """
    print("\n" + "="*80)
    print("DOWNLOADING LANGUAGE OFFERINGS DATA")
    print("="*80)

    # Only download NEW region (Charente-Maritime)
    print(f"\n→ Downloading language offerings for {NEW_REGION}...")
    filters = f"region='{NEW_REGION}'"
    records = fetch_paginated_data("fr-en-offre-langues-2d", filters=filters)

    # Group by UAI to consolidate languages per school
    school_languages = {}

    for record in records:
        fields = record.get('record', {}).get('fields', {})
        uai = fields.get('uai')
        langue = fields.get('langues')
        enseignement = fields.get('enseignements')  # LV1 or LV2

        if not uai or not langue:
            continue

        if uai not in school_languages:
            school_languages[uai] = {
                'uai': uai,
                'lv1': [],
                'lv2': [],
                'all_languages': []
            }

        # Add to appropriate list
        if langue not in school_languages[uai]['all_languages']:
            school_languages[uai]['all_languages'].append(langue)

        if enseignement == 'LV1' and langue not in school_languages[uai]['lv1']:
            school_languages[uai]['lv1'].append(langue)
        elif enseignement == 'LV2' and langue not in school_languages[uai]['lv2']:
            school_languages[uai]['lv2'].append(langue)

    # Convert to list
    new_language_data = list(school_languages.values())

    print(f"\n✓ Processed language data for {len(new_language_data)} schools")

    # Merge with existing and save
    combined = save_and_merge("language_offerings_pays_loire.json", new_language_data, key_field='uai')
    print(f"✓ Total language offerings across all regions: {len(combined)}")
    print(f"✓ Saved to {DATA_DIR / 'language_offerings_pays_loire.json'}")

    # Print some stats for combined data
    schools_with_lv1 = sum(1 for s in combined if s.get('lv1'))
    schools_with_lv2 = sum(1 for s in combined if s.get('lv2'))

    # Count language distribution
    all_lv1_langs = []
    all_lv2_langs = []
    for school in combined:
        all_lv1_langs.extend(school.get('lv1', []))
        all_lv2_langs.extend(school.get('lv2', []))

    from collections import Counter
    lv1_counts = Counter(all_lv1_langs)
    lv2_counts = Counter(all_lv2_langs)

    print(f"\nStatistics:")
    print(f"  Schools with LV1: {schools_with_lv1}")
    print(f"  Schools with LV2: {schools_with_lv2}")
    print(f"\nMost common LV1 languages:")
    for lang, count in lv1_counts.most_common(5):
        print(f"    {lang}: {count} schools")
    print(f"\nMost common LV2 languages:")
    for lang, count in lv2_counts.most_common(5):
        print(f"    {lang}: {count} schools")

    return combined


def main():
    """
    Download language offerings data for NEW regions and merge with existing
    """
    print("\n" + "="*80)
    print("DOWNLOADING LANGUAGE DATA - ADDING NEW REGIONS")
    print("New region: Nouvelle-Aquitaine (Charente-Maritime)")
    print("="*80)

    language_data = download_language_offerings()

    print("\n" + "="*80)
    print("DOWNLOAD & MERGE COMPLETE")
    print("="*80)
    print(f"\nTotal language data for {len(language_data)} schools")
    print(f"\nNext step: Run merge_datasets.py to integrate language data")
    print()


if __name__ == '__main__':
    main()
