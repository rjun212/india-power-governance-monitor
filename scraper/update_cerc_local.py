import requests
from bs4 import BeautifulSoup
import json
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def scrape_cerc_local():
    base_url = "https://cercind.gov.in/"
    year_url = base_url + "2025.html"   # change year as needed

    items = []

    response = requests.get(year_url, headers=HEADERS, timeout=15, verify=False)
    soup = BeautifulSoup(response.text, "html.parser")

    rows = soup.find_all("tr")

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue

        date_text = cols[0].get_text(strip=True)

        link = cols[1].find("a", href=True)
        if not link:
            continue

        title = link.get_text(strip=True)
        href = link["href"]

        if not href.startswith("http"):
            href = base_url + href.lstrip("/")

        items.append({
            "date": date_text,
            "authority": "CERC",
            "category": "Order",
            "doc_type": "Final",
            "title": title,
            "link": href
        })

    return items


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
    new_items = scrape_cerc_local()
    existing_data = load_existing()
    combined = deduplicate(existing_data, new_items)

    combined.sort(key=lambda x: x["date"], reverse=True)

    with open("data/central.json", "w") as f:
        json.dump(combined, f, indent=2)

    print("CERC local update complete.")


if __name__ == "__main__":
    main()
