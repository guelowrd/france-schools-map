#!/usr/bin/env python3
"""
Explore data.education.gouv.fr API to understand available data
for Pays de la Loire schools
"""

import requests
import json
from collections import Counter


# API base URL
BASE_URL = "https://data.education.gouv.fr/api/v2/catalog/datasets"

# Pays de la Loire department codes
PAYS_LOIRE_DEPARTMENTS = ['44', '49', '53', '72', '85']  # Loire-Atlantique, Maine-et-Loire, Mayenne, Sarthe, Vendée


def explore_dataset(dataset_id, name, filters=None, limit=10):
    """Explore a dataset and show sample data"""
    print("="*80)
    print(f"DATASET: {name}")
    print(f"ID: {dataset_id}")
    print("="*80)

    # Build URL
    url = f"{BASE_URL}/{dataset_id}/records"
    params = {
        'limit': limit,
        'offset': 0
    }

    if filters:
        params['where'] = filters

    try:
        print(f"Fetching {url}...")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Check structure - API uses 'records' key
        if 'records' not in data:
            print(f"⚠️  Unexpected response structure: {list(data.keys())}")
            print(f"Response sample: {json.dumps(data, indent=2)[:500]}")
            return None

        results = data['records']
        total_count = data.get('total_count', len(results))

        print(f"\nTotal records: {total_count}")
        print(f"Sample size: {len(results)}")

        if len(results) > 0:
            # Show field names
            first_record = results[0]
            if 'record' in first_record:
                fields = first_record['record'].get('fields', {})
            else:
                fields = first_record.get('fields', {})

            print(f"\nAvailable fields ({len(fields)}):")
            for field_name in sorted(fields.keys()):
                value = fields[field_name]
                value_str = str(value)[:50]
                print(f"  - {field_name}: {value_str}")

            # Show first record
            print(f"\nFirst record example:")
            print(json.dumps(first_record, indent=2, ensure_ascii=False)[:1000])

        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data: {e}")
        return None
    except Exception as e:
        print(f"❌ Error processing data: {e}")
        return None


def main():
    """Explore key datasets for Pays de la Loire schools"""

    print("\n" + "="*80)
    print("EXPLORING FRENCH EDUCATION DATA SOURCES")
    print("Region: Pays de la Loire")
    print("="*80)
    print()

    # 1. Education Directory (Annuaire)
    print("\n\n1. EDUCATION DIRECTORY (ANNUAIRE)")
    print("-"*80)
    explore_dataset(
        "fr-en-annuaire-education",
        "Annuaire de l'Éducation",
        filters="libelle_region='Pays de la Loire'",
        limit=5
    )

    # 2. IPS for Primary Schools
    print("\n\n2. IPS - PRIMARY SCHOOLS (ÉCOLES)")
    print("-"*80)
    explore_dataset(
        "fr-en-ips-ecoles-ap2022",
        "IPS des écoles (à partir de 2022)",
        limit=5
    )

    # 3. IPS for Collèges
    print("\n\n3. IPS - MIDDLE SCHOOLS (COLLÈGES)")
    print("-"*80)
    explore_dataset(
        "fr-en-ips-colleges-ap2023",
        "IPS des collèges (à partir de 2023)",
        limit=5
    )

    # 4. IPS for Lycées
    print("\n\n4. IPS - HIGH SCHOOLS (LYCÉES)")
    print("-"*80)
    explore_dataset(
        "fr-en-ips-lycees-ap2023",
        "IPS des lycées (à partir de 2023)",
        limit=5
    )

    # 5. Brevet Results (Middle School)
    print("\n\n5. BREVET RESULTS (COLLÈGES)")
    print("-"*80)
    explore_dataset(
        "fr-en-dnb-par-etablissement",
        "Résultats du Brevet par établissement",
        limit=5
    )

    # 6. Baccalauréat Results (High School)
    print("\n\n6. BACCALAURÉAT RESULTS (LYCÉES)")
    print("-"*80)
    explore_dataset(
        "fr-en-indicateurs-de-resultat-des-lycees-gt_v2",
        "Indicateurs de résultats des lycées (général et technologique)",
        limit=5
    )

    print("\n" + "="*80)
    print("EXPLORATION COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Review field names and data structure")
    print("2. Identify which 'type_etablissement' values to filter")
    print("3. Write download script to fetch all Pays de la Loire schools")
    print("4. Design merge strategy on UAI/RNE")
    print()


if __name__ == '__main__':
    main()
