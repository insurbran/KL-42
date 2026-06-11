from pathlib import Path
from email import message_from_string

def ingest_all_mhtml(input_dir, output_dir):
    input_dir = Path("data/0_source")
    output_dir = Path("data/1_bronze")
    output_dir.mkdir(exist_ok=True)
    mhtml_files = list(input_dir.glob("*.mhtml"))

    print("🥉 Bronze layer starting...")

    total = len(mhtml_files)
    extracted = 0
    failed = 0

    for file in mhtml_files:
        html = ""
        new_path = output_dir / f"{file.stem}.html"
        message = message_from_string(file.read_text(encoding="utf-8", errors="ignore"))

        if message.is_multipart():
            for part in message.walk():
                content_type = part.get_content_type()

                if content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    html = payload.decode("utf-8", errors="ignore")
                    print(f"\n✅ Extracted: {file.name}")
                    break

        else:
            print(f"\n⚠️  No HTML content found in: {file.name}")
            failed += 1

        if html:
            new_path.write_text(html, encoding="utf-8")
            extracted += 1

    print("\n📊 Bronze Summary:")
    print(f"Total: {total} | Extracted: {extracted} | Failed: {failed}")