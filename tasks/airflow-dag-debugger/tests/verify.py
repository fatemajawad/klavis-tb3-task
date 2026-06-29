#!/usr/bin/env python3
"""
Verifier for airflow-dag-debugger task.

Checks all 4 bugs by importing and inspecting the DAG:
1. start_date must be a fixed date (not datetime.now())
2. catchup must be False
3. extract_data must use data_interval_end or next_ds, not execution_date
4. FileSensor must use mode='reschedule'
"""

import sys
import os
import ast
import re
from datetime import datetime, timezone

DAG_PATH = "/workspace/dags/etl_pipeline.py"
REWARD_FILE = "/logs/verifier/reward.txt"

def write_reward(score, reason):
    os.makedirs("/logs/verifier", exist_ok=True)
    
    with open(REWARD_FILE, "w") as f:
        f.write(str(score))
    print(f"[verifier] reward={score} | {reason}")

def fail(reason):
    write_reward(0.0, reason)
    sys.exit(0)

def main():
    if not os.path.exists(DAG_PATH):
        fail(f"DAG file not found at {DAG_PATH}")

    source = open(DAG_PATH).read()

    # Parse AST for static analysis
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        fail(f"SyntaxError in DAG file: {e}")

    # CHECK 1: start_date must not use datetime.now()
    # Look for datetime.now() call anywhere in the file
    now_pattern = re.compile(r'datetime\.now\s*\(')
    if now_pattern.search(source):
        fail(
            "CHECK 1 FAILED: start_date uses datetime.now() which causes the DAG to "
            "never stabilize. Use a fixed date like datetime(2024, 1, 1)."
        )

    # CHECK 2: catchup must be False
    # Look for catchup=True
    catchup_true = re.compile(r'catchup\s*=\s*True')
    catchup_false = re.compile(r'catchup\s*=\s*False')
    if catchup_true.search(source):
        fail(
            "CHECK 2 FAILED: catchup=True with a historical start_date floods the "
            "scheduler with backfill runs. Set catchup=False."
        )
    if not catchup_false.search(source):
        fail(
            "CHECK 2 FAILED: catchup must be explicitly set to False."
        )

    # CHECK 3: extract_data must use data_interval_end or next_ds, not execution_date
    # Find the extract_data function body
    func_match = re.search(
        r'def extract_data\s*\([^)]*\).*?(?=\ndef |\Z)',
        source,
        re.DOTALL
    )
    if not func_match:
        fail("CHECK 3 FAILED: extract_data function not found.")

    func_body = func_match.group(0)

    # Must NOT use execution_date for the processing date
    if re.search(r'execution_date', func_body) and not re.search(r'data_interval_end|next_ds', func_body):
        fail(
            "CHECK 3 FAILED: extract_data uses execution_date which is the START of "
            "the data interval (yesterday). Use data_interval_end or next_ds to get "
            "the end of the current processing window."
        )

    # Must use data_interval_end or next_ds
    if not re.search(r'data_interval_end|next_ds', func_body):
        fail(
            "CHECK 3 FAILED: extract_data must use context['data_interval_end'] or "
            "context['next_ds'] to process the correct time window."
        )

    # CHECK 4: FileSensor must use mode='reschedule'
    poke_mode = re.compile(r"mode\s*=\s*['\"]poke['\"]")
    reschedule_mode = re.compile(r"mode\s*=\s*['\"]reschedule['\"]")

    if poke_mode.search(source):
        fail(
            "CHECK 4 FAILED: FileSensor uses mode='poke' which blocks a worker slot "
            "for the entire sensor duration. Use mode='reschedule' to release the "
            "worker between checks."
        )
    if not reschedule_mode.search(source):
        fail(
            "CHECK 4 FAILED: FileSensor must explicitly set mode='reschedule'."
        )

    write_reward(1.0, "All 4 checks passed: fixed start_date, catchup=False, correct time window, reschedule mode.")

if __name__ == "__main__":
    main()
