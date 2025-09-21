# configuration/config.py
# List of companies & their scraping sources

companies = [
    {"name": "Analog Devices (ADI)", "source": "workday", "tenant": "analogdevices", "site": "External", "base_domain": "wd1"},
    {"name": "Intel", "source": "workday", "tenant": "intel", "site": "External", "base_domain": "wd1"},
    {"name": "Applied Materials", "source": "workday", "tenant": "amat", "site": "External", "base_domain": "wd1"},
    {"name": "Texas Instruments (TI)", "source": "jsonld_pages", "pages": ["https://careers.ti.com/"]},
    {"name": "Qualcomm", "source": "jsonld_pages", "pages": ["https://careers.qualcomm.com/careers"]},
    {"name": "Skyworks Solutions", "source": "jsonld_pages", "pages": ["https://careers.skyworksinc.com/"]},
    {"name": "onsemi", "source": "jsonld_pages", "pages": ["https://www.onsemi.com/careers"]},
    {"name": "Lam Research", "source": "jsonld_pages", "pages": ["https://careers.lamresearch.com/"]},
    {"name": "Bell Labs (Nokia)", "source": "jsonld_pages", "pages": ["https://jobs.nokia.com/"]},
    {"name": "IBM", "source": "jsonld_pages", "pages": ["https://www.ibm.com/careers/search"]},
    {"name": "ASML", "source": "jsonld_pages", "pages": ["https://www.asml.com/careers/find-your-job"]},
]
