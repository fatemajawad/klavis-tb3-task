# Airflow DAG Debugger

## Background

You are a data engineer on-call. The team's nightly ETL pipeline has been silently broken
for weeks. No errors appear in the Airflow UI — the DAG parses fine and tasks show green —
but stakeholders report:

- The pipeline **never runs** on the expected schedule
- When it does run manually, it processes **yesterday's data** instead of today's
- The Airflow scheduler is **sluggish** after the DAG was deployed
- Workers occasionally get **stuck** and stop picking up new tasks

The DAG is at `/workspace/dags/etl_pipeline.py`.

## Your Task

Find and fix **all bugs** in the DAG so the automated verifier passes.

```bash
# The verifier checks your fixed DAG by importing and inspecting it
# Run the verifier anytime to check your progress:
python3 /tests/verify.py
```

## What the DAG is supposed to do

- Run **daily** at midnight UTC
- Process data for the **current day** (the day the run covers, not yesterday)
- Not trigger any **backfill runs** (only future scheduled runs)
- Not block worker slots with long-running sensors

## Hints (deliberately vague)

- When does Airflow actually schedule the first DAG run relative to `start_date`?
- What does `execution_date` actually represent in Airflow 2.x?
- What happens to your scheduler when `catchup=True` and `start_date` is months ago?
- What's the difference between `poke` and `reschedule` mode in sensors?
