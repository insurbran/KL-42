import sqlite3
from pathlib import Path

def run_data_profile(db_path):
    db_path = Path("data/3_gold/jobs.db")

    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM jobs")
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            SUM(CASE WHEN job_title IS NULL OR job_title = '' THEN 1 ELSE 0 END),
            SUM(CASE WHEN company IS NULL OR company = '' THEN 1 ELSE 0 END),
            SUM(CASE WHEN description IS NULL OR description = '' THEN 1 ELSE 0 END)
        FROM jobs
    """)
    nulls = cursor.fetchone()

    cursor.execute("SELECT AVG(LENGTH(description)) FROM jobs")
    avg_len = int(cursor.fetchone()[0])

    cursor.execute("""
        SELECT LENGTH(description), source_id, job_title
        FROM jobs
        ORDER BY LENGTH(description) ASC
        LIMIT 1
    """)
    shortest = cursor.fetchone()

    cursor.execute("""
        SELECT LENGTH(description), source_id, job_title
        FROM jobs
        ORDER BY LENGTH(description) DESC
        LIMIT 1
    """)
    longest = cursor.fetchone()

    conn.close()

    print("\n--- 🔍 DATA QUALITY REPORT ---")
    print(f"\n📈 Total Records: {total}")
    print(f"\n❓ Missing Values -> job_title: {nulls[0]}, company: {nulls[1]}, description: {nulls[2]}")
    print(f"\n📝 Avg Description Length: {avg_len} chars")
    print(f"\n⚠️  Shortest Description: {shortest[0]} chars")
    print(f"   ↳ source_id: {shortest[1]} | job_title: {shortest[2]}")
    print(f"\n🚨 Longest Description: {longest[0]} chars")
    print(f"   ↳ source_id: {longest[1]} | job_title: {longest[2]}")
