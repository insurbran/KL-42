import json
from pathlib import Path
from bs4 import BeautifulSoup
from pydantic import BaseModel

class JobListing(BaseModel):
    source_id: str
    job_title: str
    company: str
    description: str

def process_all_html(input_dir, output_dir):
    input_dir = Path("data/1_bronze")
    output_dir = Path("data/2_silver")
    output_dir.mkdir(parents=True, exist_ok=True)
    html_files = list(input_dir.glob("*.html"))

    print("🥈 Silver layer starting...")

    total = len(html_files)
    processed = 0
    skipped = 0

    for file in html_files:
        html_content = file.read_text(encoding="utf-8")
        soup = BeautifulSoup(html_content, "html.parser")

        source_id_tag = soup.find("meta", property="og:url")
        job_title_tag = soup.find(attrs={"data-automation": "job-detail-title"})
        company_tag = soup.find(attrs={"data-automation": "advertiser-name"})
        description_tag = (
            soup.find(attrs={"data-automation": "jobAdDetails"}) or
            soup.find(attrs={"data-automation": "job-detail-description"})
        )

        source_id = ""
        job_title = ""
        company = ""
        description = ""

        if source_id_tag:
            url = source_id_tag["content"].rstrip("/")
            source_id = url.split("/")[-1].strip()
        if job_title_tag:
            job_title = job_title_tag.get_text(separator=" ", strip=True).strip()
        if company_tag:
            company = company_tag.get_text(separator=" ", strip=True).strip()
        if description_tag:
            description = description_tag.get_text(separator=" ", strip=True).strip()

        if not source_id:
            print(f"\n⚠️  Missing source_id in: {file.name}")
            skipped += 1
            continue
        if not job_title:
            print(f"\n⚠️  Missing job_title in: {file.name}")
            skipped += 1
            continue
        if not company:
            print(f"\n⚠️  Missing company in: {file.name}")
            skipped += 1
            continue
        if not description:
            print(f"\n⚠️  Missing description in: {file.name}")
            skipped += 1
            continue

        job_listing = JobListing(
            source_id=source_id,
            job_title=job_title,
            company=company,
            description=description,
        )

        json_path = output_dir / f"{source_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(job_listing.model_dump(), f, ensure_ascii=False)

        print(f"\n✅ Processed: {file.name}")
        processed += 1

    print(f"\n📊 Silver Summary:")
    print(f"Total: {total} | Processed: {processed} | Skipped: {skipped}")
