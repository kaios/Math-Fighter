"""Small save file: the bonus level unlock and the music setting.
Also the folder where generated music is cached. Never crashes the game:
if the file can't be read or written, the defaults are used."""

import json
import os
import sys


def data_dir():
    if os.environ.get("MATHFIGHTER_DATA"):          # used by the tests
        return os.environ["MATHFIGHTER_DATA"]
    if os.environ.get("ANDROID_PRIVATE"):           # app-private storage on Android
        return os.environ["ANDROID_PRIVATE"]
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(base, "MathFighter")


def _path():
    return os.path.join(data_dir(), "save.json")


def load():
    try:
        with open(_path(), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def store(data):
    try:
        os.makedirs(data_dir(), exist_ok=True)
        tmp = _path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp, _path())
    except OSError:
        pass
