import feedparser
import json
from datetime import datetime

CENTRAL_FILE = "data/central.json"
STATE_FILE = "data/state.json"

RSS_FEEDS = {
    "ET Power": "https://energy.economictimes.indiatimes.com/rss/power",
    "ET Top Stories": "https://energy.economictimes.indiatimes.com/rss/topstories",
    "Mercom India": "https://www.mercomindia.com/feed",
    "PowerLine": "https://powerline.net.in/feed/",
    "PIB Power Ministry": "https://www.pib.gov.in/newsite/pmreleases.aspx?mincode=28&reg=3&lang=2"
}

POWER_KEYWORDS = [
    "power", "electricity", "discom",
    "grid", "transmission", "renewable",
    "thermal", "hydro", "solar",
    "wind", "energy"
]

EXCLUDE_KEYWORDS = [
    "profit", "earnings", "shares",
    "stock", "ipo", "quarter", "revenue"
]

CENTRAL_SIGNALS = [
    "cerc", "ministry of power", "mop",
    "mnre", "cea", "grid india",
    "nldc", "centre", "central government",
    "union government", "national electricity"
]

STATE_KEYWORDS = [
    "maharashtra", "gujarat", "tamil nadu",
    "karnataka", "rajasthan", "uttar pradesh",
    "bihar", "delhi", "punjab", "haryana",
    "odisha", "madhya pradesh",
    "andhra pradesh", "telangana",
    "merc", "gerc", "tnerc", "kerc",
    "uperc", "rerc", "derc", "oerc", "pserc",
    "bescom", "tangedco", "msedcl",
    "uppcl", "tpddl", "brpl"
]


def is_relevant(title):
    t = title.lower()

    if any(ex in t for ex in EXCLUDE_KEYWORDS):
        return False

    if not any(p in t for p in POWER_KEYWORDS):
        return False

    return True


def classify_level(title):
    t = title.lower()

    if any(sig in t for sig in CENTRAL_SIGNALS):
        return "Central"

    if any(state in t for state in STATE_KEYWORDS):
        return "State"

    return None


def main():
    central_items = []
    state_items = []

    for source_name, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)

        for entry in feed.entries:
            title = entry.title
            link = entry.link

            if not is_relevant(title):
                continue

            level = classify_level(title)
            if level is None:
                continue

            item = {
                "date": entry.get("published", datetime.today().strftime("%Y-%m-%d")),
                "publication": source_name,
                "title": title,
                "link": link
            }

            if level == "Central":
                central_items.append(item)
            elif level == "State":
                state_items.append(item)

    # Deduplicate
    central_unique = {item["link"]: item for item in central_items}
    state_unique = {item["link"]: item for item in state_items}

    with open(CENTRAL_FILE, "w") as f:
        json.dump(list(central_unique.values()), f, indent=2)

    with open(STATE_FILE, "w") as f:
        json.dump(list(state_unique.values()), f, indent=2)

    print("Central and State feeds updated.")


if __name__ == "__main__":
    main()
