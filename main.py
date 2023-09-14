import tablerworld.download
import tablerworld.contacts
import tablerworld.report
from dotenv import load_dotenv
import logging
import json
import os
import pandas as pd


FILE_CONTACTS_JSON = "dist/data_contacts.json"
FILE_CONTACTS_EXCEL = "dist/data_contacts.xlsx"


def main():
    load_dotenv()
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.WARN)

    DOWNLOAD_CONTACTS = False
    CONTACTS_CLEAN = True
    CONTACTS_EXPORT_XLSX = True
    DOWNLOAD_PROFILE_PICTURES = False
    GENERATE_REPORT = True

    if not os.path.isfile(FILE_CONTACTS_JSON) or DOWNLOAD_CONTACTS:
        # Download contacts if not available or if forced
        contacts = tablerworld.download.contacts()
        with open(FILE_CONTACTS_JSON, "w") as file_contacts:
            json.dump(contacts, file_contacts)
    else:
        # Read and parse contacts file
        with open(FILE_CONTACTS_JSON, "r") as file_contacts:
            contacts = json.load(file_contacts)

    # Create Pandas dataframe
    df = pd.DataFrame(contacts)

    # Apply cleaning
    if CONTACTS_CLEAN:
        df = tablerworld.contacts.clean(df)

    # Save excel file
    if CONTACTS_EXPORT_XLSX:
        df.to_excel(FILE_CONTACTS_EXCEL, sheet_name="contacts", index=False)

    # Download profile pictures
    if DOWNLOAD_PROFILE_PICTURES:
        tablerworld.download.profile_pictures(df)

    # Generate report
    if GENERATE_REPORT:
        tablerworld.report.report(df)


if __name__ == "__main__":
    main()
