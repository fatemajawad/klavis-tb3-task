#!/bin/bash
set -e
# Fix the bit shift bug: change >> 31 to << 31 in body block
sed -i 's/k = (k >> 31) | (k << (64 - 31));/k = (k << 31) | (k >> (64 - 31));/' /workspace/src/fasthash.c
cd /workspace
python3 setup.py build_ext --inplace
python3 /tests/verify.py
