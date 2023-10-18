import tablerworld.download
import tablerworld.contacts
import tablerworld.report
from pathlib import Path
from dotenv import load_dotenv
import logging
import json
import os
import pandas as pd

MODULE_PATH = Path(__file__).parent
DIST_FOLDER = Path(MODULE_PATH, "dist")

FILE_CONTACTS_JSON = Path(DIST_FOLDER, "data_contacts.json")
FILE_CONTACTS_EXCEL = Path(DIST_FOLDER, "data_contacts.xlsx")
FILE_CONTACTS_EXCEL_DIRTY = Path(DIST_FOLDER, "data_contacts_dirty.xlsx")

FILE_MANUAL_CONTACTS_EXCEL = "manual_contacts.xlsx"


def main():
    load_dotenv()

    logging.basicConfig(level=logging.WARN, format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s")

    DOWNLOAD_CONTACTS = True
    CONTACTS_CLEAN = True
    CONTACTS_EXPORT_XLSX = True
    DOWNLOAD_PROFILE_PICTURES = True
    GENERATE_REPORT = True

    if not os.path.isfile(FILE_CONTACTS_JSON) or DOWNLOAD_CONTACTS:
        contacts = tablerworld.download.contacts()
        with open(FILE_CONTACTS_JSON, "w") as file_contacts:
            json.dump(contacts, file_contacts)
    else:
        with open(FILE_CONTACTS_JSON, "r") as file_contacts:
            contacts = json.load(file_contacts)

    if os.path.isfile(FILE_MANUAL_CONTACTS_EXCEL):
        df_manual_contacts = pd.read_excel(FILE_MANUAL_CONTACTS_EXCEL)

    df = pd.DataFrame(contacts)

    if CONTACTS_CLEAN:
        df = tablerworld.contacts.clean(df, df_manual_contacts)

    if CONTACTS_EXPORT_XLSX:
        df.to_excel(FILE_CONTACTS_EXCEL, sheet_name="contacts", index=False)

    if DOWNLOAD_PROFILE_PICTURES:
        tablerworld.download.profile_pictures(df)

    if GENERATE_REPORT:
        tablerworld.report.report(df)


if __name__ == "__main__":
    main()
