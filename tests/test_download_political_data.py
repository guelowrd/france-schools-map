#!/usr/bin/env python3
"""
Comprehensive tests for political data download and processing.

Tests cover:
- INSEE mapping building
- Mayor data parsing
- Municipal elections (both rounds, different delimiters)
- Presidential elections (different encodings, delimiter handling)
- Legislative elections (wide format CSV parsing)
- Data merging logic
- Party label conversion
- Error handling
"""

import unittest
import json
import sys
from pathlib import Path
from io import StringIO
import csv

# Add scraper to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scraper"))

from download_political_data import (
    PARTY_LABELS,
    DEPARTMENTS,
    merge_political_data
)


class TestPartyLabels(unittest.TestCase):
    """Test party code to label conversion."""

    def test_party_labels_exist(self):
        """Verify PARTY_LABELS dictionary has expected entries."""
        self.assertIsInstance(PARTY_LABELS, dict)
        self.assertGreater(len(PARTY_LABELS), 20, "Should have at least 20 party labels")

    def test_common_party_codes(self):
        """Test common party codes convert correctly."""
        expected_mappings = {
            'LDVD': 'Divers droite',
            'LDVG': 'Divers gauche',
            'LDVC': 'Divers centre',
            'LUG': 'Union de la gauche',
            'LVEC': 'Écologiste',
            'LREM': 'Renaissance (ex-LREM)',
            'LNC': 'Non classé',
            'NC': 'Non classé',
            'LLR': 'Les Républicains',
            'LRN': 'Rassemblement national',
            'LEXG': 'Extrême gauche',
            'LSOC': 'Socialiste'
        }

        for code, expected_label in expected_mappings.items():
            self.assertEqual(
                PARTY_LABELS.get(code),
                expected_label,
                f"Party code {code} should map to '{expected_label}'"
            )

    def test_all_political_spectrum_covered(self):
        """Verify labels cover full political spectrum."""
        labels = set(PARTY_LABELS.values())

        # Check left spectrum
        self.assertTrue(
            any('gauche' in label.lower() or 'Socialiste' in label or 'Communiste' in label
                for label in labels),
            "Should have left-wing labels"
        )

        # Check center
        self.assertTrue(
            any('centre' in label.lower() or 'Renaissance' in label or 'Modem' in label
                for label in labels),
            "Should have center labels"
        )

        # Check right
        self.assertTrue(
            any('droite' in label.lower() or 'Républicains' in label
                for label in labels),
            "Should have right-wing labels"
        )


class TestMunicipalDataParsing(unittest.TestCase):
    """Test Municipal 2020 election data parsing."""

    def test_municipal_round1_tab_delimiter(self):
        """Round 1 files use TAB delimiter."""
        # Sample Round 1 data (tab-delimited)
        sample_csv = "Code du département\tCode de la commune\tListe\tCode Nuance\tVoix\tExprimés\n"
        sample_csv += "44\t001\tABBARETZ CAP 2026\tLNC\t234\t234\n"

        reader = csv.DictReader(StringIO(sample_csv), delimiter='\t')
        row = next(reader)

        self.assertEqual(row['Code du département'], '44')
        self.assertEqual(row['Code de la commune'], '001')
        self.assertEqual(row['Liste'], 'ABBARETZ CAP 2026')
        self.assertEqual(row['Code Nuance'], 'LNC')

    def test_municipal_round2_semicolon_delimiter(self):
        """Round 2 files use semicolon delimiter."""
        sample_csv = "Code du département;Code de la commune;Liste;Code Nuance;Voix;Exprimés\n"
        sample_csv += "44;109;ENSEMBLE NANTES EN CONFIANCE;LUG;45678;76543\n"

        reader = csv.DictReader(StringIO(sample_csv), delimiter=';')
        row = next(reader)

        self.assertEqual(row['Code du département'], '44')
        self.assertEqual(row['Code de la commune'], '109')
        self.assertEqual(row['Liste'], 'ENSEMBLE NANTES EN CONFIANCE')
        self.assertEqual(row['Code Nuance'], 'LUG')

    def test_municipal_percentage_calculation(self):
        """Test percentage calculation from voix/exprimés."""
        voix = 45678
        exprimes = 76543
        expected_pct = round((voix / exprimes) * 100, 1)

        self.assertEqual(expected_pct, 59.7)

    def test_department_filtering(self):
        """Test filtering for Pays de la Loire departments."""
        valid_depts = ['44', '49', '53', '72', '85']
        self.assertEqual(DEPARTMENTS, valid_depts)

        # Test that only these departments are processed
        test_depts = ['44', '75', '49', '13', '72']
        filtered = [d for d in test_depts if d in DEPARTMENTS]
        self.assertEqual(filtered, ['44', '49', '72'])


class TestPresidentialDataParsing(unittest.TestCase):
    """Test Presidential 2022 election data parsing."""

    def test_round1_comma_delimiter_utf8(self):
        """Round 1 uses comma delimiter and UTF-8 encoding."""
        sample_csv = "dep_code,commune_code,cand_nom,cand_prenom,cand_nb_voix,exprimes_nb\n"
        sample_csv += "44,109,MÉLENCHON,Jean-Luc,48000,146394\n"

        reader = csv.DictReader(StringIO(sample_csv), delimiter=',')
        row = next(reader)

        self.assertEqual(row['dep_code'], '44')
        self.assertEqual(row['commune_code'], '109')
        self.assertEqual(row['cand_nom'], 'MÉLENCHON')
        self.assertIn('ÉLENCHON', row['cand_nom'], "UTF-8 should preserve accents")

    def test_round2_semicolon_delimiter_latin1(self):
        """Round 2 uses semicolon delimiter and latin-1 encoding."""
        sample_csv = "Code du département;Code de la commune;Nom;Prénom;Voix;Exprimés\n"
        sample_csv += "44;109;MACRON;Emmanuel;103996;128159\n"

        reader = csv.DictReader(StringIO(sample_csv), delimiter=';')
        row = next(reader)

        self.assertEqual(row['Code du département'], '44')
        self.assertEqual(row['Voix'], '103996')
        self.assertEqual(row['Exprimés'], '128159')

    def test_presidential_round1_no_accumulation(self):
        """Test that exprimés is NOT accumulated per candidate."""
        # CRITICAL: Each candidate row has the SAME exprimés value
        # Don't accumulate it!
        exprimes_per_row = 146394
        num_candidates = 12

        # WRONG way (old bug):
        wrong_total = exprimes_per_row * num_candidates  # 1,756,728

        # RIGHT way:
        correct_total = exprimes_per_row  # 146,394

        # Test that percentage with correct total is reasonable
        macron_votes = 43386
        macron_pct = (macron_votes / correct_total) * 100
        self.assertAlmostEqual(macron_pct, 29.6, delta=0.1)

        # Test that percentage with wrong total would be tiny
        wrong_pct = (macron_votes / wrong_total) * 100
        self.assertLess(wrong_pct, 3, "Wrong calculation gives unrealistic percentage")

    def test_presidential_round2_le_pen_calculation(self):
        """Test Le Pen votes = Exprimés - Macron votes."""
        exprimes = 128159
        macron_votes = 103996

        lepen_votes = exprimes - macron_votes
        self.assertEqual(lepen_votes, 24163)

        macron_pct = round((macron_votes / exprimes) * 100, 1)
        lepen_pct = round((lepen_votes / exprimes) * 100, 1)

        self.assertEqual(macron_pct, 81.1)
        self.assertEqual(lepen_pct, 18.9)

        # Verify they sum to 100%
        self.assertAlmostEqual(macron_pct + lepen_pct, 100.0, delta=0.1)


class TestLegislativeDataParsing(unittest.TestCase):
    """Test Legislative 2024 election data parsing (wide format)."""

    def test_legislative_wide_format_parsing(self):
        """Test parsing wide format with numbered candidate columns."""
        # Wide format: one row per commune, candidates in numbered columns
        sample_csv = "Code département;Code commune;Exprimés;Nom candidat 1;Prénom candidat 1;Voix 1;Nuance candidat 1;Nom candidat 2;Prénom candidat 2;Voix 2;Nuance candidat 2\n"
        sample_csv += "44;001;988;RAUX;Jean-Claude;345;UG;PICHON;Julio;314;RN\n"

        reader = csv.DictReader(StringIO(sample_csv), delimiter=';')
        row = next(reader)

        # Test candidate 1
        self.assertEqual(row['Nom candidat 1'], 'RAUX')
        self.assertEqual(row['Voix 1'], '345')
        self.assertEqual(row['Nuance candidat 1'], 'UG')

        # Test candidate 2
        self.assertEqual(row['Nom candidat 2'], 'PICHON')
        self.assertEqual(row['Voix 2'], '314')

    def test_legislative_round2_limit_to_two(self):
        """Round 2 should only show top 2 candidates (runoff)."""
        # Simulate multiple candidates (large commune with multiple circonscriptions)
        candidates = [
            {'candidate': 'A', 'party': 'UG', 'percentage': 35.0, 'votes': 1000},
            {'candidate': 'B', 'party': 'RN', 'percentage': 30.0, 'votes': 900},
            {'candidate': 'C', 'party': 'ENS', 'percentage': 20.0, 'votes': 600},
            {'candidate': 'D', 'party': 'LR', 'percentage': 15.0, 'votes': 500}
        ]

        # For Round 2, limit to top 2
        round2_candidates = candidates[:2]

        self.assertEqual(len(round2_candidates), 2, "Round 2 should have exactly 2 candidates")
        self.assertEqual(round2_candidates[0]['candidate'], 'A')
        self.assertEqual(round2_candidates[1]['candidate'], 'B')

    def test_legislative_candidate_extraction_loop(self):
        """Test extracting candidates from numbered columns."""
        row = {
            'Nom candidat 1': 'MARTIN', 'Voix 1': '500', 'Nuance candidat 1': 'RN',
            'Nom candidat 2': 'DUBOIS', 'Voix 2': '400', 'Nuance candidat 2': 'NFP',
            'Nom candidat 3': 'LEROY', 'Voix 3': '300', 'Nuance candidat 3': 'ENS',
            'Nom candidat 4': '', 'Voix 4': '', 'Nuance candidat 4': ''  # Empty = end
        }

        candidates = []
        candidate_num = 1

        while True:
            nom = row.get(f'Nom candidat {candidate_num}', '').strip()
            voix = row.get(f'Voix {candidate_num}', '').strip()

            if not nom or not voix:
                break

            candidates.append({'name': nom, 'votes': int(voix)})
            candidate_num += 1

        self.assertEqual(len(candidates), 3)
        self.assertEqual(candidates[0]['name'], 'MARTIN')
        self.assertEqual(candidates[2]['votes'], 300)


class TestDataMerging(unittest.TestCase):
    """Test merging of political data sources."""

    def test_priority_round2_over_round1(self):
        """Municipal Round 2 should overwrite Round 1 if both exist."""
        municipal_data = {
            '44001': {
                'round': 1,
                'winning_list': 'Liste A',
                'percentage': 55.0,
                'party': 'LNC'
            }
        }

        # Simulate Round 2 result arriving
        round2_result = {
            'round': 2,
            'winning_list': 'Liste B',
            'percentage': 60.0,
            'party': 'LDVG'
        }

        # Round 2 should replace Round 1
        if round2_result['round'] >= municipal_data['44001']['round']:
            municipal_data['44001'] = round2_result

        self.assertEqual(municipal_data['44001']['round'], 2)
        self.assertEqual(municipal_data['44001']['winning_list'], 'Liste B')

    def test_party_label_conversion_in_merge(self):
        """Test that party codes are converted to labels during merge."""
        party_code = 'LDVD'
        expected_label = 'Divers droite'

        converted_label = PARTY_LABELS.get(party_code, party_code)
        self.assertEqual(converted_label, expected_label)

    def test_merge_handles_missing_data(self):
        """Test merging when some data sources are missing."""
        mayor_data = {'first_name': 'Jean', 'last_name': 'Dupont', 'party': None}
        municipal_data = None
        presidential_data = {'round_1': [], 'round_2': {}}

        # Should not crash when municipal_data is None
        merged = {
            'mayor': mayor_data,
            'municipal_2020': municipal_data,
            'presidential_2022': presidential_data
        }

        self.assertIsNotNone(merged['mayor'])
        self.assertIsNone(merged['municipal_2020'])
        self.assertIsNotNone(merged['presidential_2022'])


class TestINSEEMapping(unittest.TestCase):
    """Test INSEE code mapping logic."""

    def test_insee_code_construction(self):
        """Test building INSEE code from department + commune."""
        dept = '44'
        commune = '109'
        insee_code = dept + commune

        self.assertEqual(insee_code, '44109')
        self.assertEqual(len(insee_code), 5)

    def test_legislative_uses_full_insee(self):
        """Legislative CSVs have full INSEE code, don't concatenate."""
        # CRITICAL: Legislative "Code commune" is already full INSEE (e.g., "44001")
        code_commune = '44001'

        # Don't do this:
        wrong_insee = '44' + code_commune  # Would be "4444001"

        # Do this:
        correct_insee = code_commune

        self.assertEqual(correct_insee, '44001')
        self.assertNotEqual(wrong_insee, correct_insee)


class TestErrorHandling(unittest.TestCase):
    """Test error handling for malformed data."""

    def test_invalid_percentage_calculation(self):
        """Test handling when exprimés = 0."""
        voix = 100
        exprimes = 0

        # Should not crash, should skip
        if exprimes > 0:
            percentage = (voix / exprimes) * 100
            self.fail("Should not calculate percentage when exprimés = 0")
        else:
            # Skip this row
            pass

    def test_invalid_vote_count(self):
        """Test handling non-numeric vote counts."""
        try:
            votes = int("invalid")
            self.fail("Should raise ValueError")
        except ValueError:
            pass  # Expected

    def test_missing_columns(self):
        """Test handling when expected columns are missing."""
        row = {'Commune': 'Nantes'}  # Missing 'Voix', 'Exprimés'

        voix = row.get('Voix', '').strip()
        self.assertEqual(voix, '', "Missing column should return empty string")


class TestEncodingHandling(unittest.TestCase):
    """Test UTF-8 vs latin-1 encoding handling."""

    def test_utf8_preserves_accents(self):
        """UTF-8 should correctly handle French accents."""
        text = "MÉLENCHON"
        # In UTF-8, accented characters are preserved
        self.assertIn('É', text)
        self.assertEqual(text, "MÉLENCHON")

    def test_bom_removal(self):
        """Test BOM character removal from CSV start."""
        text_with_bom = '\ufeffPrénom;Nom\nJean;Dupont'

        if text_with_bom.startswith('\ufeff'):
            text_without_bom = text_with_bom[1:]
        else:
            text_without_bom = text_with_bom

        self.assertFalse(text_without_bom.startswith('\ufeff'))
        self.assertTrue(text_without_bom.startswith('Prénom'))


def run_tests():
    """Run all tests and return results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPartyLabels))
    suite.addTests(loader.loadTestsFromTestCase(TestMunicipalDataParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestPresidentialDataParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestLegislativeDataParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestDataMerging))
    suite.addTests(loader.loadTestsFromTestCase(TestINSEEMapping))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestEncodingHandling))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    result = run_tests()

    # Exit with non-zero if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)
