# Tests - France Schools Map

Comprehensive test suite to ensure data integrity and prevent regressions when setting up new regions.

## Test Coverage

### Unit Tests (`test_download_political_data.py`)

Tests for individual components of the political data download pipeline:

- **Party Labels** (3 tests)
- **Municipal Data Parsing** (4 tests)
- **Presidential Data Parsing** (5 tests)
- **Legislative Data Parsing** (3 tests)
- **Data Merging** (3 tests)
- **INSEE Code Mapping** (2 tests)
- **Error Handling** (3 tests)
- **Encoding** (2 tests)

**Total: 24 unit tests**

### Integration Tests (`test_integration.py`)

Tests for complete data pipeline and output quality (10 tests)

## Running Tests

### Run All Tests
```bash
python3 tests/run_all_tests.py
```

### Run Unit Tests Only
```bash
python3 tests/test_download_political_data.py
```

### Run Integration Tests Only
```bash
python3 tests/test_integration.py
```

## Critical Tests for New Regions

When adapting for a new region, pay attention to:

1. **Delimiter Detection** - Different sources use TAB, semicolon, or comma
2. **Encoding** - Round 1 UTF-8, Round 2 latin-1
3. **Percentage Bug** - Don't accumulate exprimés per candidate
4. **INSEE Codes** - Legislative CSVs already have full code
5. **Legislative Round 2** - Limit to top 2 candidates only
6. **Presidential Round 2** - Calculate Le Pen from (Exprimés - Macron)

## Test Results

✅ 34 total tests passing (24 unit + 10 integration)
