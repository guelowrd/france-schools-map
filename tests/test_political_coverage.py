#!/usr/bin/env python3
"""
Test political data coverage for both regions
Ensures all departments have political data after scraping
"""

import json
import unittest
from pathlib import Path

# Expected departments
PAYS_DE_LA_LOIRE = ['44', '49', '53', '72', '85']
NOUVELLE_AQUITAINE = ['16', '17', '19', '23', '24', '33', '40', '47', '64', '79', '86', '87']
ALL_DEPARTMENTS = PAYS_DE_LA_LOIRE + NOUVELLE_AQUITAINE

# Minimum expected communes per department (approximate, can be adjusted)
MIN_COMMUNES_PER_DEPT = {
    # Pays de la Loire
    '44': 200,  # Loire-Atlantique
    '49': 170,  # Maine-et-Loire
    '53': 230,  # Mayenne
    '72': 340,  # Sarthe
    '85': 250,  # Vendée

    # Nouvelle-Aquitaine
    '16': 350,  # Charente
    '17': 450,  # Charente-Maritime
    '19': 270,  # Corrèze
    '23': 250,  # Creuse
    '24': 490,  # Dordogne
    '33': 530,  # Gironde
    '40': 320,  # Landes
    '47': 310,  # Lot-et-Garonne
    '64': 530,  # Pyrénées-Atlantiques
    '79': 250,  # Deux-Sèvres
    '86': 260,  # Vienne
    '87': 190,  # Haute-Vienne
}


class TestPoliticalDataCoverage(unittest.TestCase):
    """Test that political data covers all required departments"""

    @classmethod
    def setUpClass(cls):
        """Load political data once for all tests"""
        political_data_path = Path(__file__).parent.parent / "frontend" / "data" / "political_data.json"

        if not political_data_path.exists():
            raise FileNotFoundError(f"Political data not found at {political_data_path}")

        with open(political_data_path) as f:
            cls.political_data = json.load(f)

        # Count communes by department
        cls.dept_counts = {}
        for insee_code in cls.political_data.keys():
            dept = insee_code[:2]
            cls.dept_counts[dept] = cls.dept_counts.get(dept, 0) + 1

    def test_all_departments_present(self):
        """Test that all 17 departments have political data"""
        missing_depts = []
        for dept in ALL_DEPARTMENTS:
            if dept not in self.dept_counts or self.dept_counts[dept] == 0:
                missing_depts.append(dept)

        self.assertEqual(
            missing_depts, [],
            f"Missing political data for departments: {missing_depts}"
        )

    def test_pays_de_la_loire_coverage(self):
        """Test that all Pays de la Loire departments have data"""
        for dept in PAYS_DE_LA_LOIRE:
            count = self.dept_counts.get(dept, 0)
            self.assertGreater(
                count, 0,
                f"Department {dept} (Pays de la Loire) has no political data"
            )

    def test_nouvelle_aquitaine_coverage(self):
        """Test that all Nouvelle-Aquitaine departments have data"""
        for dept in NOUVELLE_AQUITAINE:
            count = self.dept_counts.get(dept, 0)
            self.assertGreater(
                count, 0,
                f"Department {dept} (Nouvelle-Aquitaine) has no political data"
            )

    def test_minimum_commune_counts(self):
        """Test that each department has minimum expected number of communes"""
        insufficient_depts = []
        for dept, min_count in MIN_COMMUNES_PER_DEPT.items():
            actual_count = self.dept_counts.get(dept, 0)
            if actual_count < min_count:
                insufficient_depts.append(
                    f"{dept}: {actual_count} < {min_count} expected"
                )

        self.assertEqual(
            insufficient_depts, [],
            f"Departments with insufficient commune counts: {insufficient_depts}"
        )

    def test_political_data_structure(self):
        """Test that political data has expected structure for sample communes"""
        # Test a few sample INSEE codes from each region
        sample_communes = [
            '44109',  # Nantes (Pays de la Loire)
            '17300',  # La Rochelle (Nouvelle-Aquitaine)
        ]

        for insee_code in sample_communes:
            if insee_code in self.political_data:
                commune_data = self.political_data[insee_code]

                # Should have mayor data
                self.assertIn('mayor', commune_data, f"{insee_code} missing mayor data")

                # Should have presidential data
                self.assertIn('presidential_2022', commune_data,
                            f"{insee_code} missing presidential data")

    def test_mayor_data_completeness(self):
        """Test that most communes have mayor data (95%+ coverage expected)"""
        total_communes = len(self.political_data)
        communes_with_mayor = sum(
            1 for data in self.political_data.values()
            if data.get('mayor') and data['mayor'].get('last_name')
        )

        coverage_percent = (communes_with_mayor / total_communes) * 100

        self.assertGreater(
            coverage_percent, 95.0,
            f"Mayor data coverage too low: {coverage_percent:.1f}% "
            f"({communes_with_mayor}/{total_communes})"
        )

    def test_presidential_2022_coverage(self):
        """Test that most communes have presidential 2022 data (95%+ coverage expected)"""
        total_communes = len(self.political_data)
        communes_with_presidential = sum(
            1 for data in self.political_data.values()
            if data.get('presidential_2022')
        )

        coverage_percent = (communes_with_presidential / total_communes) * 100

        self.assertGreater(
            coverage_percent, 95.0,
            f"Presidential 2022 data coverage too low: {coverage_percent:.1f}% "
            f"({communes_with_presidential}/{total_communes})"
        )

    def test_print_coverage_summary(self):
        """Print coverage summary for debugging"""
        print("\n" + "="*80)
        print("POLITICAL DATA COVERAGE SUMMARY")
        print("="*80)

        print("\nPays de la Loire:")
        for dept in PAYS_DE_LA_LOIRE:
            count = self.dept_counts.get(dept, 0)
            expected = MIN_COMMUNES_PER_DEPT.get(dept, 0)
            status = "✓" if count >= expected else "✗"
            print(f"  {status} {dept}: {count} communes (expected >={expected})")

        print("\nNouvelle-Aquitaine:")
        for dept in NOUVELLE_AQUITAINE:
            count = self.dept_counts.get(dept, 0)
            expected = MIN_COMMUNES_PER_DEPT.get(dept, 0)
            status = "✓" if count >= expected else "✗"
            print(f"  {status} {dept}: {count} communes (expected >={expected})")

        print(f"\nTotal communes: {len(self.political_data)}")
        print("="*80)


if __name__ == '__main__':
    unittest.main(verbosity=2)
