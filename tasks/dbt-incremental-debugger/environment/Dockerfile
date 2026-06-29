FROM python:3.11-slim

RUN pip install --no-cache-dir dbt-duckdb==1.8.1 duckdb==0.10.3

WORKDIR /workspace

COPY dbt_project/ /workspace/dbt_project/

# Make seeds read-only so agents can't cheat by modifying source data
RUN chmod 444 /workspace/dbt_project/seeds/raw_events.csv

CMD ["/bin/bash"]
