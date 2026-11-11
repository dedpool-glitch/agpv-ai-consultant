from ui.crop_visualization import crop_visualization_data


def test_ground_light_and_crop_profiles_share_position_indices():
    light_day = [10.0] * 101
    light_day[17] = 3.0
    yields = [15.0] * 101
    yields[17] = 8.0
    data = crop_visualization_data({
        "output": {"ground_light": {"light_mj_m2": [light_day, light_day]}},
        "crop_result": {"grain_yield_t_ha_by_position": yields},
    })
    assert data["annual_light"][17] == 6.0
    assert data["lowest_light_index"] == 17
    assert data["lowest_yield_index"] == 17


def test_missing_ground_light_keeps_crop_curve_available():
    data = crop_visualization_data({
        "output": {},
        "crop_result": {"grain_yield_t_ha_by_position": [12.0] * 101},
    })
    assert data["annual_light"] is None
    assert len(data["yields"]) == 101
