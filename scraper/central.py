import feedparser
import json
import os
import re
from datetime import datetime

CENTRAL_FILE = "data/central.json"
STATE_FILE = "data/state.json"
GLOBAL_FILE = "data/global.json"
REPORT_FILE = "data/reports.json"

RSS_FEEDS = {
    # India power-focused sources
    "ET Power": "https://energy.economictimes.indiatimes.com/rss/power",
    "ET Renewable": "https://energy.economictimes.indiatimes.com/rss/Renewable",
    "ET Top Stories": "https://energy.economictimes.indiatimes.com/rss/topstories",
    "Mercom India": "https://www.mercomindia.com/feed",
    "PowerLine": "https://powerline.net.in/feed/",
    "PIB Power Ministry": "https://www.pib.gov.in/newsite/pmreleases.aspx?mincode=28&reg=3&lang=2",

    # Global-ish sources
    "Reuters Energy": "https://www.reuters.com/business/energy/rss",
    "FT World": "https://www.ft.com/world?format=rss",
}

# ---------- KEYWORDS ----------

POWER_KEYWORDS = [
    "power", "electricity", "discom", "distribution",
    "grid", "transmission", "renewable", "solar", "wind",
    "hydro", "thermal", "coal", "battery", "storage",
    "energy", "evacuation", "load", "demand", "procurement",
    "ppa", "tariff", "substation", "smart meter", "metering",
]

STATE_KEYWORDS = [
    # states/UTs
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh", "delhi",
    "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka", "kerala",
    "madhya pradesh", "maharashtra", "manipur", "meghalaya", "mizoram", "nagaland",
    "odisha", "punjab", "rajasthan", "sikkim", "tamil nadu", "telangana", "tripura",
    "uttar pradesh", "uttarakhand", "west bengal",
    "jammu", "kashmir", "ladakh", "puducherry",

    # common utilities/discoms/erc acronyms
    "msedcl", "tangedco", "bescom", "gescom", "hescom", "cesc",
    "uppcl", "brpl", "bypl", "tpddl",
    "dvc", "gvn",  # keep light; avoid false positives
    "erc", "sherc", "rerc", "uperc", "derc", "tnerc", "kerc", "gerc", "oerc",
]

CENTRAL_SIGNALS = [
    "cerc", "cea", "moP", "ministry of power", "mnre", "seci",
    "grid india", "posoco", "ctu", "nldc", "nlc", "cea",
    "national", "inter-state", "istS", "tariff policy",
    "electricity (amendment)", "electricity act",
]

GLOBAL_RE_KEYWORDS = [
    "renewable", "solar", "wind", "battery", "storage", "bess",
    "hydrogen", "clean energy", "energy transition", "grid",
]

REPORT_KEYWORDS = [
    "report", "study", "analysis", "outlook", "white paper", "roadmap",
    "assessment", "brief", "dataset",
]

# Hard exclusions (remove finance/politics/noise)
EXCLUDE_KEYWORDS = [
    "profit", "profits", "earnings", "revenue", "ebitda", "shares", "stock",
    "ipo", "quarter", "q1", "q2", "q3", "q4", "dividend", "market cap",
    "election", "ugc", "caste", "riot", "bangladesh", "pakistan",
]

# Strong India markers used to block "Global"
INDIA_MARKERS = [
    " india ", "indian", "new delhi", "delhi", "bharat",
    "₹", " rs ", " crore", " lakh",  # currency/format markers
    "mnre", "mop", "cerc", "cea", "seci", "ntpc", "nhpc", "powergrid",
    "pfc", "rec", "ireda", "tangedco", "msedcl", "uppcl",
    # include state names as india markers for global exclusion
] + STATE_KEYWORDS


# ---------- HELPERS ----------

def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def safe_lower(s: str) -> str:
    return norm_space(s).lower()

def parse_date(entry) -> str:
    # Prefer published_parsed if present
    if getattr(entry, "published_parsed", None):
        dt = datetime(*entry.published_parsed[:6])
        return dt.strftime("%Y-%m-%d")
    if getattr(entry, "updated_parsed", None):
        dt = datetime(*entry.updated_parsed[:6])
        return dt.strftime("%Y-%m-%d")

    # Fallback: try common date strings
    raw = getattr(entry, "published", "") or getattr(entry, "updated", "")
    raw = norm_space(raw)
    if raw:
        # keep first 10 chars if it starts like YYYY-MM-DD
        if re.match(r"^\d{4}-\d{2}-\d{2}", raw):
            return raw[:10]
    return datetime.today().strftime("%Y-%m-%d")

def is_power_relevant(title: str) -> bool:
    t = safe_lower(title)
    if any(x in t for x in EXCLUDE_KEYWORDS):
        return False
    return any(k in t for k in POWER_KEYWORDS)

def is_central(title: str) -> bool:
    t = safe_lower(title)
    # Must be power relevant + central signal
    return is_power_relevant(title) and any(sig.lower() in t for sig in CENTRAL_SIGNALS)

def is_state(title: str) -> bool:
    t = safe_lower(title)
    # Must be power relevant + mention state OR discom/erc signals
    return is_power_relevant(title) and any(sk in t for sk in STATE_KEYWORDS)

def is_global(title: str) -> bool:
    t = f" {safe_lower(title)} "
    # Must contain renewable/storage-ish terms
    if not any(gk in t for gk in GLOBAL_RE_KEYWORDS):
        return False
    # Hard exclude anything that looks India-specific
    if any(im in t for im in INDIA_MARKERS):
        return False
    return True

def is_report(title: str) -> bool:
    t = safe_lower(title)
    if any(x in t for x in EXCLUDE_KEYWORDS):
        return False
    return any(rk in t for rk in REPORT_KEYWORDS) and any(pk in t for pk in POWER_KEYWORDS)

def dedupe(items):
    # Keep latest occurrence per link
    out = {}
    for it in items:
        if it.get("link"):
            out[it["link"]] = it
    return list(out.values())

def write_json(path, items):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


# ---------- MAIN ----------

def main():
    central_items = []
    state_items = []
    global_items = []
    report_items = []

    for pub, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)

        if getattr(feed, "bozo", False):
            # still proceed; feedparser often recovers
            pass

        for entry in getattr(feed, "entries", []):
            title = norm_space(getattr(entry, "title", ""))
            link = norm_space(getattr(entry, "link", ""))

            if not title or not link:
                continue

            date = parse_date(entry)

            item = {
                "date": date,
                "publication": pub,
                "title": title,
                "link": link
            }

            # CENTRAL / STATE
            if is_central(title):
                central_items.append(item)

            if is_state(title):
                state_items.append(item)

            # GLOBAL + REPORTS
            if is_global(title):
                global_items.append(item)

            if is_report(title):
                report_items.append(item)

    # Dedupe + sort newest first
    central_items = sorted(dedupe(central_items), key=lambda x: x["date"], reverse=True)
    state_items = sorted(dedupe(state_items), key=lambda x: x["date"], reverse=True)
    global_items = sorted(dedupe(global_items), key=lambda x: x["date"], reverse=True)
    report_items = sorted(dedupe(report_items), key=lambda x: x["date"], reverse=True)

    write_json(CENTRAL_FILE, central_items)
    write_json(STATE_FILE, state_items)
    write_json(GLOBAL_FILE, global_items)
    write_json(REPORT_FILE, report_items)

    print("Central / State / Global / Reports updated.")


if __name__ == "__main__":
    main()
