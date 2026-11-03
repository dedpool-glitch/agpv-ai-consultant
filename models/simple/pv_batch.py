"""Run the crop archive's PV-MAPS revision in an isolated MATLAB process."""

from pathlib import Path
from datetime import date
import shutil
import subprocess
import tempfile

import numpy as np
from scipy.io import loadmat, savemat

from models.simple.light import expand_monthly_ground_light


def run_crop_pv_batch(pvmaps_input, script_path, year):
    matlab_exe = shutil.which("matlab")
    if matlab_exe is None:
        raise RuntimeError("MATLAB executable was not found on PATH.")
    source = Path(script_path).resolve() / "pvmaps"
    vendor = Path(__file__).resolve().parent / "vendor"
    functions = vendor / "pvmaps"
    if not (functions / "simulate.p").is_file():
        raise FileNotFoundError(f"Crop PV-MAPS functions are missing: {functions}")

    with tempfile.TemporaryDirectory(prefix="agpv-crop-pv-") as temporary:
        temp = Path(temporary)
        input_path = temp / "input.mat"
        output_path = temp / "result.mat"
        script_path = temp / "run_crop_pv.m"
        settings = {**pvmaps_input, "sim": {**pvmaps_input["sim"],
                    "save_simdat": True, "save_lightpattern": True}}
        savemat(input_path, {"input": settings})

        def quote(path):
            return str(path).replace("'", "''").replace("\\", "/")

        script = f"""cd('{quote(vendor)}');
addpath('{quote(source / 'lib' / 'PVLIB_Matlab-master' / 'PVLIB')}');
addpath('{quote(source / 'lib' / 'textprogressbar')}');
addpath('{quote(functions / 'data')}');
addpath('{quote(functions)}');
incoming = load('{quote(input_path)}', 'input');
incoming = incoming.input;
input = initiate();
input.lat = incoming.lat;
input.lon = incoming.lon;
sections = {{'module','array','sim'}};
for s = 1:numel(sections)
    section = sections{{s}};
    names = fieldnames(incoming.(section));
    for f = 1:numel(names)
        name = names{{f}};
        input.(section).(name) = incoming.(section).(name);
    end
end
input.sim.quickSim = logical(input.sim.quickSim);
input.sim.save_simdat = logical(input.sim.save_simdat);
input.sim.save_lightpattern = logical(input.sim.save_lightpattern);
input.lat = double(input.lat);
input.lon = double(input.lon);
input.module.height = double(input.module.height);
input.module.stc_eff.direct = double(input.module.stc_eff.direct);
input.module.stc_eff.diffuse = double(input.module.stc_eff.diffuse);
input.module.tcoeff = double(input.module.tcoeff);
numeric_array = {{'tilt','azimuth','albedo','pitch','gsHeight','elevation'}};
for f = 1:numel(numeric_array)
    name = numeric_array{{f}};
    input.array.(name) = double(input.array.(name));
end
input.sim.max_parallel_worker = double(input.sim.max_parallel_worker);
pv = simulate(input);
monthly_light = zeros(12,101);
monthly_open_sky = zeros(12,1);
for m = 1:12
    t = pv.time{{m}} / 60;
    curve = pv.simdat{{m}}.groundlight;
    if size(curve,1) ~= numel(t) || size(curve,2) ~= 101
        error('Unexpected PV-MAPS ground-light dimensions');
    end
    monthly_light(m,:) = trapz(t,curve,1) * 3.6;
    ghi = pv.Sun{{m}}.GHI(:) / 1000;
    if numel(ghi) ~= numel(t)
        error('Unexpected PV-MAPS open-sky radiation dimensions');
    end
    monthly_open_sky(m) = trapz(t(:),ghi) * 3.6;
end
yearly_yield = pv.yearly_yield;
monthly_yield = pv.monthly_yield;
daily_yield = pv.daily_yield;
yield_unit = pv.yield_unit;
save('{quote(output_path)}','monthly_light','monthly_open_sky','yearly_yield','monthly_yield','daily_yield','yield_unit','-v7');
"""
        script_path.write_text(script, encoding="utf-8")
        completed = subprocess.run(
            [matlab_exe, "-batch", f"run('{quote(script_path)}')"],
            capture_output=True, text=True, timeout=600,
        )
        if completed.returncode or not output_path.is_file():
            raise RuntimeError(
                "Crop PV-MAPS batch failed: " + (completed.stderr or completed.stdout)[-3000:]
            )
        result = loadmat(output_path, simplify_cells=True)

    light = expand_monthly_ground_light(np.asarray(result["monthly_light"]).tolist(), year)
    monthly_open_sky = np.asarray(result["monthly_open_sky"]).ravel().tolist()
    if len(monthly_open_sky) != 12 or not np.all(np.isfinite(monthly_open_sky)) or min(monthly_open_sky) < 0:
        raise ValueError("PV-MAPS open-sky radiation is incomplete or invalid.")
    open_sky_light = {
        "dates": light["dates"],
        "light_mj_m2": [monthly_open_sky[date.fromisoformat(day).month - 1]
                         for day in light["dates"]],
        "unit": "MJ/m²/day",
    }
    return {
        "yearly_yield": float(result["yearly_yield"]),
        "monthly_yield": np.asarray(result["monthly_yield"]).ravel().tolist(),
        "daily_yield": np.asarray(result["daily_yield"]).ravel().tolist(),
        "yield_unit": str(result["yield_unit"]),
        "warnings": [],
        "ground_light": light,
        "open_sky_light": open_sky_light,
        "final_inputs": {
            "model": "PVMAPS", "lat": pvmaps_input["lat"], "lon": pvmaps_input["lon"],
            "panel_type": pvmaps_input["module"]["cell_tech"],
            "tracking": pvmaps_input["array"]["config"],
            "tilt": pvmaps_input["array"]["tilt"], "pitch": pvmaps_input["array"]["pitch"],
        },
    }
