import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

URL = "https://cercind.gov.in/orders.html"

headers = {
    "User-Agent": "Mozilla/5.0"
}

def scrape_cerc():
    try:
        response = requests.get(
            URL,
            headers=headers,
            timeout=15,
            verify=False
        )

        soup = BeautifulSoup(response.text, "html.parser")

        items = []

        links = soup.find_all("a")

        for link in links:
            text = link.get_text(strip=True)

            if text and any(keyword in text for keyword in ["Order", "Regulation", "Consultation"]):
                href = link.get("href")

                if href:
                    if not href.startswith("http"):
                        href = "https://cercind.gov.in/" + href

                    items.append({
                        "date": datetime.today().strftime("%Y-%m-%d"),
                        "authority": "CERC",
                        "category": "Order",
                        "doc_type": "Final",
                        "title": text,
                        "link": href
                    })

        return items

    except Exception as e:
        print("Error scraping CERC:", e)
        return []


def load_existing():
    if os.path.exists("data/central.json"):
        with open("data/central.json", "r") as f:
            return json.load(f)
    return []


def deduplicate(existing, new):
    existing_links = {item["link"] for item in existing}
    for item in new:
        if item["link"] not in existing_links:
            existing.append(item)
    return existing


def main():
    new_data = scrape_cerc()
    existing_data = load_existing()
    combined = deduplicate(existing_data, new_data)

    combined.sort(key=lambda x: x["date"], reverse=True)

    with open("data/central.json", "w") as f:
        json.dump(combined, f, indent=2)


if __name__ == "__main__":
    main()
