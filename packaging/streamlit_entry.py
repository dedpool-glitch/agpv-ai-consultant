"""Readable bootstrap only; application logic lives in the separate payload."""
import importlib.util
from pathlib import Path
import sys
import uuid

# Each Streamlit rerun/session needs its own globals, just like an ordinary
# script. A shared import/reload would leak globals across concurrent sessions.
_name = "_agpv_session_" + uuid.uuid4().hex
_spec = importlib.util.spec_from_file_location(_name, Path(__file__).with_name("agpv_app.py"))
_module = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _module
try:
    _spec.loader.exec_module(_module)
finally:
    sys.modules.pop(_name, None)
