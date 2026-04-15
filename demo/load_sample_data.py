"""Load sample ESG assessment data into the SQLite database."""

import sys
from pathlib import Path
from typing import Dict, List
import pandas as pd

# Add src to path so we can import database module
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src import database


# GRI Indicator mapping: code -> (name, category)
GRI_INDICATOR_MAP: Dict[str, tuple[str, str]] = {
    "GRI 201": ("Economic Performance", "Economic"),
    "GRI 205": ("Anti-corruption", "Governance"),
    "GRI 206": ("Anti-competitive Behavior", "Governance"),
    "GRI 301": ("Materials", "Environmental"),
    "GRI 302": ("Energy Management", "Environmental"),
    "GRI 303": ("Water Management", "Environmental"),
    "GRI 305": ("Emissions", "Environmental"),
    "GRI 306": ("Waste Management", "Environmental"),
    "GRI 401": ("Employment", "Social"),
    "GRI 403": ("Occupational Health and Safety", "Social"),
    "GRI 404": ("Training and Development", "Social"),
    "GRI 405": ("Diversity and Inclusion", "Social"),
    "GRI 413": ("Community Relations", "Social"),
}


def initialize_gri_indicators() -> Dict[str, int]:
    """Seed GRI indicators into database and return code->id mapping."""
    print("Initializing GRI indicators...")
    indicator_ids: Dict[str, int] = {}

    for code, (name, category) in GRI_INDICATOR_MAP.items():
        database.upsert_gri_indicator(code, name, category, f"GRI {code} standard")

    # Fetch all indicators to build mapping
    indicators = database.get_gri_indicators()
    for indicator in indicators:
        indicator_ids[indicator["code"]] = indicator["id"]

    print(f"  Initialized {len(indicator_ids)} GRI indicators")
    return indicator_ids


def load_suppliers(df: pd.DataFrame) -> Dict[str, int]:
    """Load unique suppliers into database and return name->id mapping."""
    print("Loading suppliers...")
    supplier_ids: Dict[str, int] = {}

    # Get unique suppliers from dataframe
    unique_suppliers = df[["supplier_name", "location", "sector"]].drop_duplicates()

    for _, row in unique_suppliers.iterrows():
        supplier_name: str = row["supplier_name"]
        location: str = row["location"]
        sector: str = row["sector"]

        # Create supplier and store mapping
        supplier_id = database.create_supplier(supplier_name, location, sector)
        supplier_ids[supplier_name] = supplier_id

    print(f"  Loaded {len(supplier_ids)} unique suppliers")
    return supplier_ids


def load_assessments(
    df: pd.DataFrame,
    supplier_ids: Dict[str, int],
    indicator_ids: Dict[str, int],
) -> int:
    """Load assessments into database and return count."""
    print("Loading assessments...")
    assessment_count = 0

    for _, row in df.iterrows():
        supplier_name: str = row["supplier_name"]
        gri_code: str = row["gri_indicator_code"]

        supplier_id = supplier_ids.get(supplier_name)
        indicator_id = indicator_ids.get(gri_code)

        if not supplier_id:
            print(f"  WARNING: Supplier '{supplier_name}' not found, skipping row")
            continue

        if not indicator_id:
            print(f"  WARNING: GRI indicator '{gri_code}' not found, skipping row")
            continue

        score: float = float(row["score"])
        evidence_notes: str = str(row["evidence_notes"])
        assessed_date: str = str(row["assessed_date"])
        assessor: str = str(row["assessor"])

        try:
            database.create_assessment(
                supplier_id=supplier_id,
                indicator_id=indicator_id,
                score=score,
                evidence_notes=evidence_notes,
                assessed_date=assessed_date,
                assessor=assessor,
            )
            assessment_count += 1
        except Exception as e:
            print(f"  ERROR inserting assessment: {e}")
            continue

    print(f"  Loaded {assessment_count} assessments")
    return assessment_count


def print_summary_statistics() -> None:
    """Print summary statistics of loaded data."""
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)

    suppliers = database.get_suppliers()
    assessments = database.get_assessments()

    print(f"Total Suppliers: {len(suppliers)}")
    print(f"Total Assessments: {len(assessments)}")

    if assessments:
        scores = [a["score"] for a in assessments]
        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)

        print(f"\nScore Statistics:")
        print(f"  Average: {avg_score:.2f}")
        print(f"  Minimum: {min_score:.2f}")
        print(f"  Maximum: {max_score:.2f}")

        # Group by category
        print(f"\nAssessments by Category:")
        category_groups: Dict[str, List[float]] = {}
        for assessment in assessments:
            category = assessment["category"]
            score = assessment["score"]
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(score)

        for category in sorted(category_groups.keys()):
            scores_in_cat = category_groups[category]
            avg_cat = sum(scores_in_cat) / len(scores_in_cat)
            print(f"  {category}: {len(scores_in_cat)} assessments, avg {avg_cat:.2f}")

        # Group by supplier
        print(f"\nAssessments by Supplier (top 5):")
        supplier_counts: Dict[str, int] = {}
        for assessment in assessments:
            supplier = assessment["supplier_name"]
            supplier_counts[supplier] = supplier_counts.get(supplier, 0) + 1

        for supplier, count in sorted(
            supplier_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]:
            print(f"  {supplier}: {count} assessments")

    print("=" * 60 + "\n")


def main() -> None:
    """Main entry point for loading sample data."""
    print("\n" + "=" * 60)
    print("ESG Sample Data Loader")
    print("=" * 60 + "\n")

    # Initialize database
    database.initialize_database()

    # Define CSV path
    csv_path = Path(__file__).parent / "sample_data.csv"

    if not csv_path.exists():
        print(f"ERROR: Sample data file not found at {csv_path}")
        sys.exit(1)

    print(f"Loading data from: {csv_path}\n")

    # Read CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"ERROR reading CSV: {e}")
        sys.exit(1)

    print(f"Read {len(df)} rows from CSV")

    # Validate required columns
    required_columns = {
        "supplier_name",
        "location",
        "sector",
        "gri_indicator_code",
        "gri_indicator_name",
        "gri_category",
        "score",
        "evidence_notes",
        "assessed_date",
        "assessor",
    }
    if not required_columns.issubset(set(df.columns)):
        missing = required_columns - set(df.columns)
        print(f"ERROR: Missing required columns: {missing}")
        sys.exit(1)

    print(f"CSV validation passed\n")

    # Load data
    try:
        indicator_ids = initialize_gri_indicators()
        supplier_ids = load_suppliers(df)
        assessment_count = load_assessments(df, supplier_ids, indicator_ids)

        # Print results
        print_summary_statistics()

        print("SUCCESS: Data loading completed!")

    except Exception as e:
        print(f"\nERROR during data loading: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
