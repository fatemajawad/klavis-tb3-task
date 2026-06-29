#!/bin/bash
# Oracle solution: copy fixed model and run
cp /solution/dbt_project/models/user_events_mart.sql /workspace/dbt_project/models/user_events_mart.sql
cd /workspace/dbt_project
dbt seed --profiles-dir .
dbt run --full-refresh --profiles-dir .
dbt run --profiles-dir .
echo "Oracle solution complete."
