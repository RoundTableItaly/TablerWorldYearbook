from . import settings
import logging
import os
import sys
from pathlib import Path, PurePath
import shutil
import requests
import pandas as pd
import threading
import queue
import traceback

logger = logging.getLogger("TablerWordYearbook")


# determine if application is a script file or frozen exe
if getattr(sys, "frozen", False):
    APPLICATION_PATH = Path(sys.executable).parent
else:
    APPLICATION_PATH = Path(__file__).parent.parent

PROFILE_PICS_FOLDER = APPLICATION_PATH / "output" / "profile_pics"
PROFILE_PICS_ZIP = APPLICATION_PATH / "output" / "profile_pics.zip"

LINE_UP = "\033[1A"
LINE_CLEAR = "\x1b[2K"


def contacts():
    # Read settings
    config = settings.read()

    API_BASE_URL = config.get("api").get("base_url")
    API_KEY = config.get("api").get("key")
    API_AUTH_HEADER = {
        "Authorization": "Token {}".format(API_KEY),  # Add Peepl token
    }

    logger.info("Contacts download STARTED")

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
        logger.info(f"request {index} - records {records} - status {page.status_code}")

    logger.info("Contacts download ENDED")
    return results


def profile_pictures(df):
    logger.info("Profile pictures download STARTED\n")
    # Prepare folder
    shutil.rmtree(PROFILE_PICS_FOLDER, ignore_errors=True)
    os.makedirs(PROFILE_PICS_FOLDER, exist_ok=True)

    # Remove old zip file
    PROFILE_PICS_ZIP.unlink(missing_ok=True)

    # Prepare dataframe
    df_pictures = df.dropna(subset=["profile_pic"])

    q = queue.Queue()

    def worker():
        while True:
            try:
                item = q.get()
                pic_id = item["profile_pic_file"]

                # print(LINE_UP, end=LINE_CLEAR)
                logger.info(f"Download profile_pic {pic_id}")

                r = requests.get(item["profile_pic"])
                with open(PurePath.joinpath(PROFILE_PICS_FOLDER, pic_id), "wb") as f:
                    f.write(r.content)

            except Exception:
                logger.info(traceback.format_exc())
                while not q.empty():
                    try:
                        q.get(block=False)
                    except Empty:
                        continue
                    q.task_done()

            q.task_done()

    # Turn-on the worker threads
    for i in range(10):
        threading.Thread(target=worker, daemon=True).start()

    # Send thirty task requests to the worker.
    for index, item in df_pictures.iterrows():
        q.put(item)

    # Block until all tasks are done.
    q.join()

    # Zip folder
    shutil.make_archive(os.path.splitext(PROFILE_PICS_ZIP)[0], "zip", PROFILE_PICS_FOLDER)

    # print(LINE_UP, end=LINE_CLEAR)
    logger.info("Profile pictures download ENDED")

    return
