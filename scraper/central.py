import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0"}

MEDIA_FILE = "data/media.json"

AUTHORITIES = [
    "CERC",
    "Central Electricity Regulatory Commission",
    "SERC",
    "Electricity Regulatory Commission",
    "MoP",
    "Ministry of Power",
    "MNRE",
    "CEA",
    "SECI",
    "Grid India",
    "NLDC",
    "SLDC",
    "DISCOM"
]

TOPICS = [
    "Tariff",
    "Regulation",
    "Consultation",
    "DSM",
    "Transmission",
    "Storage",
    "Procurement",
    "Draft",
    "Amendment",
    "Notification",
    "Policy",
    "Power"
]

STATES = [
    "Maharashtra", "Gujarat", "Tamil Nadu", "Karnataka",
    "Rajasthan", "Uttar Pradesh", "Bihar", "Delhi",
    "Punjab", "Haryana", "Odisha", "Madhya Pradesh",
    "Andhra Pradesh", "Telangana"
]


# -------------------------
# Classification Helpers
# -------------------------

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


def build_item(publication, title, href):
    return {
        "date": datetime.today().strftime("%Y-%m-%d"),
        "publication": publication,
        "title": title,
        "authority_referenced": detect_authority(title),
        "topic": detect_topic(title),
        "state": detect_state(title),
        "link": href
    }


# -------------------------
# ET EnergyWorld
# -------------------------

def scrape_et():
    URL = "https://energy.economictimes.indiatimes.com/news/power"
    items = []

    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        for a in soup.find_all("a", href=True):
            title = a.get_text(" ", strip=True)
            href = a["href"]

            if not title or len(title) < 25:
                continue

            if "/news/" not in href:
                continue

            if not href.startswith("http"):
                href = "https://energy.economictimes.indiatimes.com" + href

            if any(k.lower() in title.lower() for k in AUTHORITIES + TOPICS):
                items.append(build_item("ET EnergyWorld", title, href))

    except Exception as e:
        print("ET error:", e)

    return items


# -------------------------
# Reuters India
# -------------------------

def scrape_reuters():
    URL = "https://www.reuters.com/world/india/"
    items = []

    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        for a in soup.find_all("a", href=True):
            title = a.get_text(" ", strip=True)
            href = a["href"]

            if not title or len(title) < 25:
                continue

            if not href.startswith("http"):
                href = "https://www.reuters.com" + href

            if any(k.lower() in title.lower() for k in AUTHORITIES + TOPICS):
                items.append(build_item("Reuters", title, href))

    except Exception as e:
        print("Reuters error:", e)

    return items


# -------------------------
# Business Standard
# -------------------------

def scrape_bs():
    URL = "https://www.business-standard.com/topic/power-sector"
    items = []

    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        for a in soup.find_all("a", href=True):
            title = a.get_text(" ", strip=True)
            href = a["href"]

            if not title or len(title) < 25:
                continue

            if not href.startswith("http"):
                href = "https://www.business-standard.com" + href

            if any(k.lower() in title.lower() for k in AUTHORITIES + TOPICS):
                items.append(build_item("Business Standard", title, href))

    except Exception as e:
        print("Business Standard error:", e)

    return items


# -------------------------
# PIB (Ministry of Power)
# -------------------------

def scrape_pib():
    URL = "https://pib.gov.in/PressReleasePage.aspx?MinCode=31"
    items = []

    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        for a in soup.find_all("a", href=True):
            title = a.get_text(" ", strip=True)
            href = a["href"]

            if not title or len(title) < 25:
                continue

            if any(k.lower() in title.lower() for k in AUTHORITIES + TOPICS):

                if not href.startswith("http"):
                    href = "https://pib.gov.in/" + href

                items.append(build_item("PIB", title, href))

    except Exception as e:
        print("PIB error:", e)

    return items


# -------------------------
# Main Execution
# -------------------------

def main():
    all_items = []

    all_items += scrape_et()
    all_items += scrape_reuters()
    all_items += scrape_bs()
    all_items += scrape_pib()

    # Deduplicate by link
    unique = {}
    for item in all_items:
        unique[item["link"]] = item

    final_items = list(unique.values())

    with open(MEDIA_FILE, "w") as f:
        json.dump(final_items, f, indent=2)

    print("Media multi-source update complete.")


if __name__ == "__main__":
    main()
