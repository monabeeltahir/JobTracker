# app.py
import argparse, csv, json
from datetime import datetime, timezone
from configurations.config import companies
from src.tracker import get_company_jobs, iso_to_dt
# Addding new data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7, help="Number of days to filter 'new' jobs (set to 0 or use --no_filter to disable strict filtering)")
    parser.add_argument("--no_filter", action="store_true", help="Disable date filtering; keep all jobs")
    parser.add_argument("--out", default="jobs.csv", help="Output CSV file")
    parser.add_argument("--json", default="jobs.json", help="Output JSON file")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    filter_days = None if args.no_filter else (args.days if args.days and args.days > 0 else None)

    all_jobs = []
    for entry in companies:
        rows = get_company_jobs(entry, days=filter_days, verbose=args.verbose)
        if args.verbose:
            print(f"[{entry.get('name')}] -> {len(rows)} job(s)")
        all_jobs.extend(rows)

    all_jobs.sort(key=lambda r: iso_to_dt(r.get("postedOn") or "") or datetime(1970,1,1,tzinfo=timezone.utc), reverse=True)

    # Deduplicate by (company,title,url)
    seen = set()
    deduped = []
    for r in all_jobs:
        key = (r.get("company"), r.get("title"), r.get("url"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["company","title","locations","postedOn","url"])
        writer.writeheader()
        for r in deduped:
            writer.writerow({
                "company": r.get("company"),
                "title": r.get("title"),
                "locations": r.get("locations"),
                "postedOn": r.get("postedOn"),
                "url": r.get("url"),
            })

    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(deduped, f, indent=2)

    print(f"Saved {len(deduped)} jobs -> {args.out} & {args.json}")

if __name__ == "__main__":
    main()
