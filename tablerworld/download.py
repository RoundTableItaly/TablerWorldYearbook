import os
import requests
import logging
from dotenv import load_dotenv


def contacts():
    load_dotenv()
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    API_BASE_URL = os.getenv("API_BASE_URL")
    API_KEY = os.getenv("API_KEY")
    API_AUTH_HEADER = {
        "Authorization": "Token {}".format(API_KEY),  # Add Peepl token
    }

    def contacts_step():
        session = requests.Session()

        url = f"{API_BASE_URL}/contacts/"
        querystring = {"limit": 50}

        first_page = session.get(url, params=querystring, headers=API_AUTH_HEADER)
        yield first_page

        next_page = first_page
        while get_next_page(next_page) is not None:
            try:
                next_page_url = next_page.json()["next"]
                next_page = session.get(next_page_url, params=querystring, headers=API_AUTH_HEADER)
                yield next_page

            except KeyError:
                logging.info("No more pages")
                break

    def get_next_page(page):
        return page if page.json()["next"] is not None else None

    # Iterate through pages
    results = []
    for index, page in enumerate(contacts_step()):
        results.extend(page.json()["results"])
        records = len(page.json()["results"])
        print(f"request {index} - records {records} - status {page.status_code}")

    return results
