import json
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, copy_metadata

here = Path(SPECPATH)
work = Path(os.environ['AGPV_BUILD_WORK'])
stage = work / 'application'
local_modules = json.loads((work / 'modules.json').read_text(encoding='utf-8'))
datas, binaries, hidden = [], [], list(local_modules)
for package in ('streamlit', 'chromadb', 'onnxruntime', 'matlab'):
    package_data, package_binaries, package_imports = collect_all(package)
    datas += package_data
    binaries += package_binaries
    hidden += package_imports
datas += copy_metadata('streamlit')

a = Analysis(
    [str(here / 'launcher.py')], pathex=[str(stage)],
    binaries=binaries, datas=datas, hiddenimports=hidden,
    # The browser application retrieves pre-indexed documents; ingestion is a
    # separate development command. Avoid loading Torch's conflicting DLLs.
    excludes=['docling', 'docling_core', 'transformers', 'torch', 'tensorflow',
              'pytest', 'IPython', 'notebook', 'jupyterlab'],
    noarchive=False,
)
# Analyze the original modules for dependencies, but ship only staged payloads.
# This also prevents recoverable original bytecode in a protected build's PYZ.
local_names = set(local_modules)
a.pure = [item for item in a.pure if item[0] not in local_names]
a.datas = [item for item in a.datas
           if not Path(item[1]).resolve().is_relative_to(stage.resolve())]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True,
          name='AgPV-Assistant', debug=False, strip=False, upx=False, console=True)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='AgPV-Assistant')
