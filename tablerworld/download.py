import os
from pathlib import Path, PurePath
import shutil
import requests
import pandas as pd
import threading
import queue
import traceback

MODULE_PATH = Path(__file__).parent
DIST_FOLDER = PurePath.joinpath(Path(MODULE_PATH).parent, "dist")
PROFILE_PICS_FOLDER = PurePath.joinpath(DIST_FOLDER, "profile_pics")
PROFILE_PICS_ZIP = PurePath.joinpath(DIST_FOLDER, "profile_pics.zip")

LINE_UP = "\033[1A"
LINE_CLEAR = "\x1b[2K"


def contacts():
    API_BASE_URL = os.getenv("API_BASE_URL")
    API_KEY = os.getenv("API_KEY")
    API_AUTH_HEADER = {
        "Authorization": "Token {}".format(API_KEY),  # Add Peepl token
    }

    print("Contacts download STARTED")

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

    print("Contacts download ENDED")
    return results


def profile_pictures(df):
    print("Profile pictures download STARTED\n")
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

                print(LINE_UP, end=LINE_CLEAR)
                print(f"Download profile_pic {pic_id}")

                r = requests.get(item["profile_pic"])
                with open(PurePath.joinpath(PROFILE_PICS_FOLDER, pic_id), "wb") as f:
                    f.write(r.content)

            except Exception:
                print(traceback.format_exc())
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

    print(LINE_UP, end=LINE_CLEAR)
    print("Profile pictures download ENDED")

    return
