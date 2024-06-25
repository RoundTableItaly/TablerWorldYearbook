import tablerworld.download
import tablerworld.contacts
import tablerworld.report
from pathlib import Path
import logging
import json
import os
import sys
import pandas as pd

import threading
from tkinter import *
from tkinter import ttk

logger = logging.getLogger("TablerWordYearbook")

# determine if application is a script file or frozen exe
if getattr(sys, "frozen", False):
    APPLICATION_PATH = Path(sys.executable).parent
else:
    APPLICATION_PATH = Path(__file__).parent


OUTPUT_FOLDER = APPLICATION_PATH / "output"

FILE_CONTACTS_JSON = APPLICATION_PATH / "output" / "data_contacts.json"
FILE_CONTACTS_EXCEL = APPLICATION_PATH / "output" / "data_contacts.xlsx"
FILE_CONTACTS_EXCEL_DIRTY = APPLICATION_PATH / "output" / "data_contacts_dirty.xlsx"

FILE_MANUAL_CONTACTS_EXCEL = APPLICATION_PATH / "manual_contacts.xlsx"


def execute(DOWNLOAD_CONTACTS, CONTACTS_CLEAN, CONTACTS_EXPORT_XLSX, DOWNLOAD_PROFILE_PICTURES, GENERATE_REPORT):
    # Create the directory if it doesn't exist
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

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
        logger.info("Export Excel STARTED")
        df.to_excel(FILE_CONTACTS_EXCEL, sheet_name="contacts", index=False)
        logger.info("Export Excel ENDED")

    if DOWNLOAD_PROFILE_PICTURES:
        tablerworld.download.profile_pictures(df)

    if GENERATE_REPORT:
        tablerworld.report.report(df)

    return


def main():

    # tkinter
    root = Tk()
    root.title("TablerWorldYearbook")
    root.resizable(width=False, height=False)

    mainframe = ttk.Frame(root, padding="3 3 12 12")
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    DOWNLOAD_CONTACTS = BooleanVar(value=True)
    check_dowload_contacts = ttk.Checkbutton(
        mainframe,
        text="Download contacts",
        variable=DOWNLOAD_CONTACTS,
        onvalue=True,
        offvalue=False,
    ).grid(column=1, row=1, sticky=W)

    CONTACTS_CLEAN = BooleanVar(value=True)
    check_contacts_clean = ttk.Checkbutton(
        mainframe,
        text="Clean contacts",
        variable=CONTACTS_CLEAN,
        onvalue=True,
        offvalue=False,
    ).grid(column=1, row=2, sticky=W)

    CONTACTS_EXPORT_XLSX = BooleanVar(value=True)
    check_contacts_export_xlsx = ttk.Checkbutton(
        mainframe,
        text="Export contacts Excel",
        variable=CONTACTS_EXPORT_XLSX,
        onvalue=True,
        offvalue=False,
    ).grid(column=1, row=3, sticky=W)

    DOWNLOAD_PROFILE_PICTURES = BooleanVar(value=True)
    check_download_profile_pictures = ttk.Checkbutton(
        mainframe,
        text="Download profile pictures",
        variable=DOWNLOAD_PROFILE_PICTURES,
        onvalue=True,
        offvalue=False,
    ).grid(column=1, row=4, sticky=W)

    GENERATE_REPORT = BooleanVar(value=True)
    check_generate_report = ttk.Checkbutton(
        mainframe,
        text="Generate report",
        variable=GENERATE_REPORT,
        onvalue=True,
        offvalue=False,
    ).grid(column=1, row=5, sticky=W)

    ttk.Button(
        mainframe,
        text="Execute",
        command=lambda: threading.Thread(
            target=execute,
            args=(
                DOWNLOAD_CONTACTS.get(),
                CONTACTS_CLEAN.get(),
                CONTACTS_EXPORT_XLSX.get(),
                DOWNLOAD_PROFILE_PICTURES.get(),
                GENERATE_REPORT.get(),
            ),
        ).start(),
    ).grid(column=1, row=6, sticky=W)

    for child in mainframe.winfo_children():
        child.grid_configure(padx=5, pady=5)

    text_log = Text(mainframe, width=150, height=30, wrap="none")
    ys = ttk.Scrollbar(mainframe, orient="vertical", command=text_log.yview)
    xs = ttk.Scrollbar(mainframe, orient="horizontal", command=text_log.xview)
    text_log["yscrollcommand"] = ys.set
    text_log["xscrollcommand"] = xs.set
    text_log.grid(column=1, row=7, padx=(5, 0), pady=(5, 0), sticky="NEWS")
    xs.grid(column=1, row=8, sticky="we")
    ys.grid(column=2, row=7, sticky="ns")

    # Logging
    class MyHandlerText(logging.StreamHandler):
        def __init__(self, textctrl):
            logging.StreamHandler.__init__(self)  # initialize parent
            self.textctrl = textctrl

        def emit(self, record):
            msg = self.format(record)
            self.textctrl.config(state="normal")
            self.textctrl.insert("end", msg + "\n")
            self.flush()
            self.textctrl.config(state="disabled")

    log_format = logging.Formatter(fmt="%(asctime)s %(name)-12s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    stderrHandler = logging.StreamHandler()  # no arguments => stderr
    # stderrHandler.setFormatter(log_format)

    guiHandler = MyHandlerText(text_log)
    guiHandler.setFormatter(log_format)

    logger.addHandler(stderrHandler)
    logger.addHandler(guiHandler)
    logger.setLevel(logging.INFO)

    root.mainloop()


if __name__ == "__main__":
    main()
