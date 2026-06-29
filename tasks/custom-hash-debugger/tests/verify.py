#!/usr/bin/env python3
"""
Verifier for custom-hash-debugger.

Builds the C extension, runs 500 test cases, checks exact outputs
against pre-computed ground truth from the correct implementation.
All 500 must match exactly. No partial credit.
"""

import sys
import os
import json
import subprocess

REWARD_FILE = "/logs/verifier/reward.txt"
GROUND_TRUTH = "/tests/ground_truth.json"
SRC_DIR = "/workspace"

def write_reward(score, reason):
    os.makedirs("/logs/verifier", exist_ok=True)
    with open(REWARD_FILE, "w") as f:
        f.write(str(score))
    print(f"[verifier] reward={score} | {reason}")

def fail(reason):
    write_reward(0.0, reason)
    sys.exit(0)

def main():
    # Step 1: Build the C extension
    print("[verifier] Building C extension...")
    result = subprocess.run(
        ["python3", "setup.py", "build_ext", "--inplace"],
        capture_output=True, text=True, cwd=SRC_DIR
    )
    if result.returncode != 0:
        fail(f"Build failed:\n{result.stderr[-800:]}")

    # Step 2: Import the built module
    sys.path.insert(0, SRC_DIR)
    # Force reimport
    if "fasthash" in sys.modules:
        del sys.modules["fasthash"]
    
    try:
        import fasthash
    except ImportError as e:
        fail(f"Cannot import fasthash after build: {e}")

    # Step 3: Load ground truth
    with open(GROUND_TRUTH) as f:
        test_cases = json.load(f)

    print(f"[verifier] Running {len(test_cases)} hash test cases...")

    # Step 4: Check all outputs
    failures = []
    for i, tc in enumerate(test_cases):
        got = fasthash.hash_string(tc["input"], tc["seed"])
        expected = tc["expected"]
        if got != expected:
            failures.append({
                "index": i,
                "input": tc["input"],
                "seed": tc["seed"],
                "got": got,
                "expected": expected
            })

    if failures:
        n = len(failures)
        f0 = failures[0]
        fail(
            f"CHECK FAILED: {n}/500 hash outputs are wrong. "
            f"First failure — input='{f0['input']}', seed={f0['seed']}: "
            f"got {f0['got']}, expected {f0['expected']}. "
            f"Hint: check bit rotation direction in the body block mixing step."
        )

    write_reward(1.0, "All 500 hash outputs match ground truth exactly.")

if __name__ == "__main__":
    main()
