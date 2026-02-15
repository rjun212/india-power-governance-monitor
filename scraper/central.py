import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

CENTRAL_FILE = "data/central.json"
MEDIA_FILE = "data/media.json"


# --------------------------
# Utility Functions
# --------------------------

def load_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def deduplicate(existing, new):
    existing_links = {item["link"] for item in existing}
    for item in new:
        if item["link"] not in existing_links:
            existing.append(item)
    return existing


# --------------------------
# MoP Scraper (Homepage Notices)
# --------------------------

def scrape_mop():
    URL = "https://powermin.gov.in"
    items = []

    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        announcement_block = soup.find("div", class_="view-announcement")

        if not announcement_block:
            return []

        notices = announcement_block.find_all("div", class_="views-row")

        for notice in notices:
            date_container = notice.find("div")
            title_link = notice.find("a", href=True)

            if not date_container or not title_link:
                continue

            date_text = date_container.get_text(strip=True)
            title = title_link.get_text(strip=True)
            link = title_link["href"]

            if not link.startswith("http"):
                link = "https://powermin.gov.in" + link

            items.append({
                "date": date_text,
                "authority": "MoP",
                "category": "Scheme Notification",
                "doc_type": "Final",
                "title": title,
                "link": link
            })

        return items

    except Exception as e:
        print("MoP error:", e)
        return []


# --------------------------
# MNRE Scraper (Homepage)
# --------------------------

def scrape_mnre():
    URL = "https://mnre.gov.in"
    items = []

    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        links = soup.find_all("a")

        for link in links:
            title = link.get_text(strip=True)
            href = link.get("href")

            if not title or not href:
                continue

            keywords = ["Guideline", "Notification", "Amendment"]

            if any(k.lower() in title.lower() for k in keywords):
                if not href.startswith("http"):
                    href = "https://mnre.gov.in" + href

                items.append({
                    "date": datetime.today().strftime("%Y-%m-%d"),
                    "authority": "MNRE",
                    "category": "Scheme Notification",
                    "doc_type": "Final",
                    "title": title,
                    "link": href
                })

        return items[:10]

    except Exception as e:
        print("MNRE error:", e)
        return []


# --------------------------
# Media Scraper (ET EnergyWorld)
# --------------------------

def scrape_media():
    URL = "https://energy.economictimes.indiatimes.com/"
    items = []

    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        articles = soup.find_all("a")

        keywords = [
            "CERC",
            "SERC",
            "Regulation",
            "Tariff",
            "Discom",
            "MoP",
            "MNRE",
            "Consultation"
        ]

        for article in articles:
            title = article.get_text(strip=True)
            href = article.get("href")

            if not title or not href:
                continue

            if any(keyword.lower() in title.lower() for keyword in keywords):

                if not href.startswith("http"):
                    href = "https://energy.economictimes.indiatimes.com" + href

                items.append({
                    "date": datetime.today().strftime("%Y-%m-%d"),
                    "publication": "ET EnergyWorld",
                    "title": title,
                    "link": href
                })

        return items[:15]

    except Exception as e:
        print("Media error:", e)
        return []


# --------------------------
# Main Execution
# --------------------------

def main():

    # CENTRAL INGESTION
    new_central = []
    new_central += scrape_mop()
    new_central += scrape_mnre()

    existing_central = load_json(CENTRAL_FILE)
    combined_central = deduplicate(existing_central, new_central)

    combined_central.sort(key=lambda x: x["date"], reverse=True)
    save_json(CENTRAL_FILE, combined_central)

    # MEDIA INGESTION
    media_items = scrape_media()
    save_json(MEDIA_FILE, media_items)

    print("Central and Media update complete.")


if __name__ == "__main__":
    main()
