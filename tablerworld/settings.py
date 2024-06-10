import json
from pathlib import Path
import sys


# determine if application is a script file or frozen exe
if getattr(sys, "frozen", False):
    APPLICATION_PATH = Path(sys.executable).parent
else:
    APPLICATION_PATH = Path(__file__).parent.parent

SETTINGS_JSON = APPLICATION_PATH / "settings.json"


def read():
    with open(SETTINGS_JSON, "r") as f:
        config = json.load(f)

    return config
