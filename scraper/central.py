import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime

MEDIA_FILE = "data/media.json"

RSS_FEEDS = {
    "ET Power": "https://energy.economictimes.indiatimes.com/rss/power",
    "ET Top Stories": "https://energy.economictimes.indiatimes.com/rss/topstories",
    "ET Recent": "https://energy.economictimes.indiatimes.com/rss/recentstories",
    "Mercom India": "https://www.mercomindia.com/feed",
    "PowerLine": "https://powerline.net.in/feed/",
    "PIB Power Ministry": "https://www.pib.gov.in/newsite/pmreleases.aspx?mincode=28&reg=3&lang=2",
    "Indian Express Opinion": "https://indianexpress.com/section/opinion/feed/"
}

INCLUDE_KEYWORDS = [
    "CERC", "SERC", "MoP", "MNRE", "CEA",
    "Tariff", "Regulation", "Consultation",
    "Electricity", "Power sector",
    "DSM", "Transmission", "Discom",
    "Policy", "Amendment", "Draft",
    "Grid", "Load Dispatch"
]

EXCLUDE_KEYWORDS = [
    "profit", "earnings", "shares",
    "stock", "Q1", "Q2", "Q3", "Q4",
    "IPO", "revenue", "market cap"
]


def relevant(title):
    title_lower = title.lower()

    if any(ex.lower() in title_lower for ex in EXCLUDE_KEYWORDS):
        return False

    if any(inc.lower() in title_lower for inc in INCLUDE_KEYWORDS):
        return True

    return False


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

            if relevant(title):
                items.append({
                    "date": date,
                    "publication": source_name,
                    "title": title,
                    "authority_referenced": "",
                    "topic": "Regulatory",
                    "state": "",
                    "link": link
                })

        return items

    except Exception as e:
        print(f"Error in {source_name}:", e)
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

    print("Refined regulatory media feed updated.")


if __name__ == "__main__":
    main()
