"""Put the repository root on sys.path so scripts can import the recovery package."""

import pathlib
import sys

ROOT = str(pathlib.Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
