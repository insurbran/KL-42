import sqlite3
import re
import time
from pydantic import BaseModel
from typing import List, Dict
from prompt_model import prompt_model

RETRY_LIMIT = 3
RETRY_DELAY = 12

EXCEPTIONS = ["a/b testing", "ci/cd"]

NON_TECH = {
    "agile", "scrum", "jira", "leadership", "management", "communication",
    "teamwork", "problem solving", "jenkins", "reconciliation frameworks",
    "vendor back-office systems", "normalization", "validation checks",
    "user acquisition analytics", "data parsing"
}

JAILBREAK_PATTERNS = [
    r"ignore.{0,20}(previous|above|prior).{0,20}instruction",
    r"forget.{0,20}(previous|above|prior).{0,20}instruction",
    r"you are now",
    r"act as",
    r"pretend",
    r"do not follow",
    r"override",
    r"system prompt",
    r"disregard",
    r"new instruction",
    r"ignore all",
]

class SkillGapResult(BaseModel):
    gaps: List[str]
    time: int
    tokens: int
    demand: Dict[str, int]

def is_jailbreak(text: str) -> bool:
    text_lower = text.lower()
    for pattern in JAILBREAK_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False

def parse_skills(skills_text: str) -> set:
    skills = set()
    for skill in skills_text.split(","):
        skill = skill.strip().lower()
        skill = re.sub(r'[^\w\s/+#.\-]', '', skill).strip(".")
        if not skill:
            continue
        if skill in EXCEPTIONS:
            skills.add(skill)
            continue
        for part in skill.split("/"):
            part = part.strip().strip(".")
            if part and part not in NON_TECH:
                skills.add(part)
    return skills

def extract_resume_skills(resume_text: str) -> tuple[set, int]:
    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            prompt = f"""Extract only the technical skills, tools, programming languages, and frameworks from this resume.
Return ONLY a comma separated list. No explanations, no numbering, no extra text.
Ignore certifications, soft skills, languages spoken, and non-technical skills.

Resume:
{resume_text}

Response format example: Python, SQL, Docker, AWS"""

            response = prompt_model("gemini-2.5-flash", prompt)

            if not response or response.startswith("[Error]"):
                raise ValueError(f"Bad response: {response}")

            words = len((prompt + response).split())
            tokens = words * 4
            skills = parse_skills(response)
            return skills, tokens

        except Exception as e:
            print(f"[Resume] Attempt {attempt} failed: {e}")
            if attempt < RETRY_LIMIT:
                time.sleep(RETRY_DELAY)

    return set(), 0

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
    except Exception as e:
        print(f"[Error] Could not extract resume skills: {e}")
        return SkillGapResult(gaps=[], time=0, tokens=0, demand={})

    try:
        conn = sqlite3.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT tech_stack FROM jobs WHERE tech_stack IS NOT NULL AND tech_stack != ''")
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(f"[Error] Could not read database: {e}")
        return SkillGapResult(gaps=[], time=0, tokens=0, demand={})

    # count demand per skill
    skill_demand: Dict[str, int] = {}
    for row in rows:
        for skill in parse_skills(row[0]):
            skill_demand[skill] = skill_demand.get(skill, 0) + 1

    market_skills = set(skill_demand.keys())
    gap_skills = market_skills - resume_skills
    gaps = sorted(gap_skills)

    # only show demand for gap skills
    demand = {skill: skill_demand[skill] for skill in gaps}

    elapsed = int((time.time() - start_time) * 1000)

    return SkillGapResult(gaps=gaps, time=elapsed, tokens=total_tokens, demand=demand)


if __name__ == "__main__":
    result = find_skill_gaps("data/resume_d3_eval.txt", "data/jobs_d3_eval.db")
    print(result)
    print("\n📊 Skill Demand:")
    for skill, count in sorted(result.demand.items(), key=lambda x: -x[1]):
        print(f"  {skill}: {count} job(s)")