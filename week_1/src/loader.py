import json
import sqlite3
from pathlib import Path

def load_all_jsons(input_dir, output_dir):
    input_dir = Path("data/2_silver")
    output_dir = Path("data/3_gold")
    output_dir.mkdir(exist_ok=True)
    json_files = list(input_dir.glob("*.json"))

    print("🥇 Gold layer starting...")

    total = len(json_files)
    inserted = 0
    skipped = 0

    db_path = output_dir / "jobs.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            source_id TEXT PRIMARY KEY,
            job_title TEXT,
            company TEXT,
            description TEXT,
            tech_stack TEXT
        )
    """)
    conn.commit()

    for file in json_files:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        cursor.execute("""
            INSERT OR IGNORE INTO jobs (source_id, job_title, company, description)
            VALUES (?, ?, ?, ?)
        """, (data["source_id"], data["job_title"], data["company"], data["description"]))

        if cursor.rowcount == 1:
            print(f"\n ✅ Inserted: {file.name}")
            inserted += 1
        else:
            print(f"\n ⏭️ Skipped (duplicate): {file.name}")
            skipped += 1

    conn.commit()
    conn.close()

    print("\n📊 Gold Summary:")
    print(f"Total: {total} | Inserted: {inserted} | Skipped: {skipped}")
