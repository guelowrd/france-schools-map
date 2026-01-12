#!/usr/bin/env python3
"""
Run all test suites for the France Schools Map project.

Tests cover:
- Unit tests for political data parsing
- Integration tests for full data pipeline
- Data quality validation

Usage:
    python3 tests/run_all_tests.py
"""

import sys
import unittest
from pathlib import Path

# Add tests directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import test modules
import test_download_political_data
import test_integration


def main():
    """Run all test suites."""
    print("="*80)
    print("RUNNING ALL TESTS - France Schools Map")
    print("="*80)
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add unit tests
    print("Adding unit tests...")
    suite.addTests(loader.loadTestsFromModule(test_download_political_data))

    # Add integration tests
    print("Adding integration tests...")
    suite.addTests(loader.loadTestsFromModule(test_integration))

    print()
    print("="*80)
    print()

    # Run all tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print()
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print()

    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
