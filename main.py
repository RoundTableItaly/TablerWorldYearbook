import tablerworld.download
import tablerworld.contacts
import tablerworld.report
from pathlib import Path
import logging
import json
import os
import pandas as pd

import tkinter as tk


MODULE_PATH = Path(__file__).parent
DIST_FOLDER = Path(MODULE_PATH, "dist")

FILE_CONTACTS_JSON = Path(DIST_FOLDER, "data_contacts.json")
FILE_CONTACTS_EXCEL = Path(DIST_FOLDER, "data_contacts.xlsx")
FILE_CONTACTS_EXCEL_DIRTY = Path(DIST_FOLDER, "data_contacts_dirty.xlsx")

FILE_MANUAL_CONTACTS_EXCEL = "manual_contacts.xlsx"


DOWNLOAD_CONTACTS = True
CONTACTS_CLEAN = True
CONTACTS_EXPORT_XLSX = True
DOWNLOAD_PROFILE_PICTURES = False
GENERATE_REPORT = True


def main():
    window = tk.Tk()
    window.geometry("600x600")
    window.title("Hello TkInter!")

    def first_print():
        text = "Hello World!"
        text_output = tk.Label(window, text=text, fg="red", font=("Helvetica", 16))
        text_output.grid(row=0, column=1)

    first_button = tk.Button(text="Saluta!", command=first_print)
    first_button.grid(row=0, column=0)

    window.mainloop()


def main_2():
    logging.basicConfig(
        level=logging.WARN, format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
    )

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
