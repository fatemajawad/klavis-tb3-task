FROM python:3.11-slim

RUN pip install --no-cache-dir dbt-duckdb==1.8.1 duckdb==0.10.3

WORKDIR /workspace
COPY dbt_project/ /workspace/dbt_project/
COPY solve.sh /solution/solve.sh
COPY dbt_project/models/user_events_mart.sql /solution/dbt_project/models/user_events_mart.sql

RUN chmod +x /solution/solve.sh

CMD ["/solution/solve.sh"]
