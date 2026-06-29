# dbt Incremental Model Debugger

## Background

You are a data engineer at a company whose analytics platform is built on dbt + DuckDB.
The team recently shipped an incremental model `models/user_events_mart.sql` that processes
raw user events into a clean mart table used by dashboards.

**No errors are thrown at runtime**, but after each incremental refresh stakeholders report:
- Stale user records appearing (old attribute values instead of new ones)
- Unexpected row count discrepancies vs. the source table
- Soft-deleted users still appearing in downstream reports

## Your Task

Find and fix **all bugs** in the dbt project so that the automated verifier passes.

The project is located at `/workspace/dbt_project/`.

Key files:
- `models/user_events_mart.sql` — the incremental model (contains all bugs)
- `models/schema.yml` — model config
- `seeds/raw_events.csv` — source data (read-only, do not modify)
- `dbt_project.yml` — project config
- `profiles.yml` — DuckDB connection config

## Running the model

```bash
cd /workspace/dbt_project
dbt seed          # loads seed data
dbt run           # runs the incremental model (full refresh first time)
dbt run           # run again to simulate incremental refresh
```

## Verifier

The verifier will:
1. Reset the database to a clean state
2. Run your fixed model twice (simulating initial load + incremental refresh)
3. Check final row counts, deduplication correctness, soft-delete filtering, and freshness

**Reward = 1 only if ALL checks pass.**

## Hints (deliberately vague)

- Inspect what "incremental" actually means in dbt — how are new rows identified?
- Think about boundary conditions in timestamp comparisons
- Check what happens to soft-deleted records in the current merge logic
- Verify which record is selected when a user has multiple events with the same `user_id`
