# app.py
import argparse, csv, json
from datetime import datetime, timezone

from configurations.config import companies
from src.tracker import get_company_jobs, iso_to_dt

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7, help="Number of days to filter 'new' jobs")
    parser.add_argument("--out", default="jobs.csv", help="Output CSV file")
    parser.add_argument("--json", default="jobs.json", help="Output JSON file")
    args = parser.parse_args()

    all_jobs = []
    for entry in companies:
        jobs = get_company_jobs(entry, days=args.days)
        all_jobs.extend(jobs)

    all_jobs.sort(key=lambda r: iso_to_dt(r.get("postedOn") or "") or datetime(1970,1,1,tzinfo=timezone.utc), reverse=True)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["company","title","locations","postedOn","url"])
        writer.writeheader()
        for r in all_jobs:
            writer.writerow({
                "company": r.get("company", entry.get("name")),
                "title": r.get("title"),
                "locations": r.get("locations"),
                "postedOn": r.get("postedOn"),
                "url": r.get("url"),
            })

    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, indent=2)

    print(f"Saved {len(all_jobs)} jobs -> {args.out} & {args.json}")

if __name__ == "__main__":
    main()
