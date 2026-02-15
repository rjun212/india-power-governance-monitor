import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def scrape_cerc():
    URL = "https://cercind.gov.in/orders.html"
    items = []

    try:
        response = requests.get(URL, headers=HEADERS, timeout=15, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")

        links = soup.find_all("a")

        for link in links:
            text = link.get_text(strip=True)
            href = link.get("href")

            if text and href and any(k in text for k in ["Order", "Regulation", "Consultation"]):

                if not href.startswith("http"):
                    href = "https://cercind.gov.in/" + href

                items.append({
                    "date": datetime.today().strftime("%Y-%m-%d"),
                    "authority": "CERC",
                    "category": "Regulation Amendment" if "Regulation" in text else "Order",
                    "doc_type": "Draft" if "Consultation" in text else "Final",
                    "title": text,
                    "link": href
                })

    except Exception as e:
        print("CERC error:", e)

    return items


def scrape_mop():
    URL = "https://powermin.gov.in/en/press-release"
    items = []

    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        links = soup.find_all("a")

        for link in links:
            text = link.get_text(strip=True)
            href = link.get("href")

            if text and href and any(k in text for k in ["Notification", "Guideline", "Amendment"]):

                if not href.startswith("http"):
                    href = "https://powermin.gov.in" + href

                items.append({
                    "date": datetime.today().strftime("%Y-%m-%d"),
                    "authority": "MoP",
                    "category": "Scheme Notification",
                    "doc_type": "Final",
                    "title": text,
                    "link": href
                })

    except Exception as e:
        print("MoP error:", e)

    return items


def scrape_mnre():
    URL = "https://mnre.gov.in/press-releases/"
    items = []

    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        links = soup.find_all("a")

        for link in links:
            text = link.get_text(strip=True)
            href = link.get("href")

            if text and href and any(k in text for k in ["Guideline", "Notification", "Amendment"]):

                if not href.startswith("http"):
                    href = "https://mnre.gov.in" + href

                items.append({
                    "date": datetime.today().strftime("%Y-%m-%d"),
                    "authority": "MNRE",
                    "category": "Scheme Notification",
                    "doc_type": "Final",
                    "title": text,
                    "link": href
                })

    except Exception as e:
        print("MNRE error:", e)

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
    new_items = []
    new_items += scrape_cerc()
    new_items += scrape_mop()
    new_items += scrape_mnre()

    existing_data = load_existing()
    combined = deduplicate(existing_data, new_items)

    combined.sort(key=lambda x: x["date"], reverse=True)

    with open("data/central.json", "w") as f:
        json.dump(combined, f, indent=2)


if __name__ == "__main__":
    main()
