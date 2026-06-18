# Week 1 - Job Listings Data Pipeline

## Project Description
A local ETL pipeline that scrapes, cleans, and stores job listings from Jobstreet into a SQLite database using a Medallion Architecture (Bronze → Silver → Gold).

## Setup Instructions

### Prerequisites
- Python 3.11+
- pip

### Install Dependencies
```bash
pip install beautifulsoup4 pydantic
```

## Usage

Run each stage individually or all at once:

```bash
python main.py ingest    # Extract HTML from .mhtml files → data/1_bronze
python main.py process   # Clean and structure HTML → data/2_silver
python main.py load      # Insert JSON into SQLite → data/3_gold/jobs.db
python main.py profile   # Run data quality report
python main.py all       # Run full pipeline in order
```

## Technical Reflections

### Day 1: The Extractor (Medallion & Lakehouses)
Why is it useful to keep the original raw HTML files instead of directly inserting processed data into the database? What problems become easier to debug or recover from?
- **Answer**: Keeping raw HTML means you can always reprocess from scratch if your cleaning logic changes or has bugs. If you only kept the processed output and later discovered an extraction error, you'd have no way to recover without re-scraping. The raw files act as a source of truth — like a backup — so debugging becomes as simple as re-running the pipeline with a fix.

### Day 2: Treatment Plant (ETL vs ELT & Scale)
Why do cloud systems prefer loading raw data first before cleaning it (ELT)? What problems happen when processing files sequentially, and how does distributed processing help?
- **Answer**: Cloud platforms have virtually unlimited storage and compute, so it's cheaper and faster to dump raw data in first and clean it later using scalable tools. Sequential processing like our pipeline handles one file at a time, which is slow for millions of records. Distributed systems like Spark split the data across many machines and process chunks in parallel, cutting hours of work down to minutes.

### Day 3: The Blueprint & The Vault (Storage & Contracts)
What should happen if an important field like job_title disappears? Why fail early instead of silently inserting nulls into DB? What does INSERT OR IGNORE do?
- **Answer**: If job_title disappears the record should be rejected and flagged, not inserted. Silently inserting nulls corrupts downstream analytics — dashboards and reports would show blank or misleading data with no indication anything went wrong. Failing early surfaces the problem immediately where it's easiest to fix. INSERT OR IGNORE prevents duplicate records by skipping any insert where the primary key already exists, making the pipeline safe to re-run multiple times without corrupting the database.

### Day 4: The QA Inspector & Orchestrator (Orchestration & DAGs)
What happens if processor.py crashes halfway? How are automated orchestration tools more reliable than manual retries?
- **Answer**: If processor.py crashes halfway, some files get processed and some don't, leaving the pipeline in an inconsistent state. Re-running manually means guessing where it failed. Tools like Airflow track every task's state, automatically retry failed steps, and only re-run what actually failed — not the whole pipeline. They also support scheduling, alerts, and dependency management, which a manual Python script can't do.

