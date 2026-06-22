import json
import pandas as pd
from agent import call_agent, run_patch_in_sandbox
from validator import run_validation

MAX_RETRIES = 2   # agent gets two attempts before giving up

def save_patch(patch_code: str, day: int):
    """Persist the successful patch to disk for reuse."""
    path = f"patch_day_{day}.py"
    with open(path, "w") as f:
        f.write(f"import pandas as pd\n\n{patch_code}\n")
    print(f"💾 Patch saved to: {path}")


def run_recovery_loop(broken_df: pd.DataFrame, error_log: dict, day: int) -> bool:
    """
    The self-healing loop:
      1. Send error log to agent → get patch function
      2. Run patch in sandbox
      3. Validate the patched DataFrame
      4. If valid → save patch + load to DuckDB
      5. If invalid → retry with new error log (max 2 attempts)
    """

    print(f"\n{'='*55}")
    print(f"  🔁 SELF-HEALING RECOVERY LOOP — Day {day}")
    print(f"{'='*55}")

    current_error_log = error_log

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"\n--- Attempt {attempt} of {MAX_RETRIES} ---")

        # Step 1: Call the LLM agent
        patch = call_agent(current_error_log)
        if patch is None:
            print("❌ Agent returned no patch. Aborting.")
            return False

        print(f"\n📋 Agent Explanation:\n   {patch.explanation}")
        print(f"\n📝 Generated Patch Code:\n{patch.patch_function}")

        # Step 2: Run patch in sandbox
        patched_df = run_patch_in_sandbox(patch.patch_function, broken_df)
        if patched_df is None:
            print("❌ Sandbox failed. Retrying with original error log...")
            continue

        # Step 3: Validate the patched result
        is_valid, new_error_log = run_validation(patched_df, day=day)

        if is_valid:
            # Step 4: Success — save patch and load into DuckDB
            print(f"\n✅ Self-healing SUCCESSFUL on attempt {attempt}!")
            save_patch(patch.patch_function, day)
            load_to_duckdb(patched_df)
            log_healing_event(day, attempt, patch.explanation)
            return True
        else:
            # Step 5: Patch didn't fully fix it — feed new errors back to agent
            print(f"\n⚠️  Patch didn't pass validation. Feeding new errors back to agent...")
            current_error_log = new_error_log   # self-correction loop

    print(f"\n❌ Recovery FAILED after {MAX_RETRIES} attempts. Manual intervention required.")
    log_healing_event(day, MAX_RETRIES, "FAILED", success=False)
    return False


def load_to_duckdb(df: pd.DataFrame):
    """Load the healed DataFrame into DuckDB."""
    import duckdb
    con = duckdb.connect("pipeline.duckdb")
    con.execute("""
        CREATE TABLE IF NOT EXISTS ad_campaigns (
            campaign_id VARCHAR,
            campaign_name VARCHAR,
            budget DOUBLE,
            impressions INTEGER,
            clicks INTEGER,
            date VARCHAR
        )
    """)
    con.execute("INSERT INTO ad_campaigns SELECT * FROM df")
    con.close()
    print("📦 Healed data loaded into DuckDB.")


def log_healing_event(day: int, attempts: int, explanation: str, success: bool = True):
    """Append a healing event to a running audit log."""
    from datetime import datetime
    entry = {
        "day": day,
        "timestamp": datetime.utcnow().isoformat(),
        "success": success,
        "attempts": attempts,
        "explanation": explanation
    }
    try:
        with open("healing_log.json", "r") as f:
            log = json.load(f)
    except FileNotFoundError:
        log = []

    log.append(entry)
    with open("healing_log.json", "w") as f:
        json.dump(log, f, indent=2)
    print(f"📓 Healing event logged to: healing_log.json")