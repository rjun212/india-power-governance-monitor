import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

URL = "https://cercind.gov.in/orders.html"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
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

        return items[:5]

    except Exception as e:
        print("Error scraping CERC:", e)
        return []


def main():
    data = scrape_cerc()

    with open("data/central.json", "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    main()
