import os
import requests
import logging
from dotenv import load_dotenv
import pandas as pd
import threading
import queue
import requests
import traceback


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


def profile_pictures(df):
    df_pictures = df.dropna(subset=["profile_pic"])

    q = queue.Queue()

    def worker():
        # print(f"Started thread: {threading.current_thread().name}")
        while True:
            try:
                item = q.get()
                id = f"rt{item['rt_club_number']:02} - {item['last_name']} {item['first_name']}"
                print(f"Started  {id}")

                r = requests.get(item["profile_pic"])
                with open(f"dist/profile_pics/{id}.jpg", "wb") as f:
                    f.write(r.content)

            except Exception:
                print(traceback.format_exc())
                while not q.empty():
                    try:
                        q.get(block=False)
                    except Empty:
                        continue
                    q.task_done()

            print(f"Finished {id}")
            q.task_done()

    # Turn-on the worker threads
    for i in range(10):
        threading.Thread(target=worker, daemon=True).start()

    # Send thirty task requests to the worker.
    for index, item in df_pictures.iterrows():
        q.put(item)

    # Block until all tasks are done.
    q.join()
    print("All work completed")

    return
