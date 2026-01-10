#!/usr/bin/env python3
"""
Merge all education datasets on UAI code
Create final schools.json for frontend map
"""

import json
from pathlib import Path
from collections import defaultdict

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data"


def load_json(filename):
    """Load JSON file"""
    filepath = DATA_DIR / filename
    print(f"Loading {filename}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"  Loaded {len(data)} records")
    return data


def extract_fields(record):
    """Extract fields from API record structure"""
    return record.get('record', {}).get('fields', {})


def categorize_school_type(fields):
    """
    Categorize school into: Primaire, Collège, or Lycée
    """
    type_etab = fields.get('type_etablissement', '')
    libelle_nature = fields.get('libelle_nature', '') or ''

    if 'Ecole' in type_etab or 'ECOLE' in libelle_nature.upper():
        return 'Primaire'
    elif 'Collège' in type_etab or 'COLLEGE' in libelle_nature.upper():
        return 'Collège'
    elif 'Lycée' in type_etab or 'LYCEE' in libelle_nature.upper():
        return 'Lycée'
    else:
        return 'Unknown'


def merge_data():
    """
    Merge all datasets on UAI code
    """
    print("\n" + "="*80)
    print("MERGING DATASETS ON UAI")
    print("="*80)
    print()

    # Load all datasets
    annuaire_records = load_json("annuaire_pays_loire.json")
    ips_ecoles_records = load_json("ips_ecoles_pays_loire.json")
    ips_colleges_records = load_json("ips_colleges_pays_loire.json")
    ips_lycees_records = load_json("ips_lycees_pays_loire.json")
    brevet_records = load_json("brevet_results_pays_loire.json")
    bac_records = load_json("bac_results_pays_loire.json")

    # Load enrollment data (effectifs)
    effectifs_ecoles_records = load_json("effectifs_ecoles_pays_loire.json")
    effectifs_colleges_records = load_json("effectifs_colleges_pays_loire.json")
    effectifs_lycees_records = load_json("effectifs_lycees_pays_loire.json")

    # Create lookup dictionaries by UAI
    print("\nCreating UAI lookup dictionaries...")

    ips_ecoles = {}
    for record in ips_ecoles_records:
        fields = extract_fields(record)
        uai = fields.get('uai')
        if uai:
            # Keep most recent year if multiple records
            rentree = fields.get('rentree_scolaire', '')
            if uai not in ips_ecoles or rentree > ips_ecoles[uai].get('rentree_scolaire', ''):
                ips_ecoles[uai] = fields

    ips_colleges = {}
    for record in ips_colleges_records:
        fields = extract_fields(record)
        uai = fields.get('uai')
        if uai:
            rentree = fields.get('rentree_scolaire', '')
            if uai not in ips_colleges or rentree > ips_colleges[uai].get('rentree_scolaire', ''):
                ips_colleges[uai] = fields

    ips_lycees = {}
    for record in ips_lycees_records:
        fields = extract_fields(record)
        uai = fields.get('uai')
        if uai:
            rentree = fields.get('rentree_scolaire', '')
            if uai not in ips_lycees or rentree > ips_lycees[uai].get('rentree_scolaire', ''):
                ips_lycees[uai] = fields

    brevet_results = {}
    for record in brevet_records:
        fields = extract_fields(record)
        uai = fields.get('numero_d_etablissement')
        if uai:
            brevet_results[uai] = fields

    bac_results = {}
    for record in bac_records:
        fields = extract_fields(record)
        uai = fields.get('uai')
        if uai:
            bac_results[uai] = fields

    print(f"  IPS Écoles: {len(ips_ecoles)} schools")
    print(f"  IPS Collèges: {len(ips_colleges)} schools")
    print(f"  IPS Lycées: {len(ips_lycees)} schools")
    print(f"  Brevet: {len(brevet_results)} schools")
    print(f"  Bac: {len(bac_results)} schools")

    # Create enrollment lookup dictionaries
    effectifs_ecoles = {}
    for record in effectifs_ecoles_records:
        fields = extract_fields(record)
        uai = fields.get('numero_ecole')
        if uai:
            effectifs_ecoles[uai] = fields

    effectifs_colleges = {}
    for record in effectifs_colleges_records:
        fields = extract_fields(record)
        uai = fields.get('numero_college')
        if uai:
            effectifs_colleges[uai] = fields

    effectifs_lycees = {}
    for record in effectifs_lycees_records:
        # This data is aggregated already in the download script
        uai = record.get('uai')
        if uai:
            effectifs_lycees[uai] = record

    print(f"  Effectifs Écoles: {len(effectifs_ecoles)} schools")
    print(f"  Effectifs Collèges: {len(effectifs_colleges)} schools")
    print(f"  Effectifs Lycées: {len(effectifs_lycees)} schools")

    # Merge with annuaire (base dataset)
    print("\nMerging data with Annuaire...")
    merged_schools = []
    stats = {
        'total': 0,
        'with_coordinates': 0,
        'primaire': 0,
        'college': 0,
        'lycee': 0,
        'with_ips': 0,
        'with_exam_results': 0,
        'with_enrollment': 0
    }

    for record in annuaire_records:
        fields = extract_fields(record)
        uai = fields.get('identifiant_de_l_etablissement')

        if not uai:
            continue

        # Get coordinates
        lat = fields.get('latitude')
        lon = fields.get('longitude')

        if not lat or not lon:
            continue  # Skip schools without coordinates

        stats['with_coordinates'] += 1

        # Categorize school type
        school_type = categorize_school_type(fields)

        if school_type == 'Primaire':
            stats['primaire'] += 1
        elif school_type == 'Collège':
            stats['college'] += 1
        elif school_type == 'Lycée':
            stats['lycee'] += 1

        # Build school object
        school = {
            'uai': uai,
            'name': fields.get('nom_etablissement', ''),
            'type': school_type,
            'public_private': fields.get('statut_public_prive', ''),
            'address': {
                'street': fields.get('adresse_1', ''),
                'postal_code': fields.get('code_postal', ''),
                'city': fields.get('nom_commune', ''),
                'department': fields.get('libelle_departement', '')
            },
            'coordinates': {
                'latitude': lat,
                'longitude': lon
            },
            'contact': {
                'phone': fields.get('telephone'),
                'email': fields.get('mail'),
                'website': fields.get('web')
            },
            'student_count': fields.get('nombre_d_eleves'),
        }

        # Add IPS data based on school type
        ips_data = None
        if school_type == 'Primaire' and uai in ips_ecoles:
            ips_data = ips_ecoles[uai]
        elif school_type == 'Collège' and uai in ips_colleges:
            ips_data = ips_colleges[uai]
        elif school_type == 'Lycée' and uai in ips_lycees:
            ips_data = ips_lycees[uai]

        if ips_data:
            stats['with_ips'] += 1
            # Get IPS value based on school type
            ips_value = None
            if school_type == 'Lycée':
                ips_value = ips_data.get('ips_etab')  # Lycées use ips_etab field
            else:
                ips_value = ips_data.get('ips') or ips_data.get('ips_ensemble_gt_pro')

            school['ips'] = {
                'value': ips_value,
                'year': ips_data.get('rentree_scolaire', ''),
                'ecart_type': ips_data.get('ecart_type_de_l_ips') or ips_data.get('ecart_type_etablissement'),
                # Benchmarks for context
                'national_average': ips_data.get('ips_national') or ips_data.get('ips_national_legt'),
                'academique_average': ips_data.get('ips_academique') or ips_data.get('ips_academique_legt'),
                'departemental_average': ips_data.get('ips_departemental') or ips_data.get('ips_departemental_legt')
            }

        # Add enrollment data based on school type
        effectifs_data = None
        if school_type == 'Primaire' and uai in effectifs_ecoles:
            effectifs_data = effectifs_ecoles[uai]
            school['student_count'] = effectifs_data.get('nombre_total_eleves')
            school['number_of_classes'] = effectifs_data.get('nombre_total_classes')
            school['enrollment_year'] = effectifs_data.get('rentree_scolaire')
            # Calculate actual class size for primary schools
            if school['student_count'] and school['number_of_classes'] and school['number_of_classes'] > 0:
                school['class_size'] = round(school['student_count'] / school['number_of_classes'], 1)
            if school['student_count']:
                stats['with_enrollment'] += 1
        elif school_type == 'Collège' and uai in effectifs_colleges:
            effectifs_data = effectifs_colleges[uai]
            school['student_count'] = effectifs_data.get('nombre_eleves_total')
            school['enrollment_year'] = effectifs_data.get('rentree_scolaire')
            if school['student_count']:
                stats['with_enrollment'] += 1
        elif school_type == 'Lycée' and uai in effectifs_lycees:
            effectifs_data = effectifs_lycees[uai]
            school['student_count'] = effectifs_data.get('total_students')
            school['enrollment_year'] = effectifs_data.get('rentree')
            if school['student_count']:
                stats['with_enrollment'] += 1

        # Add exam results based on school type
        if school_type == 'Collège' and uai in brevet_results:
            stats['with_exam_results'] += 1
            brevet = brevet_results[uai]
            taux = brevet.get('taux_de_reussite', '')
            # Parse "94,20%" to float
            success_rate = None
            if taux:
                try:
                    success_rate = float(taux.replace(',', '.').replace('%', ''))
                except:
                    pass

            school['exam_results'] = {
                'type': 'Brevet',
                'year': brevet.get('session', ''),
                'success_rate': success_rate,
                'students_registered': brevet.get('inscrits'),
                'students_present': brevet.get('presents'),
                'students_admitted': brevet.get('admis'),
                'mentions': {
                    'sans_mention': brevet.get('admis_sans_mention'),
                    'assez_bien': brevet.get('nombre_d_admis_mention_ab'),
                    'bien': brevet.get('admis_mention_bien'),
                    'tres_bien': brevet.get('admis_mention_tres_bien')
                }
            }

        elif school_type == 'Lycée' and uai in bac_results:
            stats['with_exam_results'] += 1
            bac = bac_results[uai]
            school['exam_results'] = {
                'type': 'Baccalauréat',
                'year': bac.get('annee', ''),
                'success_rate': bac.get('taux_reu_total'),
                # Access rates (key metric for student well-being!)
                'access_rate_2nde': bac.get('taux_acces_2nde'),  # % who start in 2nde and reach Terminale
                'access_rate_1ere': bac.get('taux_acces_1ere'),  # % who start in 1ere and reach Terminale
                'access_rate_term': bac.get('taux_acces_term'),  # % who start in Term and pass Bac
                # Value added (performance vs expected)
                'value_added_success': bac.get('va_reu_total'),
                'value_added_access_2nde': bac.get('va_acces_2nde'),
                # Student numbers
                'students_2nde': bac.get('eff_2nde'),
                'students_1ere': bac.get('eff_1ere'),
                'students_term': bac.get('eff_term'),
                'students_present': bac.get('presents_total')
            }

        merged_schools.append(school)
        stats['total'] += 1

    print(f"\n✓ Merged {stats['total']} schools with coordinates")
    print(f"  - {stats['primaire']} primary schools (Écoles)")
    print(f"  - {stats['college']} middle schools (Collèges)")
    print(f"  - {stats['lycee']} high schools (Lycées)")
    print(f"  - {stats['with_ips']} schools with IPS data ({stats['with_ips']/stats['total']*100:.1f}%)")
    print(f"  - {stats['with_enrollment']} schools with enrollment data ({stats['with_enrollment']/stats['total']*100:.1f}%)")
    print(f"  - {stats['with_exam_results']} schools with exam results ({stats['with_exam_results']/stats['total']*100:.1f}%)")

    # Deduplicate schools with same UAI (e.g., multiple campuses)
    # Keep the main campus (shorter, simpler name)
    print("\nDeduplicating schools with same UAI...")
    uai_dict = {}
    duplicate_keywords = ['site ', 'campus', 'pôle', 'esupec', 'enseignement sup']

    for school in merged_schools:
        uai = school['uai']
        name_lower = school['name'].lower()

        if uai in uai_dict:
            # Check if this is a more "main" campus than existing
            existing_name_lower = uai_dict[uai]['name'].lower()

            # Prefer schools without duplicate keywords
            existing_has_keywords = any(kw in existing_name_lower for kw in duplicate_keywords)
            current_has_keywords = any(kw in name_lower for kw in duplicate_keywords)

            if current_has_keywords and not existing_has_keywords:
                # Keep existing (it's the main campus)
                continue
            elif existing_has_keywords and not current_has_keywords:
                # Replace with current (it's the main campus)
                uai_dict[uai] = school
            else:
                # Both are similar, keep shorter name
                if len(school['name']) < len(uai_dict[uai]['name']):
                    uai_dict[uai] = school
        else:
            uai_dict[uai] = school

    deduplicated_schools = list(uai_dict.values())
    duplicates_removed = len(merged_schools) - len(deduplicated_schools)

    if duplicates_removed > 0:
        print(f"  Removed {duplicates_removed} duplicate campuses")
        stats['total'] = len(deduplicated_schools)

    # Save merged data
    output_file = DATA_DIR / "schools.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(deduplicated_schools, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Saved merged data to {output_file}")

    return merged_schools, stats


def main():
    """
    Main merge function
    """
    print("\n" + "="*80)
    print("FRANCE SCHOOLS MAP - DATA MERGE")
    print("Region: Pays de la Loire")
    print("="*80)

    schools, stats = merge_data()

    print("\n" + "="*80)
    print("MERGE COMPLETE")
    print("="*80)
    print(f"\nFinal dataset: {stats['total']} schools")
    print(f"  - Primary (Écoles): {stats['primaire']}")
    print(f"  - Middle (Collèges): {stats['college']}")
    print(f"  - High (Lycées): {stats['lycee']}")
    print(f"\nData coverage:")
    print(f"  - IPS data: {stats['with_ips']/stats['total']*100:.1f}%")
    print(f"  - Exam results: {stats['with_exam_results']/stats['total']*100:.1f}%")
    print(f"\nNext step: Copy data/schools.json to frontend/data/ and build the map")
    print()


if __name__ == '__main__':
    main()
