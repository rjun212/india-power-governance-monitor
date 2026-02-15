from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import json
import os
import time

def scrape_cerc_local():

    base_url = "https://cercind.gov.in/2025.html"
    items = []

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)

    driver.get(base_url)
    time.sleep(3)

    rows = driver.find_elements(By.TAG_NAME, "tr")

    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) < 2:
            continue

        date_text = cols[0].text.strip()

        links = cols[1].find_elements(By.TAG_NAME, "a")
        if not links:
            continue

        title = links[0].text.strip()
        href = links[0].get_attribute("href")

        items.append({
            "date": date_text,
            "authority": "CERC",
            "category": "Order",
            "doc_type": "Final",
            "title": title,
            "link": href
        })

    driver.quit()
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
