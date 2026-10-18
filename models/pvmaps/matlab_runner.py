import matlab.engine
import os
from pathlib import Path


NEURAL_NETWORK_CELL_TECHNOLOGIES = {"PVK_SI_2T", "PVK_SI_4T"}


def _validate_matlab_dependencies(eng, cell_tech):
    """Fail clearly when a cell model needs an unavailable MATLAB toolbox."""
    if cell_tech not in NEURAL_NETWORK_CELL_TECHNOLOGIES:
        return

    has_network_class = bool(
        eng.eval("~isempty(which('network'))", nargout=1)
    )
    if not has_network_class:
        raise RuntimeError(
            f"{cell_tech} requires MATLAB Deep Learning Toolbox because PVMAPS "
            "loads a saved neural-network model for this cell technology. Install "
            "that toolbox or select AL_BSF, BI_PERC, SHJ, or SHJ_NN."
        )


def run_pvmaps(pvmaps_input, script_path):
    script_path = Path(script_path).resolve()
    
    # Check for the proper path 
    if not script_path.is_dir():
        raise FileNotFoundError(f"PVMAPS folder does not exist: {script_path}")

    eng = matlab.engine.start_matlab()

    try:
        script_path = os.path.normpath(str(script_path))
        pvmaps_path = os.path.join(script_path, "pvmaps")
        eng.cd(script_path, nargout=0)
        eng.addpath(pvmaps_path, nargout=0)
        eng.addpath(os.path.join(pvmaps_path, "data"), nargout=0)
        eng.addpath(os.path.join(pvmaps_path, "lib", "textprogressbar"), nargout=0)
        eng.addpath(os.path.join(pvmaps_path, "lib", "PVLIB_Matlab-master", "PVLIB"), nargout=0)


        eng.eval("input=initiate();",nargout=0)
        _validate_matlab_dependencies(eng, pvmaps_input["module"]["cell_tech"])
        #input module fields(properties of a single solar panel)
        eng.eval(f"input.module.cell_tech='{pvmaps_input['module']['cell_tech']}';",nargout=0)
        eng.eval(f"input.module.height={pvmaps_input['module']['height']};",nargout=0)
        eng.eval(f"input.module.stc_eff.direct={pvmaps_input['module']['stc_eff']['direct']};",nargout=0)
        eng.eval(f"input.module.stc_eff.diffuse={pvmaps_input['module']['stc_eff']['diffuse']};",nargout=0)
        eng.eval(f"input.module.tcoeff={pvmaps_input['module']['tcoeff']};",nargout=0)

        #input array fields(properties of the solar panel array)
        eng.eval(f"input.array.config='{pvmaps_input['array']['config']}';",nargout=0)
        eng.eval(f"input.array.tilt={pvmaps_input['array']['tilt']};",nargout=0)
        eng.eval(f"input.array.azimuth={pvmaps_input['array']['azimuth']};",nargout=0)
        eng.eval(f"input.array.albedo={pvmaps_input['array']['albedo']};",nargout=0)
        eng.eval(f"input.array.pitch={pvmaps_input['array']['pitch']};",nargout=0)
        eng.eval(f"input.array.gsHeight={pvmaps_input['array']['gsHeight']};",nargout=0)
        eng.eval(f"input.array.elevation={pvmaps_input['array']['elevation']};",nargout=0)

        #location coordinates
        eng.eval(f"input.lat={pvmaps_input['lat']};",nargout=0)  #resemlbes writing code in MATLAB
        eng.eval(f"input.lon={pvmaps_input['lon']};",nargout=0)

        # Simulator settings supplied by the descriptor-driven input form.
        sim = pvmaps_input["sim"]
        eng.eval(f"input.sim.max_parallel_worker={sim['max_parallel_worker']};", nargout=0)
        eng.eval(f"input.sim.quickSim={str(bool(sim['quickSim'])).lower()};", nargout=0)
        eng.eval(f"input.sim.save_simdat={str(bool(sim['save_simdat'])).lower()};", nargout=0)
        eng.eval(
            f"input.sim.save_lightpattern={str(bool(sim['save_lightpattern'])).lower()};",
            nargout=0,
        )

        #run the simulation
        pvmaps_output = eng.simulate(eng.workspace["input"],nargout=1) #call function simulate with input.
        warnings = []
        return {
            "yearly_yield": float(pvmaps_output["yearly_yield"]),
            "monthly_yield": list(pvmaps_output["monthly_yield"][0]),
            "daily_yield": list(pvmaps_output["daily_yield"][0]),
            "yield_unit": str(pvmaps_output["yield_unit"]),
            "warnings": warnings,
            "final_inputs": {
                "model": "PVMAPS",
                "lat": pvmaps_input["lat"],
                "lon": pvmaps_input["lon"],
                "panel_type": pvmaps_input["module"]["cell_tech"],
                "tracking": pvmaps_input["array"]["config"],
                "tilt": pvmaps_input["array"]["tilt"],
                "pitch": pvmaps_input["array"]["pitch"],
        }
        }
    finally:
        # Without this, every simulation leaves its MATLAB process running in
        # the background indefinitely, these leaked processes pile up and eventually
        # exhaust the machine's memory. Always shut the engine down, whether
        # the simulation succeeded or raised.
        eng.quit()
