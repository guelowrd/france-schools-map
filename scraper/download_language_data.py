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

# Pays de la Loire region
REGION_NAME = "Pays de la Loire"

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
            time.sleep(0.5)  # Be respectful of API

        except requests.exceptions.RequestException as e:
            print(f"\n❌ Error fetching data: {e}")
            break

    print(f"\n✓ Fetched {len(all_records)} total records")
    return all_records


def download_language_offerings():
    """
    Download language offerings for collèges and lycées in Pays de la Loire
    """
    print("\n" + "="*80)
    print("DOWNLOADING LANGUAGE OFFERINGS DATA")
    print("="*80)

    filters = f"region='{REGION_NAME}'"
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
    language_data = list(school_languages.values())

    print(f"\n✓ Processed language data for {len(language_data)} schools")

    # Save to file
    output_file = DATA_DIR / "language_offerings_pays_loire.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(language_data, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved to {output_file}")

    # Print some stats
    schools_with_lv1 = sum(1 for s in language_data if s['lv1'])
    schools_with_lv2 = sum(1 for s in language_data if s['lv2'])

    # Count language distribution
    all_lv1_langs = []
    all_lv2_langs = []
    for school in language_data:
        all_lv1_langs.extend(school['lv1'])
        all_lv2_langs.extend(school['lv2'])

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

    return language_data


def main():
    """
    Download language offerings data
    """
    print("\n" + "="*80)
    print("DOWNLOADING LANGUAGE DATA FOR PAYS DE LA LOIRE")
    print("="*80)

    language_data = download_language_offerings()

    print("\n" + "="*80)
    print("DOWNLOAD COMPLETE")
    print("="*80)
    print(f"\nDownloaded language data for {len(language_data)} schools")
    print(f"\nNext step: Run merge_datasets.py to integrate language data")
    print()


if __name__ == '__main__':
    main()
