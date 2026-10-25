"""PT-01 recovery research and local verification."""

import pathlib
import sys

# Recovery modules reuse the atlas helpers in scripts/.
_SCRIPTS = str(pathlib.Path(__file__).resolve().parents[1] / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
