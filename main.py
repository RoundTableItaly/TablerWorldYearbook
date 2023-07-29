from tablerworld import download
import json
import os
import pandas as pd

FILE_CONTACTS_JSON = "data_contacts.json"
FILE_CONTACTS_EXCEL = "data_contacts.xlsx"


def main():
    # Download contacts if not available
    if not os.path.isfile(FILE_CONTACTS_JSON):
        contacts = download.contacts()
        with open(FILE_CONTACTS_JSON, "w") as file_contacts:
            json.dump(contacts, file_contacts)
    else:
        # Read and parse contacts file
        with open(FILE_CONTACTS_JSON, "r") as file_contacts:
            contacts = json.load(file_contacts)

    df = pd.DataFrame(contacts)

    # Clean rows
    def clean_name(cell):
        return cell.title()

    def clean_phonenumbers(cell):
        if not cell:
            return "-"

        mobile = None
        home = None
        for item in cell:
            if item.get("type", None) == "home":
                home = item.get("value", None)
            if item.get("type", None) == "mobile":
                mobile = item.get("value", None)

        return mobile if not None else home

    def clean_address(cell):
        if not cell:
            return "-"

        item = cell[0]

        street1 = item.get("street1", None)
        street2 = item.get("street2", None)
        postal_code = item.get("postal_code", None)
        city = item.get("city", None)

        return f"{street1} - {postal_code} {city}"

    df["first_name"] = df["first_name"].apply(clean_name)
    df["last_name"] = df["last_name"].apply(clean_name)
    df["phonenumbers"] = df["phonenumbers"].apply(clean_phonenumbers)
    df["address"] = df["address"].apply(clean_address)

    # Save excel file
    df.to_excel(FILE_CONTACTS_EXCEL, sheet_name="contacts", index=False)


if __name__ == "__main__":
    main()
