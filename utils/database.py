import json
from os import makedirs, path, remove, rename
from tempfile import mkstemp
from typing import Optional
from datetime import datetime

from utils import l


DATA_DIR = path.realpath(path.join(path.dirname(__file__), '../data'))


def load_data(filename: str) -> dict:
    fullpath = path.join(DATA_DIR, filename)
    try:
        with open(fullpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        l.info(f"Loaded data file {path.relpath(filename)!r}")
        return data
    except Exception:
        msg = f"Error loading {path.relpath(filename)!r};"
        try:
            rename(fullpath, f'{fullpath}.{int(datetime.now().timestamp())}.bak')
            msg += f" backing up existing file and"
        except Exception:
            pass
        msg += " assuming empty dictionary"
        l.warning(msg)
        return {}


def save_data(filename: str, data: dict) -> None:
    # Use a temporary file so that the original one doesn't get corrupted in the
    # case of an error.
    fullpath = path.join(DATA_DIR, filename)
    try:
        if not path.isdir(path.dirname(fullpath)):
            makedirs(path.dirname(fullpath))
        tempfile, tempfile_path = mkstemp(dir=DATA_DIR)
        with open(tempfile, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent='\t')
        rename(tempfile_path, path.join(DATA_DIR, filename))
        l.info(f"Saved data file {path.relpath(filename)!r}")
    except Exception:
        l.warning(f"Error saving {path.relpath(filename)!r}")
    finally:
        try:
            remove(tempfile_path)
        except Exception:
            pass


class DB(dict):
    """A simple subclass of dict implementing JSON save/load.
    Do not instantiate this class directly; use database.get_db() instead.
    Read-only attributes:
    - name -- str
    - filepath -- str
    """

    def __init__(self, db_name: str, db_path: Optional[str] = None, do_not_instantiate_directly=None):
        """Do not instantiate this class directly; use database.get_db()
        instead.
        """
        if do_not_instantiate_directly != 'ok':
            # I'm not sure whether TypeError is really the best choice here.
            raise TypeError("Do not instantiate DB object directly; use get_db() instead")
        self.name = db_name
        self.filepath = path.join(db_path or DATA_DIR, db_name + '.json')
        self.reload()

    def replace(self, new_data: dict) -> None:
        self.clear()
        self.update(new_data)

    def reload(self) -> None:
        self.replace(load_data(self.filepath))

    def save(self) -> None:
        save_data(self.filepath, self)


_DATABASES = {}


def get_db(db_name: str, db_path: Optional[str] = None) -> DB:
    if db_name not in _DATABASES:
        _DATABASES[db_name] = DB(db_name, db_path, 'ok')
    return _DATABASES[db_name]
