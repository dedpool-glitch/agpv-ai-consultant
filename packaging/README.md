# Separate Windows packaging

All build code and generated files live here. Application sources are copied,
never patched. This builds a console executable plus a supporting folder.

## Build

Use the Python environment that already runs the application successfully.
Its MATLAB Engine must match the installed MATLAB. The repository requirements
currently target R2025b; the inspected development environment uses R2026a.
Do not blindly reinstall the older Engine over that working environment.

```powershell
& 'C:\Users\Jabir\miniforge3\python.exe' -m venv --system-site-packages packaging/.venv
& .\packaging\.venv\Scripts\python.exe -m pip install -r packaging/requirements-build.txt
& .\packaging\.venv\Scripts\python.exe -m pip install --ignore-installed --no-deps grpcio==1.82.1
& .\packaging\build.ps1 -Python .\packaging\.venv\Scripts\python.exe
# Optional protected build; never silently falls back to plaintext:
& .\packaging\build.ps1 -Python .\packaging\.venv\Scripts\python.exe -Obfuscate
```

Stop document ingestion while building so copied Chroma index files remain
consistent. Each invocation creates a unique directory in `build/` and `dist/`.
The printed executable path identifies the completed build. Ship its whole
`AgPV-Assistant` folder, not just the executable. Do not ship `build/`, which
contains unprotected analysis sources even when building with obfuscation.

Build tools live in the isolated virtual environment; application dependencies
are inherited from the working environment. Versions are recorded in the output.
For repeatable releases, recreate a clean environment with those versions.

## How it works

PyInstaller analyzes ordinary staged modules, collects third-party dependencies,
then removes our modules from its bytecode archive. The selected application
payload is copied alongside the executable. In protected mode all Python payload
files must contain PyArmor wrappers, and its native runtime is shipped with them.
The only readable application entry is a small bootstrap that imports
the protected app module: Streamlit's direct execution of a protected entry script
is incompatible with PyArmor. Each run gets its own module globals, preserving
session isolation. The bootstrap contains no application logic.
Only in the staged copy, `matlab_runner.py` becomes a subprocess adapter and the
original runner is retained as `_matlab_runner_impl.py`. Both are obfuscated in
protected builds. The worker uses the same executable, clears PyInstaller's DLL
search override, and loads MATLAB without Streamlit/Chroma's native dependencies.
Input/results travel through temporary JSON files; stdout/stderr pass through to
the parent's console. No simulation logic is changed in the original runner.
PyArmor's license and Python-version restrictions apply; a trial may reject large
scripts. No license is purchased or activated by this build.

The launcher establishes the application directory, loads an optional external
`.env`, and calls Streamlit's CLI with the user's flags. stdout/stderr are retained.
Relative resource paths work unchanged because the original directory layout is
preserved in the writable portable distribution. No code is imported from the
source checkout at runtime.

The app's PDF-ingestion-only dependencies (Docling, Transformers, Torch) are
excluded. Retrieval uses the supplied Chroma index and ONNX embedding runtime.
Embedding downloads, MATLAB installation discovery, Streamlit reruns/caching,
and native DLL compatibility still require testing on the target machine.

## Validation before distribution

Run `AgPV-Assistant.exe --self-test` for application rendering, dataset loading,
stored-vector retrieval, and MATLAB Engine arithmetic checks without an LLM call.
For server startup and console-output checks as well:

```powershell
& .\packaging\.venv\Scripts\python.exe packaging/smoke_test.py 'path\to\AgPV-Assistant.exe'
```

The HTTP smoke test terminates its server after checking it; manually verify
Ctrl+C in an interactive terminal. The self-test starts and quits MATLAB.

- Start from a different working directory and check the printed server URL.
- Open the browser; verify the app renders without import errors.
- Run retrieval, a MATLAB simulation, and workbook export using a valid API key.
- Check output files persist across restart and Ctrl+C stops the server.
- Repeat with an obfuscated build and on a second Windows machine with MATLAB.
- Confirm `.env` and source-checkout logs are absent from the distribution.

A server health response alone does not prove browser-session execution or a
successful simulation. See `VALIDATION.md` for what was actually checked.
