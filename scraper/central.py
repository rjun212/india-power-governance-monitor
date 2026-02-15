import requests
import xml.etree.ElementTree as ET
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

# Power anchor words (must match at least one)
POWER_KEYWORDS = [
    "power", "electricity", "discom",
    "grid", "transmission", "renewable",
    "thermal", "hydro", "solar",
    "wind", "load dispatch", "energy"
]

# Governance triggers (optional but helpful)
GOVERNANCE_KEYWORDS = [
    "tariff", "regulation", "consultation",
    "amendment", "order", "draft",
    "policy", "reform", "approval"
]

# Remove corporate / financial noise
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

    # State ERC short forms
    "merc", "gerc", "tnerc", "kerc",
    "uperc", "rerc", "derc", "oerc", "pserc",

    # Major discoms
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

    # Central first
    if any(sig in t for sig in CENTRAL_SIGNALS):
        return "Central"

    # State
    if any(state in t for state in STATE_KEYWORDS):
        return "State"

    return None


def parse_rss(source_name, url):
    items = []

    try:
        response = requests.get(url, timeout=15)
        root = ET.fromstring(response.content)

        for item in root.findall(".//item"):
            title_elem = item.find("title")
            link_elem = item.find("link")
            date_elem = item.find("pubDate")

            if title_elem is None or link_elem is None:
                continue

            title = title_elem.text.strip()
            link = link_elem.text.strip()
            date = date_elem.text.strip() if date_elem is not None else datetime.today().strftime("%Y-%m-%d")

            if not is_relevant(title):
                continue

            level = classify_level(title)
            if level is None:
                continue

            items.append({
                "date": date,
                "publication": source_name,
                "title": title,
                "link": link
            })

        return items

    except Exception as e:
        print(f"Error in {source_name}:", e)
        return []


def main():
    central_items = []
    state_items = []

    for source_name, url in RSS_FEEDS.items():
        articles = parse_rss(source_name, url)

        for article in articles:
            level = classify_level(article["title"])

            if level == "Central":
                central_items.append(article)
            elif level == "State":
                state_items.append(article)

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
