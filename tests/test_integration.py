#!/usr/bin/env python3
"""
Integration tests for the complete political data pipeline.

Tests the full workflow from raw data files to final merged output.
"""

import unittest
import json
from pathlib import Path


class TestCachedDataIntegrity(unittest.TestCase):
    """Test integrity of cached political data files."""

    def setUp(self):
        """Load cached data files."""
        self.cache_dir = Path(__file__).parent.parent / "data" / "political_cache"
        self.frontend_data_dir = Path(__file__).parent.parent / "frontend" / "data"

    def test_political_data_json_exists(self):
        """Verify political_data.json exists in both cache and frontend."""
        cache_file = self.cache_dir / "political_data.json"
        frontend_file = self.frontend_data_dir / "political_data.json"

        self.assertTrue(cache_file.exists(), "political_data.json should exist in cache")
        self.assertTrue(frontend_file.exists(), "political_data.json should exist in frontend")

    def test_political_data_structure(self):
        """Verify structure of political_data.json."""
        political_data_file = self.cache_dir / "political_data.json"

        if not political_data_file.exists():
            self.skipTest("political_data.json not found - run download first")

        with open(political_data_file) as f:
            data = json.load(f)

        # Should have data for ~1200 communes
        self.assertGreater(len(data), 1000, "Should have data for > 1000 communes")

        # Check structure of first commune
        sample_insee = list(data.keys())[0]
        sample_commune = data[sample_insee]

        # Required fields
        self.assertIn('commune_name', sample_commune)
        self.assertIn('insee_code', sample_commune)
        self.assertEqual(sample_commune['insee_code'], sample_insee)

        # Optional but expected fields
        self.assertIn('mayor', sample_commune)
        self.assertIn('municipal_2020', sample_commune)
        self.assertIn('presidential_2022', sample_commune)
        self.assertIn('legislative_2024', sample_commune)

    def test_mayor_data_coverage(self):
        """Test that mayor data exists for most communes."""
        political_data_file = self.cache_dir / "political_data.json"

        if not political_data_file.exists():
            self.skipTest("political_data.json not found - run download first")

        with open(political_data_file) as f:
            data = json.load(f)

        with_mayor = sum(1 for v in data.values() if v.get('mayor'))
        coverage_pct = (with_mayor / len(data)) * 100

        self.assertGreater(coverage_pct, 95, f"Mayor coverage should be > 95%, got {coverage_pct:.1f}%")

    def test_presidential_2022_data_quality(self):
        """Verify Presidential 2022 data quality."""
        political_data_file = self.cache_dir / "political_data.json"

        if not political_data_file.exists():
            self.skipTest("political_data.json not found - run download first")

        with open(political_data_file) as f:
            data = json.load(f)

        issues = []

        for insee, commune in data.items():
            pres = commune.get('presidential_2022')
            if not pres:
                continue

            # Check Round 1
            if pres.get('round_1'):
                round1 = pres['round_1']

                # Should have 4 candidates
                if len(round1) != 4:
                    issues.append(f"{insee}: Round 1 has {len(round1)} candidates (expected 4)")

                # Check percentages are reasonable
                for i, cand in enumerate(round1):
                    pct = cand.get('percentage', 0)
                    if not (0 <= pct <= 100):
                        issues.append(f"{insee}: Round 1 candidate {i+1} has invalid percentage {pct}")

                    # Check encoding (no mojibake)
                    candidate_name = cand.get('candidate', '')
                    if 'Ã' in candidate_name or 'Â' in candidate_name:
                        issues.append(f"{insee}: Round 1 has encoding issue: {candidate_name}")

            # Check Round 2
            if pres.get('round_2'):
                round2 = pres['round_2']

                # Should have macron and le_pen
                self.assertIn('macron', round2, f"{insee}: Round 2 missing macron")
                self.assertIn('le_pen', round2, f"{insee}: Round 2 missing le_pen")

                macron_pct = round2.get('macron', 0)
                lepen_pct = round2.get('le_pen', 0)

                # Percentages should be reasonable
                if not (0 <= macron_pct <= 100):
                    issues.append(f"{insee}: Macron has invalid percentage {macron_pct}")

                if not (0 <= lepen_pct <= 100):
                    issues.append(f"{insee}: Le Pen has invalid percentage {lepen_pct}")

                # Should sum to approximately 100%
                total = macron_pct + lepen_pct
                if not (99 <= total <= 101):
                    issues.append(f"{insee}: Round 2 percentages sum to {total} (should be ~100)")

        if issues:
            self.fail(f"Found {len(issues)} Presidential 2022 data quality issues:\n" + "\n".join(issues[:10]))

    def test_legislative_2024_round2_candidates(self):
        """Verify Legislative 2024 Round 2 has at most 2 candidates."""
        political_data_file = self.cache_dir / "political_data.json"

        if not political_data_file.exists():
            self.skipTest("political_data.json not found - run download first")

        with open(political_data_file) as f:
            data = json.load(f)

        issues = []

        for insee, commune in data.items():
            leg = commune.get('legislative_2024')
            if not leg or not leg.get('round_2'):
                continue

            round2_candidates = leg['round_2']

            # Round 2 is a runoff - should have at most 2 candidates
            # (Sometimes 1 if elected in first round with >50%)
            if len(round2_candidates) > 2:
                issues.append(f"{insee}: Round 2 has {len(round2_candidates)} candidates (max 2 expected)")

        if issues:
            self.fail(f"Found {len(issues)} Legislative Round 2 issues:\n" + "\n".join(issues))

    def test_municipal_2020_party_labels(self):
        """Verify Municipal 2020 party codes are converted to labels."""
        political_data_file = self.cache_dir / "political_data.json"

        if not political_data_file.exists():
            self.skipTest("political_data.json not found - run download first")

        with open(political_data_file) as f:
            data = json.load(f)

        # Find mayors with party info
        mayors_with_party = []
        for commune in data.values():
            mayor = commune.get('mayor')
            if mayor and mayor.get('party'):
                mayors_with_party.append(mayor['party'])

        if not mayors_with_party:
            self.skipTest("No mayor party data found")

        # Check that labels are readable (not just codes)
        readable_labels = [
            'Divers droite', 'Divers gauche', 'Divers centre',
            'Union de la gauche', 'Écologiste', 'Non classé',
            'Les Républicains', 'Socialiste', 'Renaissance'
        ]

        has_readable_label = any(
            any(label in party for label in readable_labels)
            for party in mayors_with_party
        )

        self.assertTrue(has_readable_label, "Should have readable party labels (not just codes)")

    def test_insee_codes_are_valid(self):
        """Verify all INSEE codes are 5-digit format."""
        political_data_file = self.cache_dir / "political_data.json"

        if not political_data_file.exists():
            self.skipTest("political_data.json not found - run download first")

        with open(political_data_file) as f:
            data = json.load(f)

        invalid_codes = []

        for insee_code in data.keys():
            # INSEE codes should be 5 digits (2 dept + 3 commune)
            if not insee_code.isdigit() or len(insee_code) != 5:
                invalid_codes.append(insee_code)

        if invalid_codes:
            self.fail(f"Found {len(invalid_codes)} invalid INSEE codes: {invalid_codes[:10]}")

    def test_schools_json_has_insee_codes(self):
        """Verify schools.json has INSEE codes for matching."""
        schools_file = Path(__file__).parent.parent / "data" / "schools.json"

        if not schools_file.exists():
            self.skipTest("schools.json not found")

        with open(schools_file) as f:
            schools = json.load(f)

        # Check sample of schools for insee_code
        schools_with_insee = 0
        for school in schools[:100]:  # Check first 100
            if school.get('address', {}).get('insee_code'):
                schools_with_insee += 1

        coverage_pct = (schools_with_insee / 100) * 100

        self.assertGreater(
            coverage_pct, 90,
            f"Schools should have INSEE codes for matching (got {coverage_pct:.1f}%)"
        )


class TestDataPipelineConsistency(unittest.TestCase):
    """Test consistency across the data pipeline."""

    def setUp(self):
        """Load all relevant data files."""
        self.cache_dir = Path(__file__).parent.parent / "data" / "political_cache"

    def test_cache_files_exist(self):
        """Verify all expected cache files exist."""
        expected_files = [
            "insee_mapping.json",
            "mayors.json",
            "municipal_2020.json",
            "presidential_2022.json",
            "legislative_2024.json",
            "political_data.json"
        ]

        missing_files = []
        for filename in expected_files:
            filepath = self.cache_dir / filename
            if not filepath.exists():
                missing_files.append(filename)

        if missing_files:
            self.fail(f"Missing cache files: {missing_files}. Run download script first.")

    def test_merged_data_includes_all_sources(self):
        """Verify merged data includes all source types."""
        political_data_file = self.cache_dir / "political_data.json"

        if not political_data_file.exists():
            self.skipTest("political_data.json not found - run download first")

        with open(political_data_file) as f:
            data = json.load(f)

        # Count communes with each data type
        with_mayor = sum(1 for v in data.values() if v.get('mayor'))
        with_municipal = sum(1 for v in data.values() if v.get('municipal_2020'))
        with_presidential = sum(1 for v in data.values() if v.get('presidential_2022'))
        with_legislative = sum(1 for v in data.values() if v.get('legislative_2024'))

        # All should have significant coverage
        self.assertGreater(with_mayor, len(data) * 0.95, "Mayor coverage should be > 95%")
        self.assertGreater(with_municipal, len(data) * 0.30, "Municipal coverage should be > 30%")
        self.assertGreater(with_presidential, len(data) * 0.95, "Presidential coverage should be > 95%")
        self.assertGreater(with_legislative, len(data) * 0.95, "Legislative coverage should be > 95%")


if __name__ == '__main__':
    unittest.main(verbosity=2)
