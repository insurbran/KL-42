import sqlite3
import time
from prompt_model import prompt_model

BATCH_SIZE = 3
RETRY_LIMIT = 3
RETRY_DELAY = 5

def tag_data(db_url: str):
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

    for source_id, description in rows:
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

                cursor.execute("""
                    UPDATE jobs SET tech_stack = ? WHERE source_id = ?
                """, (tech_stack, source_id))
                conn.commit()

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

    elapsed = (time.time() - start_time) * 1000
    print(f"\nTotal tokens used: {total_tokens}, took {elapsed:.3f}ms")
    conn.close()


if __name__ == "__main__":
    tag_data("data/jobs_d3_eval.db")
