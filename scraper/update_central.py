import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

# Example source (we will improve later)
URL = "https://cercind.gov.in/orders.html"

def scrape_cerc():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")

    items = []

    links = soup.find_all("a")

    for link in links:
        text = link.get_text(strip=True)

        if "Regulation" in text or "Order" in text or "Consultation" in text:
            items.append({
                "date": datetime.today().strftime("%Y-%m-%d"),
                "authority": "CERC",
                "category": "Order",
                "doc_type": "Final",
                "title": text,
                "link": link.get("href")
            })

    return items[:5]  # limit initial output


def main():
    data = scrape_cerc()

    with open("data/central.json", "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    main()
