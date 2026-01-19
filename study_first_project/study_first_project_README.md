# Dollar Exchange Data Pipeline (Study First Project)

Overview
--------
This project demonstrates a small end-to-end data engineering pipeline that collects real-world USD→BRL exchange data from a public API and persists it into a Postgres data warehouse. The pipeline is scheduled with Apache Airflow to run every 15 minutes to ingest fresh data, then uses dbt to transform the raw data into curated tables. Finally, Metabase is connected to the Postgres instance to visualize the data in a simple dashboard that refreshes every 15 minutes.

This repository is meant as a portfolio piece to showcase:
- Dockerized multi-service local environment
- Airflow-based orchestration with a DAG that coordinates ingestion and transformation tasks
- dbt models for Bronze→Silver transformations
- Basic data ingestion code (requests → Postgres)
- End-to-end demo using Metabase for visualization

Table of contents
-----------------
- Architecture and components
- Prerequisites
- Quick start (run locally)
- Project structure and key files
- Airflow DAG explanation
- Data ingestion implementation (api_request)
- DB schema and dbt models
- Metabase: connecting and dashboard
- Recommended fixes & improvements (important)
- Security & sensitive data
- Troubleshooting
- How to present this project in your portfolio
- Next steps and enhancements
- License

Architecture and components
---------------------------
High level components:
- Postgres (data warehouse)
- Apache Airflow (orchestration)
- dbt (transformations)
- Metabase (dashboard & visualization)
- A simple Python module (api_request) that fetches USD→BRL quotes and inserts them into Postgres

Docker-compose defines four main services:
- postgres — Postgres database (db_projeto_1)
- airflow — Airflow webserver + scheduler (standalone)
- dbt — dbt image to run models
- metabase — dashboard service

The Airflow DAG (dolar_api_orchestrator) triggers:
1. A PythonOperator that runs the ingestion logic (calls api_request/insert_records)
2. A DockerOperator to run dbt (transformation) in a dbt Docker image
The DAG runs every 15 minutes.

Prerequisites
-------------
- Docker and Docker Compose (docker-compose V2 recommended). Ensure docker daemon is running.
- (Optional) Python 3.10+ if you want to run parts locally without Docker.
- At least ~2–4GB free memory for local stack.
- Internet access for the API: https://economia.awesomeapi.com.br/json/daily/USD-BRL/15

Quick start (run locally)
-------------------------
1. Clone repository:
   git clone https://github.com/pedrocaroli/lakehouse_project.git
   cd lakehouse_project/study_first_project

2. Review and (recommended) create a .env file with credentials (see Security & sensitive data). Update docker-compose.yml to reference env vars if you change defaults.

3. Start services:
   docker compose up -d

4. Watch logs:
   docker compose logs -f airflow
   docker compose logs -f postgres
   docker compose logs -f dbt

5. Access services:
   - Airflow UI: http://localhost:8080 (default standalone)
   - Metabase: http://localhost:3000
   - Postgres: connect on port 5432

6. Trigger DAG or wait for schedule:
   - The DAG is scheduled to run every 15 minutes. You can also trigger manually in the Airflow UI.

Project structure & key files
-----------------------------
- docker-compose.yml — service definitions for Postgres, Airflow, dbt, Metabase
- airflow/
  - dags/orchestrator.py — Airflow DAG coordinating ingestion and dbt run
  - (airflow Dockerfile and requirements)
- api_request/
  - api_request.py — function that calls the external API
  - insert_records.py — connects to Postgres and inserts records
- dbt/my_project/ — dbt project
  - models/sources/bronze_cotacao_data.sql — bronze model (select * from source)
  - models/sources/silver_cotacao.sql — silver deduplicated model
  - profiles.yml — dbt profiles (contains DB connection)
  - dbt_project.yml — dbt project config
- metabase-data/ — (local metabase DB data)

Airflow DAG (orchestrator.py) explained
--------------------------------------
Key aspects:
- DAG id: `dolar_api_orchestrator`
- schedule: every 15 minutes (timedelta(minutes=15))
- task 1: PythonOperator `data_ingestion_dolar_api` runs run_ingestion()
  - run_ingestion() appends `/opt/airflow/api_request` to sys.path and imports `main` from `insert_records`.
  - It then calls `main()`.
- task 2: DockerOperator `transform_data` created by build_dbt_task() runs dbt in a container:
  - image: `ghcr.io/dbt-labs/dbt-postgres:1.9.latest`
  - mounts local dbt project and profiles.yml into the dbt image
  - command: `run --project-dir /usr/app --profiles-dir /root/.dbt`
  - network_mode and mount paths are currently hardcoded and may require changes (see Recommended fixes).

Data ingestion implementation
----------------------------
- api_request/api_request.py
  - fetch_data() requests the last 15 daily USD-BRL quotes:
    GET https://economia.awesomeapi.com.br/json/daily/USD-BRL/15
  - Returns parsed JSON array or prints an error if the request fails.
- api_request/insert_records.py
  - connect_to_db() uses psycopg2 to connect to Postgres.
  - create_table() creates `dev.raw_cotacao_data` (schema dev).
  - insert_values() inserts a batch of rows into dev.raw_cotacao_data via psycopg2.extras.execute_values.
  - main() orchestrates fetch → connect → create_table → insert_values → close connection

DB schema and dbt models
------------------------
- Database: db_projeto_1
- Schema: dev
- Raw table: dev.raw_cotacao_data (created in create_table)
  - columns: code TEXT, codein TEXT, name TEXT, high FLOAT, low FLOAT, create_date TIMESTAMP, timestamp BIGINT
- dbt project
  - sources.yml points to database `db_projeto_1` and schema `dev`, table `raw_cotacao_data`
  - bronze_cotacao_data.sql → `select * from {{ source('dev','raw_cotacao_data') }}`
  - silver_cotacao.sql → deduplicates by (code, timestamp) keeping latest create_date, constructs an `id` as concat(code, '_', timestamp)

Metabase (dashboard)
--------------------
- Add a new Postgres database in Metabase UI:
  - Host: `postgres` (or `localhost` if Metabase runs outside compose; when using compose the internal network name is `postgres`)
  - Port: 5432
  - Database name: `db_projeto_1`
  - Username & password: see docker-compose environment (defaults in repository)
- Create a simple question/dashboard:
  - Example: Time series of `high` and `low` from `dev.silver_cotacao` (or the dbt models after run)
  - Set dashboard refresh to 15 minutes
  - Expose charts/screenshots as portfolio artifacts

Recommended fixes & improvements (important)
--------------------------------------------
While the project is functional as a prototype, there are a number of important code and configuration fixes you should make before presenting this project:

1) insert_records.py should NOT call main() at import time
   - Problem: Currently insert_records.py ends with `main()` executed at module import. This means importing from insert_records will execute the ingestion immediately and makes the code run twice when the DAG calls main() (or hard to manage).
   - Fix: Wrap the script-level call with:
     ```python
     if __name__ == "__main__":
         main()
     ```
   - This ensures `from insert_records import main` only imports the function and does not run ingestion immediately.

2) Avoid double execution in DAG
   - If you fix (1), the DAG's call flow `from insert_records import main` then `main()` will behave correctly.

3) Use environment variables and not hard-coded credentials
   - The repository currently contains plaintext DB credentials. Move secrets to environment variables or Docker secrets and reference them in docker-compose and dbt `profiles.yml`.
   - Example in docker-compose:
     ```yaml
     environment:
       POSTGRES_USER: ${POSTGRES_USER}
       POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
       POSTGRES_DB: ${POSTGRES_DB}
     ```
   - Replace passwords in dbt/profiles.yml with references to env vars or a secure profile.

4) DockerOperator mount paths & network names (Airflow)
   - In orchestrator.py, build_dbt_task uses absolute paths such as `/home/caroli/lakehouse-workspace/study_first_project/dbt/my_project` and `network_mode='study_first_project_my-network'`.
   - These are user-specific and will break on other machines. Replace with:
     - Use relative paths mounted into the Airflow container via docker-compose (already in docker-compose.yml: `- ./dbt/my_project:/usr/app`)
     - In the DockerOperator, prefer not to hardcode host-specific source mounts. Instead, mount the same paths that your Airflow container already exposes, or run dbt from a separate dbt service (as defined in docker-compose.yml).
   - Also ensure `auto_remove` value is boolean True/False, not `'success'`. DockerOperator expects boolean in some provider versions.

5) Airflow Dockerfile typos
   - The file study_first_project/airflow/docker-file contains lowercase keywords and likely incorrect syntax:
     ```
     from apache/airflow:2.7.2-python3
     user root
     copy requirements.txt .
     RUN pip install --no-cache-dir -r requirements.txt
     USER airflow
     ```
   - Dockerfile instructions are case sensitive and should be uppercase (FROM, USER, COPY). Consider renaming to Dockerfile and fixing syntax.

6) dbt profiles & DB connectivity
   - dbt/my_project/profiles.yml currently contains DB credentials in plaintext. Use env var interpolation:
     ```yaml
     dev:
       type: postgres
       host: "{{ env_var('DB_HOST') }}"
       user: "{{ env_var('DB_USER') }}"
       password: "{{ env_var('DB_PASSWORD') }}"
       ...
     ```
   - Ensure DB host used by dbt is reachable from the container running dbt. In docker-compose the service `dbt` uses the same network and host `postgres`.

7) Timestamp and timezone handling
   - insert_records.py converts `timestamp` to a datetime `timestamp_ajust` but doesn't insert it. Consider:
     - Insert the adjusted timestamp into a TIMESTAMP column (rename or add `timestamp_utc`).
     - Store timezone-aware timestamps or store UTC consistently.

8) Transaction handling and resilience
   - Add retry logic and more robust error handling around API calls and DB interactions.
   - Use connection pooling for production workloads (psycopg2 pool).

Security & sensitive data
-------------------------
- Remove or rotate any credentials committed to source control.
- Move secrets into environment variables or Docker secrets.
- Add a `.env` to .gitignore to avoid leaking sensitive variables.
- Avoid mounting host files with credentials into containers when sharing this project.

Troubleshooting
---------------
Common issues and fixes:
- "Could not connect to Postgres" — ensure Postgres container is healthy and ports are exposed. Check docker compose logs for postgres.
- Airflow DAG not appearing — verify the DAG file is present under `./airflow/dags` and check Airflow logs for parse errors.
- DockerOperator failing to mount local folder — ensure the host path exists and Airflow worker has permissions to bind mount it.
- dbt failing with authentication errors — check dbt profiles.yml and ensure host, user, password are correct for the container network.
- Duplicate rows — check that insert logic and dbt unique_key handling are working. Consider adding unique constraints or using `ON CONFLICT` to deduplicate in Postgres.

Testing locally (developer tips)
-------------------------------
- Test API call:
  python -c "from api_request.api_request import fetch_data; print(fetch_data()[0])"

- Test DB connection and insert locally (run inside a container or on host with appropriate network):
  python -c "from api_request.insert_records import main; main()"

- Run dbt locally (or inside dbt container):
  docker compose run --rm dbt dbt run

- Trigger the Airflow DAG from inside the airflow container:
  docker compose exec airflow bash
  airflow dags list
  airflow dags trigger dolar_api_orchestrator

How to present this project in your portfolio
--------------------------------------------
- Create a short README (this file) plus a one-page summary with:
  - Problem statement: streaming exchange data, why store it and transform it
  - Architecture diagram (small image or ASCII art)
  - Key technologies used: Docker, Airflow, dbt, Postgres, Metabase, Python
  - Show screenshots:
    - Airflow DAG UI with successful runs
    - Metabase dashboard showing the time series
    - dbt run logs or model lineage graph
  - Include a short demo video (1–2 minutes) showing:
    - Start services
    - Triggering or waiting for DAG runs
    - New data appears in Metabase
- Call out what you implemented and what you would improve (this shows maturity)

Next steps & enhancements
-------------------------
- Add automated tests (unit tests for API parsing and dbt tests)
- Add CI to run linters, dbt tests, and container image checks
- Add data quality checks and monitoring (e.g., Great Expectations, dbt tests)
- Replace periodic polling with an event-driven ingestion (if applicable)
- Use Docker Secrets / HashiCorp Vault for credentials
- Add a more mature staging/production separation and migrations for schema

Example modifications to make this repo production-ready (summary)
-----------------------------------------------------------------
- Remove hard-coded credentials; use env vars and Docker secrets.
- Fix insert_records import behavior (use if __name__ == '__main__').
- Make Airflow DockerOperator paths and network agnostic.
- Make the Dockerfile valid and ensure Airflow image installs dependencies correctly.
- Add dbt tests (schema & data tests) and assertions.
- Add README screenshots and demo video.

Appendix: Useful commands
-------------------------
- Start all services:
  docker compose up -d
- Stop and remove:
  docker compose down
- View logs:
  docker compose logs -f airflow
- Run dbt inside container:
  docker compose run --rm dbt dbt run
- Enter Airflow container shell:
  docker compose exec airflow bash

Acknowledgements & credits
-------------------------
- API: economia.awesomeapi.com.br
- dbt: dbt Labs
- Airflow: Apache Software Foundation
- Metabase: Metabase, Inc.

License
-------
Pick a license appropriate for your portfolio. MIT is a permissive common choice.

---

If you want, I can:
- Produce a small architecture diagram (ASCII or mermaid) to include in this README.
- Create a cleaned-up airflow Dockerfile and example `.env` with instructions to switch to environment variables.
- Produce a short, scripted demo (set of shell commands) that automates starting stack + waiting and taking screenshots.

Tell me which of the above you'd like next and I'll generate the files and commands.