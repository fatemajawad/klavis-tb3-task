#!/bin/bash
# Oracle: copy fixed DAG into place
cp /solution/etl_pipeline_fixed.py /workspace/dags/etl_pipeline.py
echo "Oracle solution applied."
python3 /tests/verify.py
