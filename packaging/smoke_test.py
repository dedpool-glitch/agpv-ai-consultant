"""Check a built executable's HTTP server and packaged application diagnostics."""
import argparse
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    args = parser.parse_args()
    executable = args.executable.resolve(strict=True)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    # An unrelated cwd verifies independence from the original source checkout.
    with tempfile.TemporaryDirectory(prefix="agpv-smoke-") as cwd:
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        with tempfile.TemporaryFile(mode="w+b") as output:
            process = subprocess.Popen(
                [str(executable), "--server.headless=true", "--server.address=127.0.0.1",
                 f"--server.port={port}", "--browser.gatherUsageStats=false"],
                cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW)
            try:
                deadline = time.monotonic() + 60
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError(f"Server exited with {process.returncode}")
                    try:
                        with urllib.request.urlopen(
                                f"http://127.0.0.1:{port}/_stcore/health", timeout=1) as response:
                            if response.read() == b"ok":
                                break
                    except OSError:
                        time.sleep(0.5)
                else:
                    raise RuntimeError("Server health check timed out")
                with urllib.request.urlopen(f"http://127.0.0.1:{port}", timeout=5) as response:
                    assert response.status == 200
                print("PASS: server health and browser HTML from an unrelated directory", flush=True)
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=15)
                output.seek(0)
                console = output.read().decode("utf-8", errors="replace")
                print(console, flush=True)
            if f"http://127.0.0.1:{port}" not in console:
                raise RuntimeError("Expected server URL was missing from console output")
            print("PASS: server URL retained in console output", flush=True)
        result = subprocess.run([str(executable), "--self-test"], cwd=cwd, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
        print(result.stdout.decode("utf-8", errors="replace"), flush=True)
        result.check_returncode()


if __name__ == "__main__":
    main()
