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

    ALWAYS_DOWNLOAD_CONTACTS = False

    if not os.path.isfile(FILE_CONTACTS_JSON) or ALWAYS_DOWNLOAD_CONTACTS:
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
    df = tablerworld.contacts.clean(df)

    # Save excel file
    df.to_excel(FILE_CONTACTS_EXCEL, sheet_name="contacts", index=False)

    # Download profile pictures
    tablerworld.download.profile_pictures(df)

    # Generate report
    tablerworld.report.report(df)


if __name__ == "__main__":
    main()
