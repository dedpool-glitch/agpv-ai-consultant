% Crop yield model 
% Implementation of SIMPLE crop model from
% Zhao et al. (https://doi.org/10.1016/j.eja.2019.01.009)

% AUTHOR: Jabir Bin Jahangir (jabir@purdue.edu)

function [output] = core_simple(weather, crop, sowing_date, lightmap)

arguments 
    weather
    crop 
    sowing_date
    lightmap double = []
end 

fprintf('[3/3] Executing crop simulation...\n')

% Weather file (daily)
if isempty(lightmap)
    using_nasa = true; 
else
    disp("using lightmap. ")
    using_nasa = false; % Setting false will use the lightmap 
end

% load("./weather/weather_file.mat")     
% weather = weather_lafayette;

% load("weather_Philippines.mat")
% load("./lightmap/ACRE_gnd_lightmap.mat")   % Ground Lightmap from PVMAPS (EW tracking)

% load("./pv_configs/ACRE_config_p10_e6_gndlight.mat") 
% load("./pv_configs/ACRE_config_p5_e6_gndlight.mat")
% load("./pv_configs/ACRE_config_p3.6_e6_gndlight.mat") 
% load("./pv_configs/Urbana_config_p5.5_e1.5_gndlight.mat")

%% Crop and soil specification
% Soil params

soil.awc = 0.12; %
soil.rcn = 70;   %
soil.ddc = 0.3;  %
soil.rzd = 1500; % mm

% Load crops
% load('./crop_specs/maize_spec.mat')
% load('./crop_specs/maize_calib.mat')
crop_spec = crop;
crop_spec_init = crop_spec; 

% Management
% sowing_date = datetime(2024, 5, 15);
sowing_doy = day(sowing_date, "dayofyear");

f_solar_max = 0.95;  % Max F_solar, function of crop density 

%% Main iterations
npos = 1;         % Total ground segments
if ~using_nasa
    npos = size(lightmap, 2);
end 



for pos = 1:npos
    % Init vars
    tt_sum = 0;         % total thermal time
    ismature = 0;       % crop maturity flag
    mature_doy = 0;     % DOY of the crop maturity
    mature_date = NaT;
    biomass_total = 0;
    biomass_daily = []; 
    fsolar = [];
    tt_sum_vec = []; 
    crop_light = []; 
    temp_factor = []; 
    heat_factor = []; 
    water_factor = []; 
    co2_factor = [];

    crop_spec = crop_spec_init; 

    % Main iterations
    for i=sowing_doy:height(weather) * 2
        dss = i-sowing_doy;
        weather_index = mod(i - 1, height(weather)) + 1;
        t_daily = weather.T2M(weather_index);
        t_daily_max = weather.T2M_MAX(weather_index);

        % Accumulate heat
        if ismature == 0
            tt_sum = tt_sum + TT(crop_spec, t_daily);
            % tt_sum_day = tt_sum * (i - sowing_doy); % degree days
        end

        if tt_sum > crop_spec.Tsum & ismature == 0
            ismature = 1;
            mature_date = datetime(year(sowing_date), 1, 1) + days(i - 1);
            % disp(mature_doy);
        end

        fsolar(i) = Fsolar(crop_spec, tt_sum);

        % Radiation (Load the appropriate data)
        if using_nasa
            rad = weather.ALLSKY_SFC_SW_DWN(weather_index) * 0.5;
        else
            % rad = yearly_rad_gnd_all(i, pos) * 0.5;
            % rad = lightmap(i, pos) * 0.5;

            rad = lightmap(weather_index, pos) * 0.5;
        end

        tt_sum_vec(i) = tt_sum;
        crop_light(i) = fsolar(i) * rad * crop_spec.RUE;
        temp_factor(i) = Ftemp(crop_spec, t_daily);
        heat_factor(i) = FHeat(crop_spec, t_daily_max);
        water_factor(i) = 1;    % No water stress

        % Early senes. due to heat stress
        crop_spec.I50b = crop_spec.I50b  + crop_spec.I50max_H * (1 - heat_factor(i));
        
        % CO2 enhancement
        co2_factor(i)  = 1 + crop_spec.Sco2 *(424 - 350);

        if water_factor(i) < 0
            water_factor(i) = 0;
        end

        % Daily biomass rate and accumulated biomass
        biomass_daily(i) = crop_light(i) * temp_factor(i) ...
            * min(heat_factor(i), water_factor(i)) ...
            * co2_factor(i);
        biomass_total = sum(biomass_daily);

        if (ismature == 1)
            break
        end
    end

    yield = biomass_total * crop_spec.HI * 1e-3;  % Grain yield, harvest index=0.5, yield in kg/m2
    yield_thec = yield * 11.0231;                 % yield in ton/hec
    yield_thec_segments(pos) = yield_thec;       
end

fprintf('Crop simulation completed! \n')

output.biomass_daily = biomass_daily;  % Stored for the last segment
output.grain_yield_thec_mean = mean(yield_thec_segments); 
output.grain_yield_thec_segments = yield_thec_segments; 

biomass_total = cumsum(biomass_daily  * 1e-2);
output.biomass_aggregate = biomass_total; 

plant_days = [sowing_doy:sowing_doy + dss];

output.plant_days = plant_days;
output.mature_date = mature_date;
output.sowing_date = sowing_date; 



figure();
plot(biomass_daily)
ylabel('Biomass (g/m^2)');
xlabel('Day since sowing');

figure();
plot(plant_days - plant_days(1), biomass_total(plant_days), linewidth=2);
ylabel('Biomass accumulation (t/ha)')
xlabel('Days since sowing');

end 

%% Stress response functions
% Thermal time calculation
function  tt = TT(crop_spec, t_daily)
if t_daily > crop_spec.Tbase
    tt = t_daily - crop_spec.Tbase;
else
    tt  = 0;
end
end

% Solar utilization phenomenology
function fsolar = Fsolar(crop_spec, tt_sum)
f_solar_max = 0.95;

fsolar_growth = f_solar_max  / (1 + exp(-0.01 * (tt_sum - crop_spec.I50a))); % growth period
fsolar_death = f_solar_max  / (1 + exp(0.01 * (tt_sum - crop_spec.Tsum  + crop_spec.I50b))); % sence. period

fsolar = min(fsolar_growth, fsolar_death);
end


% Temperature model
function ftemp = Ftemp(crop_spec, t_daily)

if (t_daily< crop_spec.Tbase)
    ftemp = 0;
    return;
end

if t_daily > crop_spec.Tbase & t_daily < crop_spec.Topt
    ftemp = (t_daily - crop_spec.Tbase)  / (crop_spec.Topt - crop_spec.Tbase) ;
    return;
end

ftemp = 1;
return;
end

% Heat stress
function fheat = FHeat(crop_spec, t_daily_max)
Textreme = 46;

if (t_daily_max < crop_spec.Tmax)
    fheat = 1;
    return;
end

if t_daily_max >= crop_spec.Tmax & t_daily_max < Textreme
    fheat = 1  - (t_daily_max - crop_spec.Tmax) / (Textreme - crop_spec.Tmax);
    return;
end

fheat = 0;
return;
end

function fwater = Fwater(crop_spec, arid)
fwater = 1 - crop_spec.Swater * arid;
end
