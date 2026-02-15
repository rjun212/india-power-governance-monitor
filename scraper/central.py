import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

MEDIA_FILE = "data/media.json"

AUTHORITIES = ["CERC", "SERC", "MoP", "MNRE", "CEA", "SECI", "SLDC", "DISCOM"]
TOPICS = ["Tariff", "Regulation", "Consultation", "DSM", "Transmission", "Storage", "Procurement"]
STATES = [
    "Maharashtra", "Gujarat", "Tamil Nadu", "Karnataka", "Rajasthan",
    "Uttar Pradesh", "Bihar", "Delhi", "Punjab", "Haryana"
]


def detect_authority(title):
    for authority in AUTHORITIES:
        if authority.lower() in title.lower():
            return authority
    return ""


def detect_topic(title):
    for topic in TOPICS:
        if topic.lower() in title.lower():
            return topic
    return "General"


def detect_state(title):
    for state in STATES:
        if state.lower() in title.lower():
            return state
    return ""


def scrape_et_energyworld():
    URL = "https://energy.economictimes.indiatimes.com/"
    items = []

    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        articles = soup.find_all("a")

        for article in articles:
            title = article.get_text(strip=True)
            href = article.get("href")

            if not title or not href:
                continue

            if any(keyword.lower() in title.lower() for keyword in AUTHORITIES + TOPICS):

                if not href.startswith("http"):
                    href = "https://energy.economictimes.indiatimes.com" + href

                items.append({
                    "date": datetime.today().strftime("%Y-%m-%d"),
                    "publication": "ET EnergyWorld",
                    "title": title,
                    "authority_referenced": detect_authority(title),
                    "topic": detect_topic(title),
                    "state": detect_state(title),
                    "link": href
                })

        return items[:20]

    except Exception as e:
        print("Media error:", e)
        return []


def main():
    media_items = scrape_et_energyworld()

    with open(MEDIA_FILE, "w") as f:
        json.dump(media_items, f, indent=2)

    print("Media intelligence updated.")


if __name__ == "__main__":
    main()
