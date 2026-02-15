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
    "PIB Power Ministry": "https://www.pib.gov.in/newsite/pmreleases.aspx?mincode=28&reg=3&lang=2",
    "Indian Express Opinion": "https://indianexpress.com/section/opinion/feed/"
}

POWER_KEYWORDS = [
    "power", "electricity", "discom", "grid",
    "transmission", "renewable", "thermal",
    "hydro", "solar", "wind", "energy"
]

GOVERNANCE_KEYWORDS = [
    "tariff", "regulation", "consultation",
    "amendment", "order", "draft",
    "policy", "reform", "approval",
    "erc", "cerc", "serc", "mnre", "mop", "cea"
]

EXCLUDE_KEYWORDS = [
    "profit", "earnings", "shares",
    "stock", "ipo", "quarter"
]

CENTRAL_AUTHORITIES = [
    "CERC", "Central Electricity Regulatory Commission",
    "MoP", "Ministry of Power",
    "MNRE", "CEA", "SECI",
    "Grid India", "NLDC"
]

STATES = [
    "Maharashtra", "Gujarat", "Tamil Nadu", "Karnataka",
    "Rajasthan", "Uttar Pradesh", "Bihar", "Delhi",
    "Punjab", "Haryana", "Odisha", "Madhya Pradesh",
    "Andhra Pradesh", "Telangana"
]


def is_relevant(title):
    t = title.lower()

    if any(ex in t for ex in EXCLUDE_KEYWORDS):
        return False

    if not any(p in t for p in POWER_KEYWORDS):
        return False

    if not any(g in t for g in GOVERNANCE_KEYWORDS):
        return False

    return True


def classify_level(title):
    for authority in CENTRAL_AUTHORITIES:
        if authority.lower() in title.lower():
            return "Central"

    for state in STATES:
        if state.lower() in title.lower():
            return "State"

    if "serc" in title.lower() or "erc" in title.lower():
        return "State"

    return None


def scrape_rss(source_name, url):
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
                "level": level,
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
        articles = scrape_rss(source_name, url)

        for article in articles:
            if article["level"] == "Central":
                central_items.append(article)
            elif article["level"] == "State":
                state_items.append(article)

    # Deduplicate by link
    central_unique = {item["link"]: item for item in central_items}
    state_unique = {item["link"]: item for item in state_items}

    with open(CENTRAL_FILE, "w") as f:
        json.dump(list(central_unique.values()), f, indent=2)

    with open(STATE_FILE, "w") as f:
        json.dump(list(state_unique.values()), f, indent=2)

    print("Central and State feeds updated.")


if __name__ == "__main__":
    main()
