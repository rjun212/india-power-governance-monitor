import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime

MEDIA_FILE = "data/media.json"

RSS_FEEDS = {
    "The Hindu - News": "https://www.thehindu.com/news/feeder/default.rss",
    "The Hindu - Business": "https://www.thehindu.com/business/feeder/default.rss",
    "ET EnergyWorld": "https://energy.economictimes.indiatimes.com/rss",
    "Moneycontrol": "https://www.moneycontrol.com/rss/latestnews.xml",
    "5paisa": "https://www.5paisa.com/rss/blog.xml",
    "Financial Times": "https://www.ft.com/world?format=rss",
    "Google Alerts 1": "https://www.google.co.in/alerts/feeds/08796847820147744949/6654652138658512807",
    "Google Alerts 2": "https://www.google.co.in/alerts/feeds/08796847820147744949/11350576126718779464",
    "Bloomberg Quint": "https://prod-qt-images.s3.amazonaws.com/production/bloombergquint/feed.xml",
    "Times of India": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"
}

KEYWORDS = [
    "CERC", "SERC", "MoP", "MNRE", "CEA", "SECI",
    "Tariff", "Regulation", "Consultation", "DSM",
    "Discom", "Electricity", "Power", "Transmission",
    "Grid", "Procurement", "Amendment", "Policy"
]

STATES = [
    "Maharashtra", "Gujarat", "Tamil Nadu", "Karnataka",
    "Rajasthan", "Uttar Pradesh", "Bihar", "Delhi",
    "Punjab", "Haryana", "Odisha", "Madhya Pradesh",
    "Andhra Pradesh", "Telangana"
]


def detect_state(title):
    for state in STATES:
        if state.lower() in title.lower():
            return state
    return ""


def detect_authority(title):
    for keyword in KEYWORDS:
        if keyword.lower() in title.lower():
            return keyword
    return ""


def scrape_rss(source_name, url):
    items = []

    try:
        response = requests.get(url, timeout=15)
        root = ET.fromstring(response.content)

        for item in root.findall(".//item"):
            title = item.find("title").text if item.find("title") is not None else ""
            link = item.find("link").text if item.find("link") is not None else ""

            if not title or not link:
                continue

            if any(keyword.lower() in title.lower() for keyword in KEYWORDS):
                items.append({
                    "date": datetime.today().strftime("%Y-%m-%d"),
                    "publication": source_name,
                    "title": title.strip(),
                    "authority_referenced": detect_authority(title),
                    "topic": "Regulatory",
                    "state": detect_state(title),
                    "link": link.strip()
                })

        return items

    except Exception as e:
        print(f"RSS error from {source_name}:", e)
        return []


def main():
    all_items = []

    for source_name, url in RSS_FEEDS.items():
        all_items += scrape_rss(source_name, url)

    # Deduplicate by link
    unique = {}
    for item in all_items:
        unique[item["link"]] = item

    final_items = list(unique.values())

    with open(MEDIA_FILE, "w") as f:
        json.dump(final_items, f, indent=2)

    print("RSS-based media intelligence updated.")


if __name__ == "__main__":
    main()
