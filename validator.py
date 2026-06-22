import pandas as pd
import json
from datetime import datetime

# The "golden" schema your pipeline always expects
TARGET_SCHEMA = {
    "campaign_id": "object",       # string/VARCHAR
    "campaign_name": "object",
    "budget": "float64",           # must be numeric
    "impressions": "int64",
    "clicks": "int64",
    "date": "object"
}

def validate_dataframe(df: pd.DataFrame, day: int = 1) -> dict:
    """
    Validates a DataFrame against the target schema.
    Returns a structured error log if validation fails, or a success dict.
    """
    errors = []

    # Check 1: Missing columns
    for col in TARGET_SCHEMA:
        if col not in df.columns:
            errors.append({
                "rule": "column_exists",
                "column": col,
                "message": f"Expected column '{col}' is missing from the payload.",
                "found_columns": list(df.columns)
            })

    # Check 2: Unexpected extra columns (potential renames)
    expected_cols = set(TARGET_SCHEMA.keys())
    actual_cols = set(df.columns)
    unexpected = actual_cols - expected_cols
    if unexpected:
        errors.append({
            "rule": "no_extra_columns",
            "column": list(unexpected),
            "message": f"Unexpected columns found (possible renames): {unexpected}"
        })

    # Check 3: Data type validation (only for columns that exist)
    for col, expected_dtype in TARGET_SCHEMA.items():
        if col in df.columns:
            actual_dtype = str(df[col].dtype)
            if actual_dtype != expected_dtype:
                errors.append({
                    "rule": "correct_dtype",
                    "column": col,
                    "expected_dtype": expected_dtype,
                    "actual_dtype": actual_dtype,
                    "sample_values": df[col].head(3).tolist(),
                    "message": f"Column '{col}' expected dtype '{expected_dtype}' but got '{actual_dtype}'."
                })

    # Check 4: No nulls in critical columns
    critical_columns = ["campaign_id", "budget", "impressions"]
    for col in critical_columns:
        if col in df.columns and df[col].isnull().any():
            errors.append({
                "rule": "no_nulls",
                "column": col,
                "null_count": int(df[col].isnull().sum()),
                "message": f"Critical column '{col}' contains null values."
            })

    # Build the result
    if errors:
        error_log = {
            "status": "FAILED",
            "day": day,
            "timestamp": datetime.utcnow().isoformat(),
            "total_errors": len(errors),
            "errors": errors,
            "broken_payload_sample": df.head(2).to_dict(orient="records"),
            "expected_schema": TARGET_SCHEMA
        }
        return error_log
    else:
        return {
            "status": "PASSED",
            "day": day,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "All validations passed. Data loaded successfully."
        }


def run_validation(df: pd.DataFrame, day: int = 1) -> tuple[bool, dict]:
    """
    Runs validation and prints results. Returns (is_valid, error_log).
    """
    result = validate_dataframe(df, day=day)

    if result["status"] == "FAILED":
        print(f"\n🚨 Validation FAILED on Day {day} — {result['total_errors']} error(s) detected.")
        print(json.dumps(result, indent=2))
        # Save error log to disk for the agent to pick up later
        log_path = f"error_log_day_{day}.json"
        with open(log_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n📝 Error log saved to: {log_path}")
        return False, result
    else:
        print(f"\n✅ Validation PASSED on Day {day}.")
        return True, result