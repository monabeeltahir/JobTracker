# src/tracker.py
import httpx, json, re
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup

DEFAULT_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
UTC = timezone.utc

def iso_to_dt(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None

def within_days(dt, days):
    if not dt:
        return True
    return (datetime.now(UTC) - dt) <= timedelta(days=days)

def workday_cxs_jobs(tenant, site, base_domain="wd1", limit=50, max_count=1000, timeout=20.0):
    base = f"https://{tenant}.{base_domain}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    headers = {"User-Agent": DEFAULT_UA, "Accept": "application/json"}
    jobs = []
    offset = 0
    with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True) as client:
        while True:
            url = f"{base}?limit={limit}&offset={offset}"
            r = client.get(url)
            if r.status_code != 200:
                break
            data = r.json()
            postings = data.get("jobPostings") or []
            if not postings:
                break
            for p in postings:
                jobs.append({
                    "title": p.get("title"),
                    "company": p.get("company", {}).get("name"),
                    "locations": ", ".join([loc.get("displayName", "") for loc in p.get("locations", [])]) if p.get("locations") else p.get("location", ""),
                    "url": f"https://{tenant}.{base_domain}.myworkdayjobs.com{p.get('externalPath', '')}",
                    "postedOn": p.get("postedOn"),
                    "raw": p
                })
                if len(jobs) >= max_count:
                    return jobs
            offset += limit
    return jobs

def extract_jsonld_jobs_from_html(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for tag in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(tag.string or "")
        except Exception:
            continue
        candidates = data if isinstance(data, list) else [data]
        for item in candidates:
            if isinstance(item, dict) and item.get("@type") == "JobPosting":
                jobs.append({
                    "title": item.get("title"),
                    "company": (item.get("hiringOrganization") or {}).get("name"),
                    "locations": item.get("jobLocation", {}),
                    "url": item.get("url"),
                    "postedOn": item.get("datePosted") or item.get("datePublished"),
                    "raw": item
                })
    return jobs

def fetch_jsonld_pages(pages, timeout=20.0):
    headers = {"User-Agent": DEFAULT_UA}
    jobs = []
    with httpx.Client(headers=headers, timeout=timeout, follow_redirects=True) as client:
        for url in pages:
            try:
                r = client.get(url)
                if r.status_code != 200:
                    continue
                jobs.extend(extract_jsonld_jobs_from_html(r.text, base_url=url))
            except Exception:
                continue
    return jobs

def get_company_jobs(entry, days=7, timeout=20.0, maxjobs=1000):
    out = []
    if entry.get("source") == "workday":
        jobs = workday_cxs_jobs(entry["tenant"], entry["site"], entry.get("base_domain", "wd1"), max_count=maxjobs, timeout=timeout)
        for j in jobs:
            dt = iso_to_dt(j.get("postedOn"))
            if within_days(dt, days):
                out.append(j)
    elif entry.get("source") == "jsonld_pages":
        jobs = fetch_jsonld_pages(entry.get("pages", []), timeout=timeout)
        for j in jobs:
            dt = iso_to_dt(j.get("postedOn"))
            if within_days(dt, days):
                out.append(j)
    return out
