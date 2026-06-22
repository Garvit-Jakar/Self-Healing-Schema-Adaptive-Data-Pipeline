import sys
from mock_data import generate_mock_data
from validator import run_validation
from recovery import run_recovery_loop
import pandas as pd
import duckdb

DB_PATH = "pipeline.duckdb"

def load_data(day: int = 1):
    
    raw_data = generate_mock_data(day=day)
    df = pd.DataFrame(raw_data)

    is_valid, error_log = run_validation(df, day=day)

    if not is_valid:
        print("⛔ Validation failed. Handing off to recovery agent...")
        success = run_recovery_loop(df, error_log, day=day)
        if not success:
            print("🚨 Pipeline could not self-heal. Check healing_log.json.")
    else:
        # Normal path — load directly
        con = duckdb.connect(DB_PATH)
        con.execute("""
            CREATE TABLE IF NOT EXISTS ad_campaigns (
                campaign_id VARCHAR, campaign_name VARCHAR,
                budget DOUBLE, impressions INTEGER,
                clicks INTEGER, date VARCHAR
            )
        """)
        con.execute("INSERT INTO ad_campaigns SELECT * FROM df")
        con.close()
        print(f"✅ Day {day}: {len(df)} records written to DuckDB.")

if __name__ == "__main__":
    day = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    load_data(day=day)