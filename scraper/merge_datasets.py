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
        'with_exam_results': 0
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
            school['ips'] = {
                'value': ips_data.get('ips') or ips_data.get('ips_ensemble_gt_pro'),
                'year': ips_data.get('rentree_scolaire', ''),
                'ecart_type': ips_data.get('ecart_type_de_l_ips') or ips_data.get('ecart_type_etablissement'),
                # Benchmarks for context
                'national_average': ips_data.get('ips_national'),
                'academique_average': ips_data.get('ips_academique'),
                'departemental_average': ips_data.get('ips_departemental')
            }

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
    print(f"  - {stats['with_exam_results']} schools with exam results ({stats['with_exam_results']/stats['total']*100:.1f}%)")

    # Calculate class size estimates where possible
    print("\nCalculating class size estimates...")
    for school in merged_schools:
        if school.get('student_count') and school['student_count'] > 0:
            # Rough estimates for class size
            if school['type'] == 'Primaire':
                # Elementary: typically 5 grades (CP, CE1, CE2, CM1, CM2)
                estimated_classes = max(5, school['student_count'] // 25)  # Assume ~25 per class
                school['estimated_class_size'] = school['student_count'] / estimated_classes
            elif school['type'] == 'Collège':
                # Middle school: 4 grades (6e, 5e, 4e, 3e)
                estimated_classes = max(4, school['student_count'] // 28)  # Assume ~28 per class
                school['estimated_class_size'] = school['student_count'] / estimated_classes
            elif school['type'] == 'Lycée':
                # High school: 3 grades (2nde, 1ere, Terminale)
                # Use actual enrollment data if available
                if school.get('exam_results'):
                    total_enrolled = sum(filter(None, [
                        school['exam_results'].get('students_2nde'),
                        school['exam_results'].get('students_1ere'),
                        school['exam_results'].get('students_term')
                    ]))
                    if total_enrolled > 0:
                        estimated_classes = max(3, total_enrolled // 30)
                        school['estimated_class_size'] = total_enrolled / estimated_classes
                else:
                    estimated_classes = max(3, school['student_count'] // 30)
                    school['estimated_class_size'] = school['student_count'] / estimated_classes

    # Save merged data
    output_file = DATA_DIR / "schools.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_schools, f, ensure_ascii=False, indent=2)

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
