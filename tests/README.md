# Test Suite for France Schools Map

Automated tests to ensure data integrity and prevent regressions when adding new features.

## Test Files

### Python Tests (`test_data_validation.py`)
Validates the data pipeline output (`data/schools.json`):

✅ **Data Structure Tests**
- File exists and is valid JSON
- School count is reasonable (2500-4000)
- All required fields present
- UAI codes have valid format (7 digits + 1 letter)

✅ **Geographic Tests**
- All coordinates are within Pays de la Loire bounds
- Latitude: 46.2°N to 48.6°N
- Longitude: -2.6°E to 1.0°E (includes Sarthe/Le Mans area)

✅ **School Type Tests**
- Valid types: Primaire, Collège, Lycée
- Distribution follows expected ratios (Primaire > Collège > Lycée)
- No professional lycées in dataset

✅ **Data Coverage Tests**
- IPS coverage >80% (currently ~92%)
- Enrollment coverage >40% (currently ~54%)
- IPS values in reasonable range (30-200 or "NS")
- Enrollment values reasonable (no multi-year aggregation bug)

✅ **Data Quality Tests**
- Primary schools with enrollment have calculated class sizes
- All data sources include dates/years
- No duplicate UAI codes

### Frontend Tests (`test_frontend.js`)
Validates that the frontend can load and display data correctly:

✅ **Load Tests**
- schools.json is valid JSON array
- File size is reasonable (1-10 MB)

✅ **Display Tests**
- All schools have required fields for map display
- Coordinates are valid numbers
- Popup content can be generated for all schools
- Marker colors defined for all school types

✅ **Data Structure Tests**
- IPS data structure valid where present (handles "NS" values)
- Enrollment data structure valid where present
- Class size calculation correct for primary schools
- Exam results structure valid where present

✅ **Integrity Tests**
- No duplicate UAI codes

## Running Tests

### Run All Tests
```bash
./tests/run_tests.sh
```

### Run Individual Tests
```bash
# Python data validation tests
python3 tests/test_data_validation.py

# Frontend validation tests
node tests/test_frontend.js
```

## When to Run Tests

**Always run tests before:**
1. Committing data changes
2. Adding new data sources (e.g., real estate prices)
3. Modifying merge logic
4. Pushing to GitHub

**Command:**
```bash
./tests/run_tests.sh && git add . && git commit
```

## Common Test Failures and Fixes

### "Invalid coordinates" Error
**Cause:** School coordinates outside expected region bounds
**Fix:** Check if bounds need adjustment or if school is incorrectly included

### "IPS value not a number" Error
**Cause:** IPS value is "NS" (Non Significatif) or non-numeric
**Fix:** Tests now handle "NS" values - if you see this error, there's a new invalid value

### "Suspiciously high enrollment" Error
**Cause:** Multi-year aggregation bug (summing across years instead of taking most recent)
**Fix:** Check `download_enrollment_data.py` - ensure filtering by most recent year BEFORE aggregating

### "Duplicate UAI codes" Error
**Cause:** Schools with multiple campuses sharing same UAI
**Fix:** Deduplication logic in `merge_datasets.py` should keep main campus only

### "No professional lycées" Failed
**Cause:** Professional lycées slipped through filters
**Fix:** Update filters in `download_data.py` to exclude professional schools

## Test Coverage

Current coverage:
- ✅ Data structure validation
- ✅ Geographic bounds checking
- ✅ Data coverage metrics
- ✅ Data quality checks
- ✅ Frontend compatibility
- ✅ Regression prevention (multi-year aggregation, professional lycées, duplicates)

Future additions (when adding real estate data):
- Add tests for real estate price ranges
- Validate real estate data joins correctly by city/canton/department
- Check for missing real estate data coverage

## Continuous Integration (Optional)

To run tests automatically on every commit, you can set up:

### GitHub Actions
Create `.github/workflows/test.yml`:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - uses: actions/setup-node@v2
        with:
          node-version: '16'
      - run: ./tests/run_tests.sh
```

### Pre-commit Hook
Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
./tests/run_tests.sh
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

## Adding New Tests

When adding new features (e.g., real estate prices):

1. **Add Python validation tests** in `test_data_validation.py`:
```python
def test_real_estate_data_coverage():
    """Test real estate data coverage"""
    schools = load_schools()
    with_real_estate = sum(1 for s in schools if s.get('real_estate_price'))
    # Add assertions
```

2. **Add frontend validation tests** in `test_frontend.js`:
```javascript
test('Real estate prices valid where present', () => {
    const schoolsWithPrices = schools.filter(s => s.real_estate_price);
    // Add assertions
});
```

3. **Update this README** with new test descriptions

## Test Philosophy

These tests are designed to:
- ✅ Catch regressions early
- ✅ Validate data pipeline correctness
- ✅ Ensure frontend compatibility
- ✅ Document expected data structure
- ✅ Make future changes safer

The tests are **fast** (~5 seconds total) so you can run them frequently!
