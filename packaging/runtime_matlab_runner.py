"""Packaging-only MATLAB process boundary; preserves the original runner API."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def _invoke(request):
    with tempfile.TemporaryDirectory(prefix="agpv-matlab-") as directory:
        request_path = Path(directory) / "request.json"
        result_path = Path(directory) / "result.json"
        request_path.write_text(json.dumps(request), encoding="utf-8")
        subprocess.run(
            [sys.executable, "--matlab-worker", str(request_path), str(result_path)],
            check=True, stdout=sys.stdout, stderr=sys.stderr,
            creationflags=subprocess.CREATE_NO_WINDOW)
        return json.loads(result_path.read_text(encoding="utf-8"))


def run_pvmaps(pvmaps_input, script_path):
    return _invoke({"input": pvmaps_input, "script_path": str(script_path)})


def check_matlab():
    return _invoke({"check": True})
