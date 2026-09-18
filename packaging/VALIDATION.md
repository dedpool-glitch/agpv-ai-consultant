# Prototype validation — 2026-09-18

Validated executable:

`dist/protected-20260918-123026-688350/AgPV-Assistant/AgPV-Assistant.exe`

Keep its entire `AgPV-Assistant` directory together. It occupies approximately
1,191 MiB. This is a local Windows prototype built with PyArmor 9.2.7 trial mode,
Python 3.12.8, Streamlit 1.61.1, and MATLAB Engine 26.1.12. No license was purchased.

## Passed

- Started the executable from a working directory outside the source checkout.
- HTTP server health returned `ok`; browser HTML returned HTTP 200.
- The server URL appeared in captured terminal output.
- Streamlit AppTest rendered the obfuscated application and reran it without
  exceptions; the bootstrap cleaned up its per-run module registration.
- Loaded PVMAPS descriptors and the bundled NASA dataset.
- Opened both bundled Chroma collections: 1,597 book chunks and 1,172 paper chunks.
- Queried both collections using stored embeddings, without a model download.
- Loaded ONNX Runtime 1.30.0.
- Started the packaged MATLAB worker, calculated `sqrt(4) = 2`, and quit MATLAB.
  MATLAB reported R2026a Update 4. This check needed normal license/runtime access
  outside the tool sandbox; a sandboxed MATLAB startup had stalled.
- Inspected the executable's PYZ archive: no original application modules remained.
- Verified application logic files have PyArmor wrappers; the Streamlit bootstrap
  and PyArmor's small runtime loader remain readable by design.
- No `.env` or conversation logs were included in the distribution.
- `git diff --exit-code` confirmed all previously tracked source files unchanged.

## Still to verify

- A full PVMAPS simulation and its complete console output, AI conversation,
  text-query embedding download, workbook export, and restart persistence.
- Manual Ctrl+C from a normal terminal, including while a simulation is active.
  Automated console-event testing was inconclusive; the smoke test terminates
  its own server after checking HTTP and console output.
- Concurrent browser sessions and installation on a second Windows machine.
- MATLAB installed outside `C:\Program Files\MATLAB\R2026a`: the packaged Engine
  currently carries its installed `_arch.txt` paths from this development machine.
- Appropriate PyArmor licensing before treating the prototype as a release.

PyInstaller reports unresolved optional-library warnings (including Arrow Flight
and GDAL-related components). The checks above passed; optional features outside
those checks have not been validated. MATLAB `.m` files and datasets are not
obfuscated by this build. Existing PVMAPS `.p` files remain in their original form.
