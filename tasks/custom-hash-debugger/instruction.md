# Custom Hash Function Debugger

## Background

Your data pipeline uses a custom 64-bit hash function (`fastHash64`) implemented as a
Python C extension for performance. It generates deterministic row IDs for deduplication.

A colleague recently "optimized" the function and introduced a bug. The function now
produces wrong hash values, breaking row ID generation downstream. No crash occurs —
the function runs fine and returns numbers, just the wrong ones.

## Your Task

Fix the bug in `/workspace/src/fasthash.c`, recompile, and verify all test vectors match.

```bash
cd /workspace

# Rebuild after fixing
python3 setup.py build_ext --inplace

# Run verifier
python3 /tests/verify.py
```

## What you know

- The function is a modified MurmurHash3 finalizer
- The bug is in the **bit rotation logic** in the body block processing
- A correct bit rotation left by N bits on a 64-bit integer looks like:
  `(x << N) | (x >> (64 - N))`
- The verifier checks 500 exact expected hash values — all must match

## Files

- `/workspace/src/fasthash.c` — the C source (contains the bug)
- `/workspace/setup.py` — build script
