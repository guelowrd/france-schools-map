#!/usr/bin/env python3
"""
Download political data for Pays de la Loire communes

Downloads:
- Current mayors from RNE API (Opendatasoft)
- Municipal 2020 election results from data.gouv.fr
- Presidential 2022 election results from data.gouv.fr
- Legislative 2024 election results from data.gouv.fr
- INSEE commune code mappings from geo.api.gouv.fr

Outputs merged political_data.json keyed by INSEE commune code
"""

import json
import time
import requests
import csv
import io
from pathlib import Path
from collections import defaultdict

# Configuration
CACHE_DIR = Path(__file__).parent.parent / "data" / "political_cache"
CACHE_DIR.mkdir(exist_ok=True)

SCHOOLS_FILE = Path(__file__).parent.parent / "data" / "schools.json"
DEPARTMENTS = ["44", "49", "53", "72", "85"]  # Pays de la Loire

# Rate limiting
REQUEST_DELAY = 0.022  # seconds between requests (~45 req/sec, within 50 req/sec limit)


def build_insee_mapping():
    """Build postal code → INSEE code mapping using geo.api.gouv.fr"""
    print("\n" + "="*80)
    print("BUILDING INSEE CODE MAPPING")
    print("="*80)

    # Load schools to get all postal codes and cities
    with open(SCHOOLS_FILE) as f:
        schools = json.load(f)

    print(f"Loaded {len(schools)} schools")

    # Collect unique postal code + city combinations
    locations = set()
    for school in schools:
        postal_code = school.get('address', {}).get('postal_code')
        city = school.get('address', {}).get('city')
        if postal_code and city:
            locations.add((postal_code, city))

    print(f"Found {len(locations)} unique postal code + city combinations")

    mapping = {}
    success = 0
    failed = []

    for postal_code, city in sorted(locations):
        print(f"  Querying {postal_code} ({city})...", end=' ')

        try:
            url = f"https://geo.api.gouv.fr/communes?codePostal={postal_code}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            communes = response.json()

            if len(communes) == 1:
                # Single commune for this postal code
                insee_code = communes[0]['code']
                commune_name = communes[0]['nom']
                mapping[f"{postal_code}|{city}"] = {
                    'insee_code': insee_code,
                    'commune_name': commune_name
                }
                print(f"✓ {insee_code} ({commune_name})")
                success += 1
            elif len(communes) > 1:
                # Multiple communes - match by city name
                matched = False
                for commune in communes:
                    if commune['nom'].lower() == city.lower():
                        insee_code = commune['code']
                        commune_name = commune['nom']
                        mapping[f"{postal_code}|{city}"] = {
                            'insee_code': insee_code,
                            'commune_name': commune_name
                        }
                        print(f"✓ {insee_code} ({commune_name}) [matched by name]")
                        success += 1
                        matched = True
                        break

                if not matched:
                    # Use first commune as fallback
                    insee_code = communes[0]['code']
                    commune_name = communes[0]['nom']
                    mapping[f"{postal_code}|{city}"] = {
                        'insee_code': insee_code,
                        'commune_name': commune_name
                    }
                    print(f"⚠ {insee_code} ({commune_name}) [fallback, {len(communes)} options]")
                    success += 1
            else:
                print("✗ No communes found")
                failed.append(f"{postal_code}|{city}")

            time.sleep(REQUEST_DELAY)

        except Exception as e:
            print(f"✗ Error: {str(e)}")
            failed.append(f"{postal_code}|{city}")
            time.sleep(REQUEST_DELAY)

    print(f"\n✓ Successfully mapped {success}/{len(locations)} locations")
    if failed:
        print(f"✗ Failed to map {len(failed)} locations:")
        for loc in failed[:10]:
            print(f"  - {loc}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")

    # Save mapping
    output_file = CACHE_DIR / "insee_mapping.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved INSEE mapping to {output_file}")
    return mapping


def download_mayors():
    """Download current mayors from RNE CSV export via Opendatasoft"""
    print("\n" + "="*80)
    print("DOWNLOADING CURRENT MAYORS")
    print("="*80)

    mayors = {}

    # CSV export URL from Opendatasoft
    csv_url = "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/donnees-du-repertoire-national-des-elus/exports/csv/?delimiters=%3B&lang=en&timezone=UTC&use_labels=true"

    print("Downloading full RNE CSV export...")
    print("  This may take a minute (large file)...")

    try:
        response = requests.get(csv_url, timeout=300)
        response.raise_for_status()
        response.encoding = 'utf-8'

        print("  ✓ Downloaded CSV, parsing...")

        # Remove BOM if present at the start of the file
        text_content = response.text
        if text_content.startswith('\ufeff'):
            text_content = text_content[1:]

        # Parse CSV
        reader = csv.DictReader(io.StringIO(text_content), delimiter=';')

        total_processed = 0
        mayors_found = 0
        for row in reader:
            total_processed += 1

            # Filter for mayors only - EXACT match required
            function_name = row.get('Nom de la fonction', '').strip()

            # Check if this is a mayor (Maire) - EXACT match, not adjoint/deputy
            if function_name != 'Maire':
                continue

            # Get commune code
            com_code = row.get('Code de la commune', '').strip()
            dept_code = row.get('Code du département', '').strip()

            # Filter for our 5 departments (Pays de la Loire)
            if dept_code in DEPARTMENTS and com_code:
                mayors[com_code] = {
                    'first_name': row.get('Prénom de l\'élu·e', '').strip(),
                    'last_name': row.get('Nom de l\'élu·e', '').strip(),
                    'party': None  # Will be filled from municipal_2020 data
                }
                mayors_found += 1

            if total_processed % 50000 == 0:
                print(f"  Processed {total_processed} records, found {mayors_found} Pays de la Loire mayors...")

        print(f"\n✓ Processed {total_processed} total records")
        print(f"✓ Found {len(mayors)} mayors from Pays de la Loire")

        # Show breakdown by department
        by_dept = {}
        for insee in mayors:
            dept = insee[:2]
            by_dept[dept] = by_dept.get(dept, 0) + 1
        print(f"  By department: {sorted(by_dept.items())}")

    except Exception as e:
        print(f"✗ Error downloading mayors: {str(e)}")

    # Save mayors
    output_file = CACHE_DIR / "mayors.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mayors, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved mayors data to {output_file}")
    return mayors


def download_municipal_2020():
    """Download Municipal 2020 2nd round results from data.gouv.fr"""
    print("\n" + "="*80)
    print("DOWNLOADING MUNICIPAL 2020 RESULTS")
    print("="*80)

    municipal = {}

    # Municipal 2020 2nd round - two files for different commune sizes
    urls = [
        'https://www.data.gouv.fr/api/1/datasets/r/7a5faf5f-7e3b-4de6-9f1d-a8e3ad176476',  # < 1000 inhabitants (TXT)
        'https://www.data.gouv.fr/api/1/datasets/r/e7cae0aa-5e36-4370-b724-6f233014d0d6'   # >= 1000 inhabitants (TXT)
    ]

    for idx, url in enumerate(urls):
        file_type = "< 1000 inhabitants" if idx == 0 else ">= 1000 inhabitants"
        print(f"\nDownloading {file_type}...")

        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            response.encoding = 'latin-1'  # French gov files use latin-1

            # Parse CSV (semicolon-separated, not tab)
            reader = csv.DictReader(io.StringIO(response.text), delimiter=';')

            for row in reader:
                code_departement = row.get('Code du département', '').strip()
                code_commune = row.get('Code de la commune', '').strip()

                # Filter for Pays de la Loire departments
                if code_departement not in DEPARTMENTS:
                    continue

                # Build INSEE code (department + commune)
                insee_code = code_departement + code_commune

                # Extract winning list data (liste with highest % wins)
                libelle_liste = row.get('Libellé de liste', '').strip()
                nuance_liste = row.get('Libellé de la nuance de la liste', '').strip()
                voix = row.get('Voix', '').strip()
                exprimes = row.get('Exprimés', '').strip()

                if voix and exprimes and int(exprimes) > 0:
                    percentage = (int(voix) / int(exprimes)) * 100

                    # Keep only the list with highest percentage
                    if insee_code not in municipal or percentage > municipal[insee_code]['percentage']:
                        municipal[insee_code] = {
                            'year': 2020,
                            'round': 2,
                            'winning_list': libelle_liste or nuance_liste or 'Liste inconnue',
                            'percentage': round(percentage, 1),
                            'party': nuance_liste or None
                        }

            print(f"  ✓ Processed {len(municipal)} communes so far")

        except Exception as e:
            print(f"  ✗ Error downloading {file_type}: {str(e)}")

    output_file = CACHE_DIR / "municipal_2020.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(municipal, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved municipal data for {len(municipal)} communes to {output_file}")
    return municipal


def download_presidential_2022():
    """Download Presidential 2022 results (both rounds) from data.gouv.fr"""
    print("\n" + "="*80)
    print("DOWNLOADING PRESIDENTIAL 2022 RESULTS")
    print("="*80)

    presidential = {}

    # Round 1 and Round 2 URLs (TXT format, sub-commune level)
    # These are large files that include all polling station data, which we'll aggregate by commune
    urls = {
        'round_1': 'https://www.data.gouv.fr/api/1/datasets/r/68b19a8d-5921-4d49-a0c7-b9241ddce9e6',  # Round 1 TXT
        'round_2': 'https://www.data.gouv.fr/api/1/datasets/r/c700bcf1-5d88-4da6-b998-094587a90444'   # Round 2 XLSX - will try as CSV
    }

    for round_name, url in urls.items():
        print(f"\nDownloading {round_name}...")

        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            response.encoding = 'latin-1'  # French gov files use latin-1

            # Parse CSV (semicolon-separated for French data)
            # Filter out NUL bytes if present
            text_content = response.text.replace('\x00', '')
            reader = csv.DictReader(io.StringIO(text_content), delimiter=';')

            # Aggregate votes by commune
            commune_votes = defaultdict(lambda: defaultdict(int))
            commune_totals = defaultdict(int)

            for row in reader:
                code_departement = row.get('Code du département', '').strip()
                code_commune = row.get('Code de la commune', '').strip()

                # Filter for Pays de la Loire departments
                if code_departement not in DEPARTMENTS:
                    continue

                insee_code = code_departement + code_commune

                # Get candidate info
                nom = row.get('Nom', '').strip()
                prenom = row.get('Prénom', '').strip()
                voix = row.get('Voix', '').strip()
                exprimes = row.get('Exprimés', '').strip()

                if voix and nom:
                    candidate_name = f"{prenom} {nom}".strip() if prenom else nom
                    commune_votes[insee_code][candidate_name] += int(voix)

                if exprimes:
                    commune_totals[insee_code] += int(exprimes)

            # Calculate percentages and store top 4
            for insee_code in commune_votes:
                total = commune_totals[insee_code]
                if total == 0:
                    continue

                # Calculate percentages for each candidate
                candidates = []
                for candidate, votes in commune_votes[insee_code].items():
                    percentage = (votes / total) * 100
                    candidates.append({
                        'candidate': candidate,
                        'percentage': round(percentage, 1)
                    })

                # Sort by percentage descending
                candidates.sort(key=lambda x: x['percentage'], reverse=True)

                # Initialize if needed
                if insee_code not in presidential:
                    presidential[insee_code] = {}

                if round_name == 'round_1':
                    # Store top 4 candidates
                    presidential[insee_code]['round_1'] = candidates[:4]
                else:
                    # Round 2: store Macron vs Le Pen
                    if len(candidates) >= 2:
                        presidential[insee_code]['round_2'] = {
                            'macron': candidates[0]['percentage'] if 'Macron' in candidates[0]['candidate'] else candidates[1]['percentage'],
                            'le_pen': candidates[1]['percentage'] if 'Macron' in candidates[0]['candidate'] else candidates[0]['percentage']
                        }

            print(f"  ✓ Processed {len(commune_votes)} communes for {round_name}")

        except Exception as e:
            print(f"  ✗ Error downloading {round_name}: {str(e)}")

    output_file = CACHE_DIR / "presidential_2022.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(presidential, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved presidential data for {len(presidential)} communes to {output_file}")
    return presidential


def download_legislative_2024():
    """Download Legislative 2024 results (both rounds) from data.gouv.fr"""
    print("\n" + "="*80)
    print("DOWNLOADING LEGISLATIVE 2024 RESULTS")
    print("="*80)

    legislative = {}

    # Round 1 and Round 2 URLs (CSV format, commune level)
    urls = {
        'round_1': 'https://www.data.gouv.fr/api/1/datasets/r/bd32fcd3-53df-47ac-bf1d-8d8003fe23a1',
        'round_2': 'https://www.data.gouv.fr/api/1/datasets/r/5a8088fd-8168-402a-9f40-c48daab88cd1'
    }

    for round_name, url in urls.items():
        print(f"\nDownloading {round_name}...")

        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            response.encoding = 'latin-1'  # French gov files use latin-1

            # Parse CSV (semicolon-separated)
            reader = csv.DictReader(io.StringIO(response.text), delimiter=';')

            # Group by commune
            commune_candidates = defaultdict(list)

            for row in reader:
                code_departement = row.get('Code du département', '').strip()
                code_commune = row.get('Code de la commune', '').strip()

                # Filter for Pays de la Loire departments
                if code_departement not in DEPARTMENTS:
                    continue

                insee_code = code_departement + code_commune

                # Get candidate info
                nom = row.get('Nom', '').strip()
                prenom = row.get('Prénom', '').strip()
                nuance = row.get('Libellé de la nuance', '').strip()
                voix = row.get('Voix', '').strip()
                exprimes = row.get('Exprimés', '').strip()

                if voix and exprimes and nom:
                    votes = int(voix)
                    total_exprimes = int(exprimes)

                    if total_exprimes > 0:
                        percentage = (votes / total_exprimes) * 100
                        candidate_name = f"{prenom} {nom}".strip() if prenom else nom

                        commune_candidates[insee_code].append({
                            'candidate': candidate_name,
                            'party': nuance or 'Divers',
                            'percentage': round(percentage, 1),
                            'votes': votes
                        })

            # For each commune, sort candidates by votes and keep top 4
            for insee_code, candidates in commune_candidates.items():
                # Sort by votes descending
                candidates.sort(key=lambda x: x['votes'], reverse=True)

                # Initialize if needed
                if insee_code not in legislative:
                    legislative[insee_code] = {}

                # Store top 4 candidates (without vote counts in final data)
                top_candidates = [
                    {
                        'candidate': c['candidate'],
                        'party': c['party'],
                        'percentage': c['percentage']
                    }
                    for c in candidates[:4]
                ]

                legislative[insee_code][round_name] = top_candidates

            print(f"  ✓ Processed {len(commune_candidates)} communes for {round_name}")

        except Exception as e:
            print(f"  ✗ Error downloading {round_name}: {str(e)}")

    output_file = CACHE_DIR / "legislative_2024.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(legislative, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved legislative data for {len(legislative)} communes to {output_file}")
    return legislative


def merge_political_data():
    """Merge all political data sources by INSEE code"""
    print("\n" + "="*80)
    print("MERGING POLITICAL DATA")
    print("="*80)

    # Load all data sources
    print("Loading data sources...")

    with open(CACHE_DIR / "insee_mapping.json") as f:
        insee_mapping = json.load(f)

    with open(CACHE_DIR / "mayors.json") as f:
        mayors = json.load(f)

    with open(CACHE_DIR / "municipal_2020.json") as f:
        municipal = json.load(f)

    with open(CACHE_DIR / "presidential_2022.json") as f:
        presidential = json.load(f)

    with open(CACHE_DIR / "legislative_2024.json") as f:
        legislative = json.load(f)

    print(f"  INSEE mapping: {len(insee_mapping)} entries")
    print(f"  Mayors: {len(mayors)} communes")
    print(f"  Municipal 2020: {len(municipal)} communes")
    print(f"  Presidential 2022: {len(presidential)} communes")
    print(f"  Legislative 2024: {len(legislative)} communes")

    # Collect all unique INSEE codes
    all_insee_codes = set()

    # Add INSEE codes from mapping
    for mapping_data in insee_mapping.values():
        all_insee_codes.add(mapping_data['insee_code'])

    # Add INSEE codes from other sources
    all_insee_codes.update(mayors.keys())
    all_insee_codes.update(municipal.keys())
    all_insee_codes.update(presidential.keys())
    all_insee_codes.update(legislative.keys())

    print(f"\nMerging data for {len(all_insee_codes)} unique communes...")

    # Merge data
    political_data = {}

    for insee_code in all_insee_codes:
        # Find commune name from mapping or mayors
        commune_name = None
        for mapping_data in insee_mapping.values():
            if mapping_data['insee_code'] == insee_code:
                commune_name = mapping_data['commune_name']
                break

        if not commune_name and insee_code in mayors:
            # Try to infer from INSEE code (not ideal but fallback)
            commune_name = f"Commune {insee_code}"

        if commune_name:
            # Get mayor info and merge party from municipal data
            mayor_info = mayors.get(insee_code)
            if mayor_info and insee_code in municipal:
                # Add party from municipal election results
                mayor_info = mayor_info.copy()
                mayor_info['party'] = municipal[insee_code].get('party', 'N/A')

            political_data[insee_code] = {
                'commune_name': commune_name,
                'insee_code': insee_code,
                'mayor': mayor_info,
                'municipal_2020': municipal.get(insee_code),
                'presidential_2022': presidential.get(insee_code),
                'legislative_2024': legislative.get(insee_code)
            }

    print(f"✓ Merged {len(political_data)} communes with political data")

    # Statistics
    with_mayor = sum(1 for v in political_data.values() if v.get('mayor'))
    with_municipal = sum(1 for v in political_data.values() if v.get('municipal_2020'))
    with_presidential = sum(1 for v in political_data.values() if v.get('presidential_2022'))
    with_legislative = sum(1 for v in political_data.values() if v.get('legislative_2024'))

    print(f"\nCoverage:")
    print(f"  Mayors: {with_mayor}/{len(political_data)} ({100*with_mayor/len(political_data):.1f}%)")
    print(f"  Municipal 2020: {with_municipal}/{len(political_data)} ({100*with_municipal/len(political_data) if political_data else 0:.1f}%)")
    print(f"  Presidential 2022: {with_presidential}/{len(political_data)} ({100*with_presidential/len(political_data) if political_data else 0:.1f}%)")
    print(f"  Legislative 2024: {with_legislative}/{len(political_data)} ({100*with_legislative/len(political_data) if political_data else 0:.1f}%)")

    # Save merged data
    output_file = CACHE_DIR / "political_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(political_data, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved merged political data to {output_file}")

    return political_data


def main():
    """Main execution"""
    print("="*80)
    print("POLITICAL DATA DOWNLOAD - PAYS DE LA LOIRE")
    print("="*80)

    start_time = time.time()

    # Step 1: Build INSEE mapping
    print("\n[1/6] Building INSEE code mapping...")
    insee_mapping = build_insee_mapping()

    # Step 2: Download mayors
    print("\n[2/6] Downloading current mayors...")
    mayors = download_mayors()

    # Step 3: Download municipal results
    print("\n[3/6] Downloading Municipal 2020 results...")
    municipal = download_municipal_2020()

    # Step 4: Download presidential results
    print("\n[4/6] Downloading Presidential 2022 results...")
    presidential = download_presidential_2022()

    # Step 5: Download legislative results
    print("\n[5/6] Downloading Legislative 2024 results...")
    legislative = download_legislative_2024()

    # Step 6: Merge all data
    print("\n[6/6] Merging all political data...")
    political_data = merge_political_data()

    elapsed = time.time() - start_time

    print("\n" + "="*80)
    print("DOWNLOAD COMPLETE")
    print("="*80)
    print(f"Total time: {elapsed:.1f} seconds")
    print(f"Political data cached in: {CACHE_DIR}")
    print(f"\nNext step: Copy political_data.json to frontend/data/")
    print(f"  cp {CACHE_DIR / 'political_data.json'} frontend/data/")


if __name__ == "__main__":
    main()
