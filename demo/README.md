# ESG Sample Data Demo

This directory contains sample data and utilities for demonstrating the ESG Data Collector system with realistic Indonesian company data.

## Files

### sample_data.csv

Contains 25 rows of realistic ESG assessment data for Indonesian companies:

- **25 assessments** across 12 unique suppliers
- **Suppliers**: Major Indonesian companies (PT Sinar Mas Agro, PT Pertamina Persero, PT Telkom Indonesia, PT Astra International, etc.)
- **Sectors**: Mining, Palm Oil, Telecommunications, Automotive, Banking, Food & Beverage, Heavy Equipment, Energy, Petrochemicals, Pharmaceuticals
- **GRI Indicators**: 13 different GRI standards (201, 205, 206, 301, 302, 303, 305, 306, 401, 403, 404, 405, 413)
- **Score Range**: 68-88 (realistic ESG assessment scores)
- **Assessment Dates**: January 2025 through March 2026
- **Assessors**: Indonesian names (Budi Santoso, Siti Nurhaliza, Ahmad Fauzi, Dewi Lestari, Rudi Hartono)

### load_sample_data.py

Python script to load sample_data.csv into the SQLite database.

**Features:**
- Type-annotated with full return types
- Immutable patterns (no in-place mutations)
- GRI indicator seeding with mapping
- Comprehensive error handling
- Summary statistics reporting

**Usage:**

```bash
python3 load_sample_data.py
```

**Output:**
- Creates/initializes `esg_data.db` SQLite database
- Seeds 13 GRI indicators
- Loads 12 suppliers
- Loads 25 assessments
- Prints summary statistics including:
  - Total suppliers and assessments
  - Score statistics (avg, min, max)
  - Breakdown by ESG category (Economic, Environmental, Social, Governance)
  - Top suppliers by assessment count

## Data Quality

All sample data is:
- **Realistic**: Reflects actual ESG assessment patterns
- **Consistent**: Valid dates, score ranges, and indicator codes
- **Representative**: Covers multiple sectors, regions, and ESG categories
- **Traceable**: Includes evidence notes and assessor names

## GRI Indicators Included

- **Economic (GRI 200)**: Economic Performance (201), Anti-corruption (205), Anti-competitive Behavior (206)
- **Environmental (GRI 300)**: Materials (301), Energy (302), Water (303), Emissions (305), Waste (306)
- **Social (GRI 400)**: Employment (401), Health & Safety (403), Training (404), Diversity (405), Communities (413)
- **Governance**: Covered by anti-corruption and anti-competitive behavior indicators

## Database Schema

The loader creates/uses the following tables:

- `suppliers`: Company information (name, location, sector)
- `gri_indicators`: GRI standard definitions (code, name, category)
- `esg_assessments`: Assessment records linking suppliers to indicators
- `evidence_files`: Optional storage for supporting documentation

## Next Steps

After loading sample data:

1. Verify data in database: `sqlite3 esg_data.db "SELECT COUNT(*) FROM esg_assessments;"`
2. Run analysis queries on assessment trends
3. Build dashboards using the assessment data
4. Test filtering and aggregation logic
