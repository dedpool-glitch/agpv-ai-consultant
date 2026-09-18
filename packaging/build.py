"""Build only staged copies. Never patch or overwrite the application's sources."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PACKAGES = ("llm", "models", "model_desc", "questionnaire", "rag", "services", "ui")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--obfuscate", action="store_true")
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.error("Build this Windows executable on Windows.")
    required = ["PyInstaller", "streamlit", "matlabengine", "chromadb", "onnxruntime"]
    if args.obfuscate:
        required.append("pyarmor")
    for name in required:
        try:
            importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            parser.error(f"Missing {name}; install application and build dependencies first.")

    # Unique directories avoid destructive cleanup and preserve earlier good builds.
    label = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    mode = "protected" if args.obfuscate else "plain"
    work = HERE / "build" / f"{mode}-{label}"
    stage = work / "application"
    stage.mkdir(parents=True)
    shutil.copy2(ROOT / "app.py", stage / "agpv_app.py")
    shutil.copy2(ROOT / "constants.py", stage / "constants.py")
    for name in PACKAGES:
        # Runtime model resources are copied separately, not scanned as Python.
        shutil.copytree(ROOT / name, stage / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "bin"))
    runner = stage / "models/pvmaps/matlab_runner.py"
    runner.rename(runner.with_name("_matlab_runner_impl.py"))
    shutil.copy2(HERE / "runtime_matlab_runner.py", runner)
    modules = []
    for source in stage.rglob("*.py"):
        parts = list(source.relative_to(stage).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        if parts:
            modules.append(".".join(parts))
    (work / "modules.json").write_text(json.dumps(modules), encoding="utf-8")

    payload = stage
    env = os.environ.copy()
    if args.obfuscate:
        payload = work / "protected"
        env["PYARMOR_HOME"] = str(HERE / ".pyarmor")
        # Do not fall back to plaintext on a license/compatibility failure.
        subprocess.run(
            [sys.executable, "-m", "pyarmor.cli", "gen", "-r", "-O", str(payload),
             "agpv_app.py", "constants.py", *PACKAGES], cwd=stage, env=env, check=True)
        for source in stage.rglob("*.py"):
            target = payload / source.relative_to(stage)
            if not target.exists() or "__pyarmor__" not in target.read_text(encoding="utf-8"):
                raise RuntimeError(f"Script was not protected: {source.relative_to(stage)}")

    output = HERE / "dist" / f"{mode}-{label}"
    env["AGPV_BUILD_WORK"] = str(work)
    build_python = sys.executable
    if (Path(sys.base_prefix) / "conda-meta").is_dir():
        # PyInstaller needs the real Conda prefix to locate NumPy/SciPy DLLs.
        # Run the base interpreter with our isolated build tools on PYTHONPATH;
        # nothing is installed into or changed in the base environment.
        build_python = str(Path(sys.base_prefix) / "python.exe")
        env["PYTHONPATH"] = os.pathsep.join(
            [str(Path(sys.prefix) / "Lib/site-packages"), env.get("PYTHONPATH", "")])
    subprocess.run(
        [build_python, "-m", "PyInstaller", "--noconfirm", "--distpath", str(output),
         "--workpath", str(work / "pyinstaller"), str(HERE / "app.spec")],
        cwd=HERE, env=env, check=True)
    distribution = output / "AgPV-Assistant"
    from PyInstaller.archive.readers import CArchiveReader
    archive = CArchiveReader(str(distribution / "AgPV-Assistant.exe"))
    leaked = set(modules).intersection(archive.open_embedded_archive("PYZ.pyz").toc)
    if leaked:
        raise RuntimeError(f"Original application bytecode remained in executable: {sorted(leaked)}")
    app = distribution / "application"
    shutil.copytree(payload, app)
    shutil.copy2(HERE / "streamlit_entry.py", app / "app.py")
    # Only allowlisted resources: never copy .env, logs, or the entire repository.
    shutil.copy2(ROOT / "models/pvmaps/pvmaps.json", app / "models/pvmaps/pvmaps.json")
    shutil.copytree(ROOT / "models/pvmaps/bin", app / "models/pvmaps/bin",
                    ignore=shutil.ignore_patterns("*.asv", "__pycache__"))
    (app / "data").mkdir()
    shutil.copy2(ROOT / "data/panel_specs.json", app / "data/panel_specs.json")
    # Use SQLite backup to obtain a consistent database snapshot; stop ingestion
    # during packaging so the separate Chroma index files match the snapshot.
    import sqlite3
    db_source = ROOT / "data/chroma_db"
    db_target = app / "data/chroma_db"
    shutil.copytree(db_source, db_target, ignore=shutil.ignore_patterns("chroma.sqlite3*"))
    with sqlite3.connect((db_source / "chroma.sqlite3").as_uri() + "?mode=ro", uri=True) as src:
        with sqlite3.connect(db_target / "chroma.sqlite3") as dst:
            src.backup(dst)
    versions = {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()}
    (distribution / "build-info.json").write_text(
        json.dumps({"obfuscated": args.obfuscate, "python": sys.version,
                    "packages": versions}, indent=2), encoding="utf-8")
    shutil.copy2(HERE / "DISTRIBUTION.txt", distribution / "README.txt")
    # The validation record describes the specific tested prototype, not an
    # automatic claim that a future build has passed those checks.
    shutil.copy2(HERE / "VALIDATION.md", distribution / "VALIDATION.md")
    print(f"\nBuild complete: {distribution / 'AgPV-Assistant.exe'}", flush=True)


if __name__ == "__main__":
    main()
