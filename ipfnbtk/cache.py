# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

import sys
import os
from pathlib import Path
import pickle


try:
    _CACHEDIR = Path(os.environ["IPFNB_CACHEDIR"])
    assert _CACHEDIR.is_dir(), f"{str(_CACHEDIR)} is not a directory"

except KeyError as exc:
    sys.exit(f"Missing environment variable: {exc.args[0]}")


def cache_dump(data, filename):
    ofile = _CACHEDIR.joinpath(f"{filename}.pkl")
    pickle.dump(data, ofile.open("wb"))


def cache_load(filename):
    ofile = _CACHEDIR.joinpath(f"{filename}.pkl")
    return pickle.load(ofile.open("rb"))
