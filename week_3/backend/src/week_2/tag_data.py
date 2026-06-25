import sqlite3
import time
from pathlib import Path
from prompt_model import prompt_model

# Rate limit justification:
# Gemini 2.5 Flash: 5 RPM, 20 RPD
# BATCH_SIZE = 5 means we process 5 jobs before committing
# RETRY_DELAY = 12 seconds = 60s / 5 RPM to stay within rate limit
# For local Ollama: no rate limit, but RETRY_DELAY kept for stability
BATCH_SIZE = 5
RETRY_LIMIT = 3
RETRY_DELAY = 12


def tag_data(db_url: str):
    if not Path(db_url).exists():
        print(f"[Error] Database not found: {db_url}")
        return

    conn = sqlite3.connect(db_url)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT source_id, description FROM jobs
        WHERE tech_stack IS NULL OR tech_stack = ''
    """)
    rows = cursor.fetchall()

    if not rows:
        print("No data to tag")
        conn.close()
        return

    total_tokens = 0
    start_time = time.time()

    for batch_start in range(0, len(rows), BATCH_SIZE):
        batch = rows[batch_start:batch_start + BATCH_SIZE]
        batch_num = batch_start // BATCH_SIZE

        batch_success = []

        for source_id, description in batch:
            success = False

            for attempt in range(1, RETRY_LIMIT + 1):
                try:
                    prompt = f"""Extract only technical skills, tools, frameworks, and technologies from this job description.
Return ONLY a comma separated list. No explanations, no numbering, no extra text.

Job Description:
{description[:800]}

Response format example: Python, SQL, Docker, AWS"""

                    response = prompt_model("gemini-2.5-flash", prompt)

                    if not response or response.startswith("[Error]"):
                        raise ValueError(f"Bad response: {response}")

                    tech_stack = response.strip().split("\n")[0].strip()
                    batch_success.append((tech_stack, source_id))
                    words = len((prompt + response).split())
                    total_tokens += words * 4
                    print(f"Analyzed Job {source_id}: {tech_stack}")
                    success = True
                    break

                except Exception as e:
                    print(f"[Job {source_id}] Attempt {attempt} failed: {e}")
                    if attempt < RETRY_LIMIT:
                        time.sleep(RETRY_DELAY)

            if not success:
                print(f"[Job {source_id}] All attempts failed, skipping.")

        # batch commit
        for tech_stack, source_id in batch_success:
            cursor.execute("""
                UPDATE jobs SET tech_stack = ? WHERE source_id = ?
            """, (tech_stack, source_id))
        conn.commit()
        print(f"[Batch {batch_num}] Committed {len(batch_success)} jobs.")

    elapsed = (time.time() - start_time) * 1000
    print(f"\nTotal tokens used: {total_tokens}, took {elapsed:.3f}ms")
    conn.close()


if __name__ == "__main__":
    tag_data("data/jobs_d1.db")