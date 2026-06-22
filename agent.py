import json
import os
import pandas as pd
from typing import Optional
from pydantic import BaseModel
import google.genai as genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# --------------------------------------------------------------------------
# Pydantic model — forces structured output[]
# --------------------------------------------------------------------------
class AgentPatch(BaseModel):
    patch_function: str
    explanation: str

# --------------------------------------------------------------------------
# System prompt — strict persona for the agent
# --------------------------------------------------------------------------
SYSTEM_PROMPT = """
You are an expert data engineer specializing in schema recovery.
You will be given:
  1. A broken JSON payload (sample rows from a failed pipeline run)
  2. The expected target schema (column names and their required dtypes)
  3. A structured error log describing exactly what failed

Your ONLY job is to output a JSON object with exactly two keys:
  - "patch_function": a valid Python function string named `patch_dataframe(df)`
    that takes a pandas DataFrame and returns a corrected DataFrame
    matching the target schema. Do NOT import anything inside the function.
    Assume pandas is already imported as pd.
  - "explanation": a short plain-English explanation of what was broken and what you fixed.

Output ONLY raw JSON. No markdown, no backticks, no preamble.
"""

# --------------------------------------------------------------------------
# Core agent call
# --------------------------------------------------------------------------
def call_agent(error_log):

    user_message = f"""
Here is the error log from the failed pipeline run:

{json.dumps(error_log, indent=2)}

Generate the patch_function and explanation now.
"""

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
            config={
                "system_instruction": SYSTEM_PROMPT,
                "temperature": 0,
                "max_output_tokens": 1000,
            },
        )

        raw = response.text.strip()

        if raw.startswith("```"):

            raw = raw.replace("```json", "")
            raw = raw.replace("```", "")

        parsed = json.loads(raw)

        return AgentPatch(**parsed)

    except Exception as e:

        print(f"❌ Agent call failed: {e}")

        return None


# --------------------------------------------------------------------------
# Sandbox executor
# --------------------------------------------------------------------------
def run_patch_in_sandbox(patch_code: str, df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Executes the agent-generated patch function in an isolated namespace.
    Uses exec() with a controlled local scope — never touches globals.
    """
    sandbox_globals = {"pd": pd}
    sandbox_locals  = {}

    try:
        exec(patch_code, sandbox_globals, sandbox_locals)

        if "patch_dataframe" not in sandbox_locals:
            print("❌ Sandbox error: agent did not define 'patch_dataframe'.")
            return None

        patched_df = sandbox_locals["patch_dataframe"](df.copy())
        print("🧪 Patch executed in sandbox successfully.")
        return patched_df

    except Exception as e:
        print(f"❌ Sandbox execution error: {e}")
        return None