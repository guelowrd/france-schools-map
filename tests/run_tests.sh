#!/bin/bash
# Test runner script
# Run all tests and report results

echo "========================================="
echo "Running France Schools Map Test Suite"
echo "========================================="
echo ""

# Track overall success
ALL_PASSED=true

# Run Python data validation tests
echo "▶ Running Python data validation tests..."
python3 tests/test_data_validation.py
if [ $? -ne 0 ]; then
    ALL_PASSED=false
fi
echo ""

# Run frontend validation tests
echo "▶ Running frontend validation tests..."
node tests/test_frontend.js
if [ $? -ne 0 ]; then
    ALL_PASSED=false
fi
echo ""

# Summary
echo "========================================="
if [ "$ALL_PASSED" = true ]; then
    echo "✅ ALL TESTS PASSED"
    echo "========================================="
    exit 0
else
    echo "❌ SOME TESTS FAILED"
    echo "========================================="
    exit 1
fi
