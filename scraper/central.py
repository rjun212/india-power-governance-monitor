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

POWER_KEYWORDS = [
    "power", "electricity", "discom", "grid",
    "transmission", "renewable", "solar",
    "wind", "hydro", "thermal", "battery",
    "storage", "energy"
]

STATE_KEYWORDS = [
    "maharashtra", "gujarat", "tamil nadu",
    "karnataka", "rajasthan", "uttar pradesh",
    "bihar", "delhi", "punjab", "haryana",
    "odisha", "madhya pradesh",
    "merc", "gerc", "tnerc", "kerc",
    "uperc", "rerc", "derc"
]

CENTRAL_KEYWORDS = [
    "cerc", "ministry of power", "mop",
    "mnre", "cea", "grid india",
    "centre", "central government",
    "national electricity"
]

GLOBAL_KEYWORDS = [
    "renewable", "solar", "wind",
    "battery", "storage", "hydrogen"
]

NON_INDIA_MARKERS = [
    "us", "usa", "united states",
    "europe", "germany", "france",
    "china", "japan", "africa",
    "australia", "canada"
]

EXCLUDE_KEYWORDS = [
    "profit", "earnings", "shares",
    "stock", "ipo", "quarter",
    "revenue"
]


def is_power_related(title):
    t = title.lower()
    if any(ex in t for ex in EXCLUDE_KEYWORDS):
        return False
    return any(p in t for p in POWER_KEYWORDS)


def classify(title):
    t = title.lower()

    if any(c in t for c in CENTRAL_KEYWORDS):
        return "Central"

    if any(s in t for s in STATE_KEYWORDS):
        return "State"

    return None


def is_global(title):
    t = title.lower()

    if not any(g in t for g in GLOBAL_KEYWORDS):
        return False

    if not any(n in t for n in NON_INDIA_MARKERS):
        return False

    if "india" in t:
        return False

    return True


def is_report(title):
    t = title.lower()
    return "report" in t or "outlook" in t


def parse_date(entry):
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        dt = datetime(*entry.published_parsed[:6])
        return dt.strftime("%Y-%m-%d")
    return datetime.today().strftime("%Y-%m-%d")


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

            if not is_power_related(title):
                continue

            item = {
                "title": title,
                "date": date,
                "link": link
            }

            level = classify(title)

            if level == "Central":
                central_items.append(item)
            elif level == "State":
                state_items.append(item)

            if is_global(title):
                global_items.append(item)

            if is_report(title):
                report_items.append(item)

    # Deduplicate + Sort
    central_items = sorted({i["link"]: i for i in central_items}.values(),
                           key=lambda x: x["date"], reverse=True)

    state_items = sorted({i["link"]: i for i in state_items}.values(),
                         key=lambda x: x["date"], reverse=True)

    global_items = sorted({i["link"]: i for i in global_items}.values(),
                          key=lambda x: x["date"], reverse=True)

    report_items = sorted({i["link"]: i for i in report_items}.values(),
                          key=lambda x: x["date"], reverse=True)

    os.makedirs("data", exist_ok=True)

    with open(CENTRAL_FILE, "w") as f:
        json.dump(list(central_items), f, indent=2)

    with open(STATE_FILE, "w") as f:
        json.dump(list(state_items), f, indent=2)

    with open(GLOBAL_FILE, "w") as f:
        json.dump(list(global_items), f, indent=2)

    with open(REPORT_FILE, "w") as f:
        json.dump(list(report_items), f, indent=2)

    print("Feeds updated successfully.")


if __name__ == "__main__":
    main()
