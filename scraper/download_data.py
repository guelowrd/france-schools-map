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

# Pays de la Loire region
REGION_NAME = "Pays de la Loire"
REGION_NAME_UPPER = "PAYS DE LA LOIRE"  # For IPS datasets (uppercase)
REGION_CODE = "52"  # Code région for Pays de la Loire
DEPARTMENT_CODES = ['044', '049', '053', '072', '085']  # Loire-Atlantique, Maine-et-Loire, Mayenne, Sarthe, Vendée
DEPARTMENT_CODES_SHORT = ['44', '49', '53', '72', '85']  # Without leading zeros

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


def download_annuaire():
    """
    Download education directory for Pays de la Loire
    Filter to general curriculum only:
    - Écoles élémentaires (keep)
    - Collèges (keep all)
    - Lycées généraux et technologiques (keep)
    - Exclude: Lycées professionnels only, CFA, etc.
    """
    print("\n" + "="*80)
    print("1. DOWNLOADING ANNUAIRE (Education Directory)")
    print("="*80)

    filters = f"libelle_region='{REGION_NAME}'"
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

        # Keep lycées but filter out professional-only
        elif 'Lycée' in type_etab or 'LYCEE' in libelle_nature.upper():
            # Check for general/technological indicators
            voie_generale = fields.get('voie_generale')
            voie_techno = fields.get('voie_technologique')
            voie_pro = fields.get('voie_professionnelle')

            # Keep if has general OR technological track
            # (even if also has professional - polyvalent lycées are OK)
            if voie_generale or voie_techno:
                filtered_records.append(record)
            # Also keep if voie fields are None (data not specified) - safer to include
            elif voie_generale is None and voie_techno is None and voie_pro is None:
                # Check libelle to exclude obvious professional-only
                if 'PROFESSIONNEL' not in libelle_nature.upper():
                    filtered_records.append(record)

    print(f"\n✓ Filtered to {len(filtered_records)} general curriculum schools")
    print(f"  (from {len(records)} total establishments)")

    # Save to file
    output_file = DATA_DIR / "annuaire_pays_loire.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_records, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved to {output_file}")
    return filtered_records


def download_ips_ecoles():
    """
    Download IPS data for primary schools in Pays de la Loire
    """
    print("\n" + "="*80)
    print("2. DOWNLOADING IPS ÉCOLES (Primary Schools Social Index)")
    print("="*80)

    filters = f"region='{REGION_NAME_UPPER}'"
    records = fetch_paginated_data("fr-en-ips-ecoles-ap2022", filters=filters)

    # Save to file
    output_file = DATA_DIR / "ips_ecoles_pays_loire.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved to {output_file}")
    return records


def download_ips_colleges():
    """
    Download IPS data for middle schools (collèges) in Pays de la Loire
    Filter by department codes since region filter doesn't work for this dataset
    """
    print("\n" + "="*80)
    print("3. DOWNLOADING IPS COLLÈGES (Middle Schools Social Index)")
    print("="*80)

    # Filter by department codes (more reliable than region name)
    dept_filter = " OR ".join([f"code_du_departement='{code}'" for code in DEPARTMENT_CODES_SHORT])
    records = fetch_paginated_data("fr-en-ips-colleges-ap2023", filters=dept_filter)

    # Save to file
    output_file = DATA_DIR / "ips_colleges_pays_loire.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved to {output_file}")
    return records


def download_ips_lycees():
    """
    Download IPS data for high schools (lycées) in Pays de la Loire
    Filter by department codes since region filter doesn't work for this dataset
    """
    print("\n" + "="*80)
    print("4. DOWNLOADING IPS LYCÉES (High Schools Social Index)")
    print("="*80)

    # Filter by department codes (more reliable than region name)
    dept_filter = " OR ".join([f"code_du_departement='{code}'" for code in DEPARTMENT_CODES_SHORT])
    records = fetch_paginated_data("fr-en-ips-lycees-ap2023", filters=dept_filter)

    # Save to file
    output_file = DATA_DIR / "ips_lycees_pays_loire.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved to {output_file}")
    return records


def download_brevet_results():
    """
    Download Brevet exam results for collèges in Pays de la Loire
    Get most recent year only
    """
    print("\n" + "="*80)
    print("5. DOWNLOADING BREVET RESULTS (Middle School Exams)")
    print("="*80)

    # Filter by department codes
    dept_filter = " OR ".join([f"code_departement='{code}'" for code in DEPARTMENT_CODES])
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

    # Save to file
    output_file = DATA_DIR / "brevet_results_pays_loire.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(latest_records, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved to {output_file}")
    return latest_records


def download_bac_results():
    """
    Download Baccalauréat results for lycées in Pays de la Loire
    Get most recent year only, general & technological track only
    """
    print("\n" + "="*80)
    print("6. DOWNLOADING BAC RESULTS (High School Exams)")
    print("="*80)

    # Filter by department codes (use short codes without leading zeros)
    dept_filter = " OR ".join([f"code_departement='{code}'" for code in DEPARTMENT_CODES_SHORT])
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

    # Save to file
    output_file = DATA_DIR / "bac_results_pays_loire.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(latest_records, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved to {output_file}")
    return latest_records


def main():
    """
    Download all datasets for Pays de la Loire
    """
    print("\n" + "="*80)
    print("DOWNLOADING EDUCATION DATA FOR PAYS DE LA LOIRE")
    print("Region: Pays de la Loire")
    print("Scope: General curriculum only (Écoles, Collèges, Lycées GT)")
    print("="*80)

    # Download all datasets
    annuaire = download_annuaire()
    ips_ecoles = download_ips_ecoles()
    ips_colleges = download_ips_colleges()
    ips_lycees = download_ips_lycees()
    brevet = download_brevet_results()
    bac = download_bac_results()

    print("\n" + "="*80)
    print("DOWNLOAD COMPLETE")
    print("="*80)
    print(f"\nDownloaded:")
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
