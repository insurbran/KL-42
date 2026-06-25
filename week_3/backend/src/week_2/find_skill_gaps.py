import json
import sqlite3
import time
from pathlib import Path
from pydantic import BaseModel
from typing import List, Dict
from prompt_model import prompt_model

# Rate limit justification:
# Gemini 2.5 Flash: 5 RPM, 20 RPD
# Only 1 LLM call is made per run (resume skill extraction)
# RETRY_DELAY = 12 seconds = 60s / 5 RPM to stay within rate limit
RETRY_LIMIT = 3
RETRY_DELAY = 12

JAILBREAK_PATTERNS = [
    "ignore previous instructions",
    "ignore all instructions",
    "disregard previous",
    "you are now",
    "act as",
    "pretend you are",
    "do not follow",
    "override instructions",
    "system prompt",
    "new instructions",
    "forget previous",
]


class SkillGapResult(BaseModel):
    gaps: List[str]
    time: int
    tokens: int
    demand: Dict[str, int]


def is_jailbreak(text: str) -> bool:
    text_lower = text.lower()
    for pattern in JAILBREAK_PATTERNS:
        if pattern in text_lower:
            return True
    return False


def parse_skills(skills_text: str) -> list:
    skills = []
    for skill in skills_text.split(","):
        skill = skill.strip().lower()
        if not skill:
            continue
        skills.append(skill)
    return skills


def extract_resume_skills(resume_text: str) -> tuple[list, int]:
    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            prompt = f"""Extract all technical skills, tools, programming languages, and frameworks from this resume.
Return ONLY a JSON array of lowercase strings. No explanations, no markdown, no extra text.
Treat CI/CD and A/B testing as single skills. Split combined skills like AWS/Azure/GCP into separate items.
Ignore soft skills, certifications, and non-technical skills.

Resume:
{resume_text[:1500]}

Example response: ["python", "sql", "docker", "aws", "ci/cd"]"""

            response = prompt_model("gemini-2.5-flash", prompt)

            if not response or response.startswith("[Error]"):
                raise ValueError(f"Bad response: {response}")

            clean = response.strip().strip("```json").strip("```").strip()
            skills = json.loads(clean)
            skills = [s.lower().strip() for s in skills if isinstance(s, str) and s.strip()]

            words = len((prompt + response).split())
            tokens = words * 4

            return skills, tokens

        except Exception as e:
            print(f"[Resume] Attempt {attempt} failed: {e}")
            if attempt < RETRY_LIMIT:
                time.sleep(RETRY_DELAY)

    return [], 0


def find_skill_gaps(input_file_path: str, db_url: str) -> SkillGapResult:
    start_time = time.time()
    total_tokens = 0

    try:
        with open(input_file_path, "r", encoding="utf-8") as f:
            resume_text = f.read()
    except Exception as e:
        print(f"[Error] Could not read resume: {e}")
        return SkillGapResult(gaps=[], time=0, tokens=0, demand={})

    if is_jailbreak(resume_text):
        print("[Security] Jailbreak attempt detected in resume. Aborting.")
        return SkillGapResult(gaps=[], time=0, tokens=0, demand={})

    try:
        resume_skills, tokens = extract_resume_skills(resume_text)
        total_tokens += tokens
        resume_skills_set = set(resume_skills)
    except Exception as e:
        print(f"[Error] Could not extract resume skills: {e}")
        return SkillGapResult(gaps=[], time=0, tokens=0, demand={})

    try:
        if not Path(db_url).exists():
            print(f"[Error] Database not found: {db_url}")
            return SkillGapResult(gaps=[], time=0, tokens=0, demand={})

        conn = sqlite3.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT tech_stack FROM jobs WHERE tech_stack IS NOT NULL AND tech_stack != ''")
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(f"[Error] Could not read database: {e}")
        return SkillGapResult(gaps=[], time=0, tokens=0, demand={})

    # use simple parsing for market skills — fast and deterministic
    skill_demand: Dict[str, int] = {}
    for row in rows:
        job_skills = parse_skills(row[0])
        for skill in job_skills:
            skill_demand[skill] = skill_demand.get(skill, 0) + 1

    market_skills = set(skill_demand.keys())
    gap_skills = market_skills - resume_skills_set
    gaps = sorted(gap_skills)

    demand = {skill: skill_demand[skill] for skill in gaps}
    elapsed = int((time.time() - start_time) * 1000)

    return SkillGapResult(gaps=gaps, time=elapsed, tokens=total_tokens, demand=demand)


if __name__ == "__main__":
    result = find_skill_gaps("data/resume_d3_eval.txt", "data/jobs_d3_eval.db")
    print(result)
    print("\n📊 Skill Demand:")
    for skill, count in sorted(result.demand.items(), key=lambda x: -x[1]):
        print(f"  {skill}: {count} job(s)")