import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def scrape_cerc():
    base_url = "https://cercind.gov.in/"
    main_url = base_url + "orders.html"
    items = []

    try:
        response = requests.get(main_url, headers=HEADERS, timeout=15, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the first year link on the Orders page
        year_anchor = soup.find("a", href=True)
        if not year_anchor:
            return []

        year_href = year_anchor["href"]
        if not year_href.startswith("http"):
            year_href = base_url + year_href.lstrip("/")

        # Open the year page
        year_response = requests.get(year_href, headers=HEADERS, timeout=15, verify=False)
        year_soup = BeautifulSoup(year_response.text, "html.parser")

        rows = year_soup.find_all("tr")

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

    except Exception as e:
        print("CERC error:", e)
        return []


def scrape_mop():
    URL = "https://powermin.gov.in"
    items = []

    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        notices = soup.find_all("div", class_="views-row")

        for notice in notices:
            date_div = notice.find("div", class_="views-field-field-date")
            title_link = notice.find("a", href=True)

            if not date_div or not title_link:
                continue

            # Extract date parts
            date_text = date_div.get_text(strip=True)

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
