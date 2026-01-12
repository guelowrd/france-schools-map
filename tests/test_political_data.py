#!/usr/bin/env python3
"""
Political data validation tests

Tests:
- political_data.json structure and validity
- Coverage of schools with political data
- Data quality (percentages, sorting, etc.)
"""

import json
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
SCHOOLS_FILE = PROJECT_ROOT / "data" / "schools.json"
POLITICAL_FILE = PROJECT_ROOT / "data" / "political_cache" / "political_data.json"


def test_political_data_structure():
    """Verify political_data.json has correct structure"""
    print("="*80)
    print("TEST 1: Political data structure")
    print("="*80)

    assert POLITICAL_FILE.exists(), f"political_data.json not found at {POLITICAL_FILE}"

    with open(POLITICAL_FILE) as f:
        data = json.load(f)

    assert len(data) > 0, "Political data is empty"
    print(f"✓ Loaded {len(data)} communes")

    # Check random commune has all required fields
    sample_insee = list(data.keys())[0]
    commune_data = data[sample_insee]

    required_fields = ['commune_name', 'insee_code', 'mayor', 'municipal_2020',
                      'presidential_2022', 'legislative_2024']

    for field in required_fields:
        assert field in commune_data, f"Missing field: {field}"

    print(f"✓ All required fields present in sample commune ({sample_insee})")
    print()


def test_insee_coverage():
    """Check that schools have matching political data"""
    print("="*80)
    print("TEST 2: INSEE code coverage")
    print("="*80)

    with open(SCHOOLS_FILE) as f:
        schools = json.load(f)

    with open(POLITICAL_FILE) as f:
        political = json.load(f)

    schools_with_insee = [s for s in schools if s.get("address", {}).get("insee_code")]
    matched = sum(1 for s in schools_with_insee if s["address"]["insee_code"] in political)

    coverage = (matched / len(schools)) * 100
    print(f"✓ Schools with INSEE codes: {len(schools_with_insee)}/{len(schools)}")
    print(f"✓ Political data coverage: {matched}/{len(schools)} schools ({coverage:.1f}%)")

    if coverage < 80:
        print(f"⚠ Warning: Coverage below 80% ({coverage:.1f}%)")
    else:
        print(f"✓ Coverage above 80%")

    print()


def test_percentage_ranges():
    """Verify all percentages are between 0-100"""
    print("="*80)
    print("TEST 3: Percentage ranges")
    print("="*80)

    with open(POLITICAL_FILE) as f:
        data = json.load(f)

    errors = []

    for insee, commune in data.items():
        # Check municipal percentage
        if commune.get("municipal_2020") and commune["municipal_2020"].get("percentage"):
            pct = commune["municipal_2020"]["percentage"]
            if not (0 <= pct <= 100):
                errors.append(f"Invalid municipal % in {insee}: {pct}")

        # Check presidential round 2
        if "presidential_2022" in commune and "round_2" in commune["presidential_2022"]:
            r2 = commune["presidential_2022"]["round_2"]
            if "macron" in r2 and not (0 <= r2["macron"] <= 100):
                errors.append(f"Invalid Macron % in {insee}: {r2['macron']}")
            if "le_pen" in r2 and not (0 <= r2["le_pen"] <= 100):
                errors.append(f"Invalid Le Pen % in {insee}: {r2['le_pen']}")

            # Should sum to ~100
            if "macron" in r2 and "le_pen" in r2:
                total = r2["macron"] + r2["le_pen"]
                if not (99 <= total <= 101):
                    errors.append(f"Presidential R2 doesn't sum to 100 in {insee}: {total}")

    if errors:
        print("✗ Found percentage errors:")
        for error in errors[:10]:
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
        raise AssertionError(f"Found {len(errors)} percentage errors")
    else:
        print(f"✓ All percentages valid (checked {len(data)} communes)")

    print()


def test_top4_ordering():
    """Verify TOP 4 candidates are sorted by percentage (descending)"""
    print("="*80)
    print("TEST 4: TOP 4 candidate ordering")
    print("="*80)

    with open(POLITICAL_FILE) as f:
        data = json.load(f)

    errors = []

    for insee, commune in data.items():
        # Check presidential round 1
        if "presidential_2022" in commune and "round_1" in commune["presidential_2022"]:
            r1 = commune["presidential_2022"]["round_1"]
            if r1 and len(r1) > 1:
                percentages = [c["percentage"] for c in r1]
                if percentages != sorted(percentages, reverse=True):
                    errors.append(f"Presidential R1 not sorted in {insee}")

        # Check legislative rounds
        for round_key in ["round_1", "round_2"]:
            if "legislative_2024" in commune and round_key in commune["legislative_2024"]:
                candidates = commune["legislative_2024"][round_key]
                if candidates and len(candidates) > 1:
                    percentages = [c["percentage"] for c in candidates]
                    if percentages != sorted(percentages, reverse=True):
                        errors.append(f"Legislative {round_key} not sorted in {insee}")

    if errors:
        print("✗ Found sorting errors:")
        for error in errors[:10]:
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
        raise AssertionError(f"Found {len(errors)} sorting errors")
    else:
        print(f"✓ All TOP 4 lists properly sorted (checked {len(data)} communes)")

    print()


def test_schools_have_insee():
    """Verify schools.json has insee_code field"""
    print("="*80)
    print("TEST 5: Schools have INSEE codes")
    print("="*80)

    with open(SCHOOLS_FILE) as f:
        schools = json.load(f)

    with_insee = sum(1 for s in schools if s.get("address", {}).get("insee_code"))
    without_insee = len(schools) - with_insee

    print(f"✓ Schools with INSEE codes: {with_insee}/{len(schools)} ({100*with_insee/len(schools):.1f}%)")

    if without_insee > 0:
        print(f"⚠ {without_insee} schools without INSEE codes")

    print()


def test_mayor_data_presence():
    """Check mayor data coverage"""
    print("="*80)
    print("TEST 6: Mayor data presence")
    print("="*80)

    with open(POLITICAL_FILE) as f:
        data = json.load(f)

    with_mayor = sum(1 for v in data.values() if v.get('mayor'))

    coverage = (with_mayor / len(data)) * 100
    print(f"✓ Communes with mayor data: {with_mayor}/{len(data)} ({coverage:.1f}%)")

    if coverage < 50:
        print(f"⚠ Warning: Mayor coverage below 50% ({coverage:.1f}%)")

    # Sample a commune with mayor
    communes_with_mayor = [k for k, v in data.items() if v.get('mayor')]
    if communes_with_mayor:
        sample = data[communes_with_mayor[0]]
        print(f"✓ Sample mayor data: {sample['mayor']['first_name']} {sample['mayor']['last_name']} ({sample['mayor']['party']})")

    print()


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("POLITICAL DATA VALIDATION TESTS")
    print("="*80)
    print()

    tests = [
        test_political_data_structure,
        test_insee_coverage,
        test_percentage_ranges,
        test_top4_ordering,
        test_schools_have_insee,
        test_mayor_data_presence
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ TEST FAILED: {str(e)}")
            failed += 1
            print()

    print("="*80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*80)

    return failed == 0


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
