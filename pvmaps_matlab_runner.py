import matlab.engine 
import os

def run_pvmaps(pvmaps_input, script_path):
    eng = matlab.engine.start_matlab()
    script_path = os.path.normpath(script_path)
    pvmaps_path = os.path.join(script_path, "pvmaps")
    eng.cd(script_path, nargout=0)
    eng.addpath(pvmaps_path, nargout=0)
    eng.addpath(os.path.join(pvmaps_path, "data"), nargout=0)
    eng.addpath(os.path.join(pvmaps_path, "lib", "textprogressbar"), nargout=0)
    eng.addpath(os.path.join(pvmaps_path, "lib", "PVLIB_Matlab-master", "PVLIB"), nargout=0)
        
    eng.eval("input=initiate();",nargout=0)
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

    #default simulator settings
    eng.eval("input.sim.max_parallel_worker=0;",nargout=0)
    eng.eval("input.sim.quickSim=true;",nargout=0)
    eng.eval("input.sim.save_simdat=true;",nargout=0)
    eng.eval("input.sim.save_lightpattern=false;",nargout=0)

    #run the simulation
    pvmaps_output = eng.simulate(eng.workspace["input"],nargout=1) #call function simulate with input.

    return {
        "yearly_yield": float(pvmaps_output["yearly_yield"]),
        "monthly_yield": list(pvmaps_output["monthly_yield"][0]),
        "daily_yield": list(pvmaps_output["daily_yield"][0]),
        "yield_unit": str(pvmaps_output["yield_unit"]),
        "warnings": [],
        "assumptions": {
            "model": "PVMAPS",
            "lat": pvmaps_input["lat"],
            "lon": pvmaps_input["lon"],
            "panel_type": pvmaps_input["module"]["cell_tech"],
            "tracking": pvmaps_input["array"]["config"],
            "tilt": pvmaps_input["array"]["tilt"],
            "pitch": pvmaps_input["array"]["pitch"],
    }
    }