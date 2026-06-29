#!/bin/bash
set -e
cp /solution/train_fixed.py /workspace/pipeline/train.py
cp /solution/serve_fixed.py /workspace/pipeline/serve.py
cd /workspace
python3 pipeline/train.py
python3 /tests/verify.py
