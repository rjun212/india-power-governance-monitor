import feedparser
import json
import os
from datetime import datetime

CENTRAL_FILE = "data/central.json"
STATE_FILE = "data/state.json"
GLOBAL_FILE = "data/global.json"
REPORT_FILE = "data/reports.json"

RSS_FEEDS = {
    "ET Power": "https://energy.economictimes.indiatimes.com/rss/power",
    "ET Renewable": "https://energy.economictimes.indiatimes.com/rss/Renewable",
    "Mercom India": "https://www.mercomindia.com/feed",
    "PowerLine": "https://powerline.net.in/feed/",
    "PIB Power Ministry": "https://www.pib.gov.in/newsite/pmreleases.aspx?mincode=28&reg=3&lang=2",
    "Business Standard Power": "https://www.business-standard.com/rss/topic/power-sector",
    "Reuters Energy": "https://www.reuters.com/business/energy/rss"
}

# ----------------------------
# Core Filters
# ----------------------------

POWER_KEYWORDS = [
    "power", "electricity", "discom",
    "grid", "transmission", "renewable",
    "thermal", "hydro", "solar",
    "wind", "battery", "storage",
    "energy"
]

GOVERNANCE_KEYWORDS = [
    "tariff", "regulation", "consultation",
    "amendment", "order", "draft",
    "policy", "reform", "approval",
    "rules"
]

REPORT_KEYWORDS = [
    "report", "study", "analysis",
    "outlook", "white paper",
    "roadmap", "assessment"
]

EXCLUDE_KEYWORDS = [
    "profit", "earnings", "shares",
    "stock", "ipo", "quarter",
    "revenue", "ugc", "election",
    "caste", "rbi"
]

CENTRAL_SIGNALS = [
    "cerc", "ministry of power", "mop",
    "mnre", "cea", "grid india",
    "nldc", "centre", "central government",
    "union government", "national electricity",
    "electricity market"
]

STATE_KEYWORDS = [
    "maharashtra", "gujarat", "tamil nadu",
    "karnataka", "rajasthan", "uttar pradesh",
    "bihar", "delhi", "punjab", "haryana",
    "odisha", "madhya pradesh",
    "andhra pradesh", "telangana",
    "merc", "gerc", "tnerc", "kerc",
    "uperc", "rerc", "derc", "oerc",
    "bescom", "tangedco", "msedcl",
    "uppcl", "tpddl", "brpl"
]

GLOBAL_KEYWORDS = [
    "renewable", "solar", "wind",
    "battery", "storage", "hydrogen",
    "energy transition"
]

NON_INDIA_MARKERS = [
    "us", "usa", "united states",
    "europe", "eu", "germany",
    "france", "uk", "britain",
    "china", "japan", "korea",
    "australia", "canada",
    "africa", "argentina",
    "brazil", "mexico",
    "middle east"
]

INDIA_MARKERS = [
    "india", "indian", "new delhi",
    "₹", " rs ", " crore",
    "mnre", "mop", "cerc", "cea",
    "seci", "ntpc", "nhpc",
] + STATE_KEYWORDS


# ----------------------------
# Helper Functions
# ----------------------------

def is_relevant(title):
    t = title.lower()

    if any(ex in t for ex in EXCLUDE_KEYWORDS):
        return False

    if not any(p in t for p in POWER_KEYWORDS):
        return False

    return True


def classify_level(title):
    t = title.lower()

    # Central
    if any(sig in t for sig in CENTRAL_SIGNALS):
        return "Central"

    # State requires both state + governance trigger
    if any(state in t for state in STATE_KEYWORDS) and \
       any(g in t for g in GOVERNANCE_KEYWORDS):
        return "State"

    return None


def is_global(title):
    t = f" {title.lower()} "

    if not any(k in t for k in GLOBAL_KEYWORDS):
        return False

    if not any(g in t for g in NON_INDIA_MARKERS):
        return False

    if any(ind in t for ind in INDIA_MARKERS):
        return False

    return True


def is_report(title):
    t = title.lower()

    if not any(r in t for r in REPORT_KEYWORDS):
        return False

    if not any(p in t for p in POWER_KEYWORDS):
        return False

    return True


def parse_date(entry):
    if hasattr(entry, "published"):
        return entry.published
    return datetime.today().strftime("%Y-%m-%d")


def dedupe(items):
    return {item["link"]: item for item in items}.values()


# ----------------------------
# Main Engine
# ----------------------------

def main():
    central_items = []
    state_items = []
    global_items = []
    report_items = []

    for source_name, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)

        for entry in feed.entries:
            title = entry.title
            link = entry.link
            date = parse_date(entry)

            if not is_relevant(title):
                continue

            item = {
                "date": date,
                "publication": source_name,
                "title": title,
                "link": link
            }

            level = classify_level(title)
            if level == "Central":
                central_items.append(item)
            elif level == "State":
                state_items.append(item)

            if is_global(title):
                global_items.append(item)

            if is_report(title):
                report_items.append(item)

    central_items = sorted(dedupe(central_items), key=lambda x: x["date"], reverse=True)
    state_items = sorted(dedupe(state_items), key=lambda x: x["date"], reverse=True)
    global_items = sorted(dedupe(global_items), key=lambda x: x["date"], reverse=True)
    report_items = sorted(dedupe(report_items), key=lambda x: x["date"], reverse=True)

    os.makedirs("data", exist_ok=True)

    with open(CENTRAL_FILE, "w") as f:
        json.dump(list(central_items), f, indent=2)

    with open(STATE_FILE, "w") as f:
        json.dump(list(state_items), f, indent=2)

    with open(GLOBAL_FILE, "w") as f:
        json.dump(list(global_items), f, indent=2)

    with open(REPORT_FILE, "w") as f:
        json.dump(list(report_items), f, indent=2)

    print("Central / State / Global / Reports updated.")


if __name__ == "__main__":
    main()
