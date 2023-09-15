import json
from pathlib import Path, PurePath


MODULE_PATH = Path(__file__).parent
SETTINGS_JSON = PurePath.joinpath(MODULE_PATH.parent, "settings.json")


def read():
    with open(SETTINGS_JSON, "r") as f:
        config = json.load(f)

    return config
