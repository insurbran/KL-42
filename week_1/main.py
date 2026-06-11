import sys
from pathlib import Path

from src.ingestor import ingest_all_mhtml
from src.processor import process_all_html
from src.loader import load_all_jsons
from src.profiler import run_data_profile

if len(sys.argv) < 2:
    print("Usage: python main.py [ingest|process|load|profile|all]")
    sys.exit()

command = sys.argv[1]

if command == "ingest":
    ingest_all_mhtml(
        Path("data/0_source"),
        Path("data/1_bronze")
    )

elif command == "process":
    process_all_html(
        Path("data/1_bronze"),
        Path("data/2_silver")
    )

elif command == "load":
    load_all_jsons(
        Path("data/2_silver"),
        Path("data/3_gold")
    )

elif command == "profile":
    run_data_profile(
        Path("data/3_gold/jobs.db")
    )

elif command == "all":
    ingest_all_mhtml(Path("data/0_source"), Path("data/1_bronze"))
    process_all_html(Path("data/1_bronze"), Path("data/2_silver"))
    load_all_jsons(Path("data/2_silver"), Path("data/3_gold"))
    run_data_profile(Path("data/3_gold/jobs.db"))

else:
    print("No function available.")