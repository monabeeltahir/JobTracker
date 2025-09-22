# src/tracker.py
import httpx, json, re
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup

DEFAULT_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
UTC = timezone.utc

def iso_to_dt(s):
    try:
        return datetime.fromisoformat((s or "").replace("Z", "+00:00"))
    except Exception:
        return None

def within_days(dt, days):
    if days is None:
        return True
    if not dt:
        # keep if no date (user can filter later)
        return True
    return (datetime.now(UTC) - dt) <= timedelta(days=days)

def workday_cxs_jobs(tenant, site, base_domain="wd1", limit=50, max_count=1000, timeout=20.0, verbose=False):
    base = f"https://{tenant}.{base_domain}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    headers = {"User-Agent": DEFAULT_UA, "Accept": "application/json"}
    jobs = []
    offset = 0
    with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True) as client:
        while True:
            url = f"{base}?limit={limit}&offset={offset}"
            if verbose:
                print(f"[workday] {url}")
            r = client.get(url)
            if r.status_code != 200:
                if verbose:
                    print(f"[workday] HTTP {r.status_code}")
                break
            try:
                data = r.json()
            except Exception:
                if verbose:
                    print("[workday] JSON parse error")
                break
            postings = data.get("jobPostings") or []
            if not postings:
                break
            for p in postings:
                jobs.append({
                    "title": p.get("title"),
                    "company": (p.get("company") or {}).get("name"),
                    "locations": ", ".join([loc.get("displayName", "") for loc in p.get("locations", [])]) if p.get("locations") else p.get("location", ""),
                    "url": f"https://{tenant}.{base_domain}.myworkdayjobs.com{p.get('externalPath', '')}",
                    "postedOn": p.get("postedOn") or p.get("secondaryPostedOn"),
                    "raw": p
                })
                if len(jobs) >= max_count:
                    return jobs
            offset += limit
    return jobs

def _fmt_loc(loc):
    if isinstance(loc, dict):
        addr = loc.get("address") or {}
        parts = [addr.get("addressLocality"), addr.get("addressRegion"), addr.get("addressCountry")]
        return ", ".join([p for p in parts if p])
    return None

def extract_jsonld_jobs_from_html(html, base_url, verbose=False):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for tag in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(tag.string or "")
        except Exception:
            continue
        blobs = data if isinstance(data, list) else [data]
        for item in blobs:
            if not isinstance(item, dict):
                continue
            # Handle @graph arrays
            if "@graph" in item and isinstance(item["@graph"], list):
                for g in item["@graph"]:
                    if isinstance(g, dict) and _is_jobposting(g):
                        jobs.append(_normalize_jsonld_job(g, base_url))
            elif _is_jobposting(item):
                jobs.append(_normalize_jsonld_job(item, base_url))
    if verbose:
        print(f"[jsonld] found {len(jobs)} job(s) on {base_url}")
    return jobs

def _is_jobposting(obj):
    t = obj.get("@type")
    if isinstance(t, list):
        return "JobPosting" in t
    return t == "JobPosting"

def _normalize_jsonld_job(j, base_url):
    date_posted = j.get("datePosted") or j.get("datePublished")
    loc = j.get("jobLocation")
    if isinstance(loc, list):
        loc_text = "; ".join([_fmt_loc(x) for x in loc if isinstance(x, dict) and _fmt_loc(x)])
    elif isinstance(loc, dict):
        loc_text = _fmt_loc(loc)
    else:
        loc_text = None
    url = j.get("url")
    if url and url.startswith("/"):
        # derive absolute
        from urllib.parse import urljoin
        url = urljoin(base_url, url)
    org = j.get("hiringOrganization")
    company = org.get("name") if isinstance(org, dict) else (org if isinstance(org, str) else None)
    return {
        "title": j.get("title"),
        "company": company,
        "locations": loc_text,
        "url": url,
        "postedOn": date_posted,
        "raw": j
    }

def fetch_jsonld_pages(pages, timeout=20.0, verbose=False):
    headers = {"User-Agent": DEFAULT_UA}
    jobs = []
    with httpx.Client(headers=headers, timeout=timeout, follow_redirects=True) as client:
        for url in pages:
            if verbose:
                print(f"[jsonld] GET {url}")
            try:
                r = client.get(url)
                if r.status_code != 200:
                    if verbose:
                        print(f"[jsonld] HTTP {r.status_code} {url}")
                    continue
                jobs.extend(extract_jsonld_jobs_from_html(r.text, base_url=url, verbose=verbose))
            except Exception as e:
                if verbose:
                    print(f"[jsonld] error {e} -> {url}")
    return jobs

def get_company_jobs(entry, days=7, timeout=20.0, maxjobs=1000, verbose=False):
    """
    - source == 'workday': try candidates list
    - source == 'jsonld_pages': only JSON-LD
    - source == 'hybrid': try workday candidates first, then JSON-LD pages
    """
    out = []
    src = entry.get("source")
    if src in ("workday", "hybrid"):
        for cand in entry.get("candidates", []):
            jobs = workday_cxs_jobs(cand["tenant"], cand["site"], cand.get("base_domain", "wd1"),
                                    max_count=maxjobs, timeout=timeout, verbose=verbose)
            if jobs:
                if verbose:
                    print(f"[{entry.get('name')}] Workday candidate worked: {cand}")
                for j in jobs:
                    dt = iso_to_dt(j.get("postedOn"))
                    if within_days(dt, days):
                        j["company"] = j.get("company") or entry.get("name")
                        out.append(j)
                break  # stop at first working candidate
            else:
                if verbose:
                    print(f"[{entry.get('name')}] Workday candidate returned 0 jobs: {cand}")
    if (src in ("jsonld_pages", "hybrid")) and (not out):
        jobs = fetch_jsonld_pages(entry.get("pages", []), timeout=timeout, verbose=verbose)
        for j in jobs:
            dt = iso_to_dt(j.get("postedOn"))
            if within_days(dt, days):
                j["company"] = j.get("company") or entry.get("name")
                out.append(j)
    return out
