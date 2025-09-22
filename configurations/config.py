# configuration/config.py
"""
You can list multiple "candidates" for Workday tenants if you're unsure.
The tracker will try them in order until one returns data (HTTP 200 with postings).
"""

companies = [
    # Confirmed Workday
    {"name": "Analog Devices (ADI)", "source": "workday", "candidates": [{"tenant": "analogdevices", "site": "External", "base_domain": "wd1"}]},
    {"name": "Intel", "source": "workday", "candidates": [{"tenant": "intel", "site": "External", "base_domain": "wd1"}]},
    {"name": "Applied Materials", "source": "workday", "candidates": [{"tenant": "amat", "site": "External", "base_domain": "wd1"}]},

    # Likely Workday (provide candidates); if none work, JSON-LD pages act as fallback
    {"name": "Qualcomm", "source": "hybrid", "candidates": [
        {"tenant": "qualcomm", "site": "external", "base_domain": "wd5"},
        {"tenant": "qualcomm", "site": "external", "base_domain": "wd1"},
    ], "pages": ["https://careers.qualcomm.com/careers"]},

    {"name": "Skyworks Solutions", "source": "hybrid", "candidates": [
        {"tenant": "skyworks", "site": "External", "base_domain": "wd1"},
    ], "pages": ["https://careers.skyworksinc.com/"]},

    {"name": "onsemi", "source": "hybrid", "candidates": [
        {"tenant": "onsemi", "site": "careers", "base_domain": "wd1"},
        {"tenant": "onsemi", "site": "External", "base_domain": "wd1"},
    ], "pages": ["https://www.onsemi.com/careers"]},

    {"name": "Lam Research", "source": "hybrid", "candidates": [
        {"tenant": "lamresearch", "site": "External", "base_domain": "wd1"},
    ], "pages": ["https://careers.lamresearch.com/"]},

    # Non-Workday or mixed
    {"name": "Texas Instruments (TI)", "source": "jsonld_pages", "pages": ["https://careers.ti.com/"]},
    {"name": "Bell Labs (Nokia)", "source": "jsonld_pages", "pages": ["https://jobs.nokia.com/"]},
    {"name": "IBM", "source": "jsonld_pages", "pages": ["https://www.ibm.com/careers/search"]},
    {"name": "ASML", "source": "jsonld_pages", "pages": ["https://www.asml.com/careers/find-your-job"]},
]
