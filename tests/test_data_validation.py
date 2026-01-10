#!/usr/bin/env python3
"""
Data validation tests for schools.json
Ensures data integrity and catches regressions
"""

import json
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test configuration
DATA_DIR = Path(__file__).parent.parent / "data"
SCHOOLS_FILE = DATA_DIR / "schools.json"

# Expected region bounds (Pays de la Loire)
# Sarthe extends further east (Le Mans area around 0.7°E)
LAT_MIN, LAT_MAX = 46.2, 48.6
LON_MIN, LON_MAX = -2.6, 1.0

# Expected school types
VALID_TYPES = {'Primaire', 'Collège', 'Lycée'}
VALID_PUBLIC_PRIVATE = {'Public', 'Privé'}


def load_schools():
    """Load schools.json file"""
    with open(SCHOOLS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_file_exists():
    """Test that schools.json exists"""
    assert SCHOOLS_FILE.exists(), f"schools.json not found at {SCHOOLS_FILE}"
    print("✓ schools.json exists")


def test_valid_json():
    """Test that schools.json is valid JSON"""
    try:
        schools = load_schools()
        assert isinstance(schools, list), "schools.json should be a list"
        print(f"✓ schools.json is valid JSON with {len(schools)} schools")
        return schools
    except json.JSONDecodeError as e:
        raise AssertionError(f"Invalid JSON: {e}")


def test_school_count():
    """Test that we have expected number of schools"""
    schools = load_schools()
    assert len(schools) > 2500, f"Expected >2500 schools, got {len(schools)}"
    assert len(schools) < 4000, f"Expected <4000 schools, got {len(schools)}"
    print(f"✓ School count is reasonable: {len(schools)}")


def test_school_type_distribution():
    """Test distribution of school types"""
    schools = load_schools()
    type_counts = {}

    for school in schools:
        school_type = school.get('type')
        assert school_type in VALID_TYPES, f"Invalid school type: {school_type}"
        type_counts[school_type] = type_counts.get(school_type, 0) + 1

    # Expected ratios (Primaire > Collège > Lycée)
    assert type_counts['Primaire'] > type_counts['Collège'], "Should have more primary than middle schools"
    assert type_counts['Collège'] > type_counts['Lycée'], "Should have more middle than high schools"

    print(f"✓ School type distribution:")
    for school_type, count in sorted(type_counts.items()):
        pct = count / len(schools) * 100
        print(f"    {school_type:15s}: {count:4d} ({pct:5.1f}%)")


def test_required_fields():
    """Test that all schools have required fields"""
    schools = load_schools()
    required_fields = ['uai', 'name', 'type', 'public_private', 'address', 'coordinates', 'contact']

    errors = []
    for i, school in enumerate(schools):
        for field in required_fields:
            if field not in school:
                errors.append(f"School {i} ({school.get('name', 'Unknown')}) missing field: {field}")

    assert len(errors) == 0, f"Missing required fields:\n" + "\n".join(errors[:10])
    print(f"✓ All schools have required fields")


def test_coordinates_valid():
    """Test that all coordinates are within expected bounds"""
    schools = load_schools()
    invalid_coords = []

    for school in schools:
        coords = school.get('coordinates', {})
        lat = coords.get('latitude')
        lon = coords.get('longitude')

        if lat is None or lon is None:
            invalid_coords.append(f"{school['name']}: missing coordinates")
            continue

        if not (LAT_MIN <= lat <= LAT_MAX):
            invalid_coords.append(f"{school['name']}: latitude {lat} out of bounds")

        if not (LON_MIN <= lon <= LON_MAX):
            invalid_coords.append(f"{school['name']}: longitude {lon} out of bounds")

    assert len(invalid_coords) == 0, f"Invalid coordinates:\n" + "\n".join(invalid_coords[:10])
    print(f"✓ All coordinates are within Pays de la Loire bounds")


def test_ips_data_coverage():
    """Test IPS data coverage"""
    schools = load_schools()
    with_ips = sum(1 for s in schools if s.get('ips') and s['ips'].get('value'))
    coverage = with_ips / len(schools) * 100

    assert coverage > 80, f"IPS coverage too low: {coverage:.1f}% (expected >80%)"
    print(f"✓ IPS coverage: {coverage:.1f}% ({with_ips}/{len(schools)})")


def test_ips_values_valid():
    """Test that IPS values are in reasonable range"""
    schools = load_schools()
    invalid_ips = []
    ns_count = 0

    for school in schools:
        ips = school.get('ips', {})
        if ips and ips.get('value'):
            value_str = str(ips['value'])

            # Handle 'NS' (Non Significatif) values - these are valid
            if value_str.upper() in ['NS', 'NON SIGNIFICATIF']:
                ns_count += 1
                continue

            try:
                value = float(value_str)
                # IPS typically ranges from 40 to 180
                if not (30 <= value <= 200):
                    invalid_ips.append(f"{school['name']}: IPS {value}")
            except ValueError:
                invalid_ips.append(f"{school['name']}: IPS value not numeric: '{value_str}'")

    assert len(invalid_ips) == 0, f"Invalid IPS values:\n" + "\n".join(invalid_ips[:10])
    print(f"✓ All IPS values are valid (30-200 or NS), {ns_count} schools have NS")


def test_enrollment_data_coverage():
    """Test enrollment data coverage"""
    schools = load_schools()
    with_enrollment = sum(1 for s in schools if s.get('student_count'))
    coverage = with_enrollment / len(schools) * 100

    assert coverage > 40, f"Enrollment coverage too low: {coverage:.1f}% (expected >40%)"
    print(f"✓ Enrollment coverage: {coverage:.1f}% ({with_enrollment}/{len(schools)})")


def test_enrollment_values_reasonable():
    """Test that enrollment values are reasonable (not inflated from multi-year aggregation)"""
    schools = load_schools()
    invalid_enrollment = []

    for school in schools:
        student_count = school.get('student_count')
        if student_count:
            # Reasonable max values by type
            max_students = {
                'Primaire': 800,   # Large primary school
                'Collège': 1500,   # Large middle school
                'Lycée': 2000      # Large high school
            }

            max_for_type = max_students.get(school['type'], 2000)
            if student_count > max_for_type:
                invalid_enrollment.append(
                    f"{school['name']} ({school['type']}): {student_count} students (max expected: {max_for_type})"
                )

    assert len(invalid_enrollment) == 0, (
        f"Suspiciously high enrollment (possible multi-year aggregation bug):\n" +
        "\n".join(invalid_enrollment[:10])
    )
    print(f"✓ All enrollment values are reasonable (no multi-year aggregation)")


def test_primary_schools_class_size():
    """Test that primary schools with enrollment have class size calculated"""
    schools = load_schools()
    primaires = [s for s in schools if s['type'] == 'Primaire']

    with_enrollment = [s for s in primaires if s.get('student_count')]
    with_classes = [s for s in with_enrollment if s.get('number_of_classes')]
    with_class_size = [s for s in with_classes if s.get('class_size')]

    # If we have students and classes, we should have class_size
    assert len(with_class_size) == len(with_classes), (
        f"Class size calculation missing: {len(with_classes)} schools have classes but "
        f"only {len(with_class_size)} have class_size"
    )

    print(f"✓ Primary schools: {len(with_enrollment)} with enrollment, "
          f"{len(with_class_size)} with class size")


def test_exam_results_coverage():
    """Test exam results coverage for collèges and lycées"""
    schools = load_schools()

    colleges = [s for s in schools if s['type'] == 'Collège']
    colleges_with_results = [s for s in colleges if s.get('exam_results')]

    lycees = [s for s in schools if s['type'] == 'Lycée']
    lycees_with_results = [s for s in lycees if s.get('exam_results')]

    print(f"✓ Exam results:")
    print(f"    Collèges: {len(colleges_with_results)}/{len(colleges)} "
          f"({len(colleges_with_results)/len(colleges)*100:.1f}%)")
    print(f"    Lycées: {len(lycees_with_results)}/{len(lycees)} "
          f"({len(lycees_with_results)/len(lycees)*100:.1f}%)")


def test_no_professional_lycees():
    """Test that professional lycées are excluded"""
    schools = load_schools()
    lycees = [s for s in schools if s['type'] == 'Lycée']

    professional_keywords = ['professionnel', 'section d\'enseignement']
    suspicious = []

    for school in lycees:
        name_lower = school['name'].lower()
        if any(keyword in name_lower for keyword in professional_keywords):
            suspicious.append(school['name'])

    assert len(suspicious) == 0, (
        f"Found {len(suspicious)} potential professional lycées that should be filtered:\n" +
        "\n".join(suspicious[:10])
    )
    print(f"✓ No professional lycées in dataset")


def test_uai_format():
    """Test that UAI codes have valid format"""
    schools = load_schools()
    invalid_uai = []

    for school in schools:
        uai = school.get('uai', '')
        # UAI format: 7 digits + 1 letter (e.g., 0440021J)
        if not (len(uai) == 8 and uai[:7].isdigit() and uai[7].isalpha()):
            invalid_uai.append(f"{school['name']}: UAI '{uai}'")

    assert len(invalid_uai) == 0, f"Invalid UAI codes:\n" + "\n".join(invalid_uai[:10])
    print(f"✓ All UAI codes have valid format")


def test_dates_present():
    """Test that data sources include dates/years"""
    schools = load_schools()

    # Check IPS has years
    with_ips_year = sum(1 for s in schools if s.get('ips') and s['ips'].get('year'))
    ips_schools = sum(1 for s in schools if s.get('ips'))

    # Check enrollment has years
    with_enrollment_year = sum(1 for s in schools if s.get('enrollment_year'))
    enrollment_schools = sum(1 for s in schools if s.get('student_count'))

    # Check exam results have years
    with_exam_year = sum(1 for s in schools if s.get('exam_results') and s['exam_results'].get('year'))
    exam_schools = sum(1 for s in schools if s.get('exam_results'))

    assert with_ips_year == ips_schools, f"Some IPS data missing year field"
    assert with_enrollment_year == enrollment_schools, f"Some enrollment data missing year field"
    assert with_exam_year == exam_schools, f"Some exam results missing year field"

    print(f"✓ All data sources include dates/years")


def run_all_tests():
    """Run all tests and report results"""
    print("=" * 80)
    print("RUNNING DATA VALIDATION TESTS")
    print("=" * 80)
    print()

    tests = [
        test_file_exists,
        test_valid_json,
        test_school_count,
        test_school_type_distribution,
        test_required_fields,
        test_coordinates_valid,
        test_ips_data_coverage,
        test_ips_values_valid,
        test_enrollment_data_coverage,
        test_enrollment_values_reasonable,
        test_primary_schools_class_size,
        test_exam_results_coverage,
        test_no_professional_lycees,
        test_uai_format,
        test_dates_present,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__} FAILED:")
            print(f"  {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} ERROR:")
            print(f"  {e}")
            failed += 1
        print()

    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
