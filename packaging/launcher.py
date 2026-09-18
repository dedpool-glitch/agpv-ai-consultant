"""Console entry point; application sources remain untouched."""
import multiprocessing
import os
from pathlib import Path
import sys
import tempfile


def matlab_worker(request_path, result_path):
    import ctypes
    import json
    # PyInstaller adds its native-library directory to the Windows DLL search
    # path. Clear that override before loading the installed MATLAB libraries.
    # This worker never imports Streamlit, Arrow, Chroma, or their native DLLs.
    if sys.platform == "win32":
        if not ctypes.windll.kernel32.SetDllDirectoryW(None):
            raise ctypes.WinError()
    request = json.loads(Path(request_path).read_text(encoding="utf-8"))
    if request.get("check"):
        import matlab.engine
        engine = matlab.engine.start_matlab()
        try:
            result = {"sqrt": engine.sqrt(4.0), "version": engine.version()}
        finally:
            engine.quit()
    else:
        from models.pvmaps._matlab_runner_impl import run_pvmaps
        result = run_pvmaps(request["input"], request["script_path"])
    Path(result_path).write_text(json.dumps(result), encoding="utf-8")
    return 0


def self_test(application):
    """Exercise the packaged app without API calls or conversation logging."""
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(application / "app.py"), default_timeout=60).run()
    if app.exception:
        raise RuntimeError("; ".join(str(error.message) for error in app.exception))
    app.run()
    if app.exception:
        raise RuntimeError("; ".join(str(error.message) for error in app.exception))
    if any(name.startswith("_agpv_session_") for name in sys.modules):
        raise RuntimeError("Streamlit bootstrap leaked a session module")
    print("PASS: Streamlit application rendered and reran", flush=True)
    from models.pvmaps.descriptor import get_pvmaps_input_descriptors
    assert get_pvmaps_input_descriptors()
    from services.nasa_power_lookup import get_climate_summary
    assert get_climate_summary(40.4, -86.9)
    print("PASS: descriptors and NASA dataset loaded", flush=True)
    from rag.vector_db import get_chroma_client
    client = get_chroma_client()
    collections = client.list_collections()
    print("Chroma collections:", [(c.name, c.count()) for c in collections], flush=True)
    if not collections:
        raise RuntimeError("The packaged retrieval database has no collections")
    for collection in collections:
        if collection.count():
            sample = collection.get(limit=1, include=["embeddings"])
            matches = collection.query(query_embeddings=sample["embeddings"], n_results=1)
            assert matches["ids"][0], f"No vector match in {collection.name}"
    print("PASS: stored-vector retrieval (no embedding download)", flush=True)
    import onnxruntime
    print("PASS: Chroma and ONNX runtime loaded", onnxruntime.__version__, flush=True)
    from models.pvmaps.matlab_runner import check_matlab
    result = check_matlab()
    assert result["sqrt"] == 2.0
    print("PASS: isolated MATLAB Engine computed sqrt(4) = 2;", result["version"], flush=True)
    return 0


def main():
    multiprocessing.freeze_support()
    distribution = Path(sys.executable).resolve().parent
    application = distribution / "application"
    if not (application / "app.py").is_file():
        raise RuntimeError("Keep the executable and its application folder together.")
    # A portable distribution: resources, the database, and outputs persist here.
    # Fail explicitly instead of silently losing the application's best-effort logs.
    try:
        with tempfile.TemporaryFile(dir=application):
            pass
    except OSError as exc:
        raise RuntimeError("Extract the entire distribution to a writable folder.") from exc
    sys.path.insert(0, str(application))
    os.chdir(application)
    if len(sys.argv) == 4 and sys.argv[1] == "--matlab-worker":
        return matlab_worker(sys.argv[2], sys.argv[3])
    # Frozen paths are not site-packages paths; otherwise Streamlit mistakes
    # the packaged installation for a development checkout and uses a dev server.
    os.environ.setdefault("STREAMLIT_GLOBAL_DEVELOPMENT_MODE", "false")
    from dotenv import load_dotenv
    load_dotenv(distribution / ".env")
    if sys.argv[1:] == ["--self-test"]:
        return self_test(application)
    # Import only after the application path is set. stdout/stderr stay attached.
    from streamlit.web import cli
    sys.argv = ["streamlit", "run", str(application / "app.py"), *sys.argv[1:]]
    return cli.main()


if __name__ == "__main__":
    raise SystemExit(main())
