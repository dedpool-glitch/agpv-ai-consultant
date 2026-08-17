r""" Testing for the the DLL load order conflict patch between latest version of MATLAB 2026a engine and 
    RAG related methods. 
    
    Issue: services.explainer_context and matlab shares same dll dependency. 
    However, incompatibility between the dll versions causes a crash in matlab 2026a during engine 
    initialization (matlab.engine.start_engine()) .  
    
    Following error is thrown: "C:\Users\Jabir\miniforge3\Lib\site-packages\matlab\engine\matlabfuture.py", line 87, 
    in result handle = pythonengine.getMATLAB(self._future) matlab.engine.EngineError: 
    Loading C:\Program Files\MATLAB\R2026a\bin\win64\mvm_transport\mvm_transport\mwmvmtransport_layered.dllfailed
    with error: The specified procedure could not be found. : state not recoverable: state not recoverable
    
    The bug was patched by lazy importing the dependencies in RAG functions 
    in services.explainer_context. In future, creating the subprocess may be a better solution. 
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_explainer_import_does_not_break_matlab_engine():
    """Import the explainer before starting MATLAB in a clean process."""
    probe = textwrap.dedent(
        """
        import os

        import psutil


        SUSPECT_DLLS = {
            "abseil_dll.dll",
            "grpc.dll",
            "libiomp5md.dll",
            "libprotobuf.dll",
            "torch.dll",
            "torch_cpu.dll",
        }


        def loaded_dlls():
            return {
                os.path.basename(mapping.path).lower(): mapping.path
                for mapping in psutil.Process().memory_maps()
                if mapping.path.lower().endswith(".dll")
            }


        dlls_before = loaded_dlls()

        from services.explainer_context import (
            log_expert_explanation_result,
            retrieve_output_explanation_context,
        )

        dlls_after = loaded_dlls()
        newly_loaded_suspects = {
            name: path
            for name, path in dlls_after.items()
            if name not in dlls_before and name in SUSPECT_DLLS
        }
        if newly_loaded_suspects:
            raise AssertionError(
                "explainer_context loaded suspect DLLs: "
                f"{newly_loaded_suspects}"
            )

        import matlab.engine

        engine = matlab.engine.start_matlab(background=True).result()
        try:
            version = engine.version(nargout=1)
            print(f"MATLAB Engine started successfully: {version}")
        finally:
            engine.quit()
        """
    )

    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )

    assert result.returncode == 0, (
        "The explainer/MATLAB isolation probe failed.\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
