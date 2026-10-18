"""Conceptual array-geometry diagrams built from submitted PVMAPS inputs."""

import math

from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle


CONFIGURATION_TITLES = {
    "fixed": "Fixed-tilt array",
    "tracking": "Tracking array",
    "GSVBF": "Ground-sculpted vertical bifacial array",
}


def configuration_caption(array):
    config = array.get("config")
    pitch = array.get("pitch")
    elevation = array.get("elevation")
    azimuth = array.get("azimuth")
    albedo = array.get("albedo")
    parts = [CONFIGURATION_TITLES.get(config, str(config or "Unknown configuration"))]
    if pitch is not None:
        parts.append(f"{pitch:g} m pitch")
    if elevation is not None:
        parts.append(f"{elevation:g} m center elevation")
    if config == "fixed" and array.get("tilt") is not None:
        parts.append(f"{array['tilt']:g} degree tilt")
    if azimuth is not None:
        parts.append(f"{azimuth:g} degree azimuth")
    if albedo is not None:
        parts.append(f"{albedo:g} ground albedo")
    return " | ".join(parts)


def _panel_segment(center_x, center_y, length, angle_degrees):
    angle = math.radians(angle_degrees)
    dx = length * math.cos(angle) / 2
    dy = length * math.sin(angle) / 2
    return (center_x - dx, center_x + dx), (center_y - dy, center_y + dy)


def _azimuth_vector(azimuth_degrees):
    """Return an east/north vector for azimuth measured clockwise from north."""
    angle = math.radians(azimuth_degrees)
    return math.sin(angle), math.cos(angle)


def _draw_orientation_compass(ax, azimuth, panel_color, accent_color, muted_color):
    from matplotlib.patches import Circle

    ax.add_patch(Circle((0, 0), 1, fill=False, color=muted_color, linewidth=1.2))
    for label, x, y in (("N", 0, 1.2), ("E", 1.2, 0),
                        ("S", 0, -1.2), ("W", -1.2, 0)):
        ax.text(x, y, label, ha="center", va="center", color=muted_color,
                fontsize=8, fontweight="semibold")

    if isinstance(azimuth, (int, float)):
        dx, dy = _azimuth_vector(float(azimuth))
        ax.add_patch(FancyArrowPatch(
            (0, 0), (0.82 * dx, 0.82 * dy), arrowstyle="-|>",
            mutation_scale=14, color=accent_color, linewidth=2.2,
        ))
        ax.text(0, -1.55, f"Azimuth: {azimuth:g} degrees", ha="center",
                va="top", color=panel_color, fontsize=8)
    else:
        ax.text(0, -1.55, "Azimuth not recorded", ha="center", va="top",
                color=muted_color, fontsize=8)

    ax.set_xlim(-1.65, 1.65)
    ax.set_ylim(-1.75, 1.45)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Array orientation", fontsize=9, fontweight="semibold", pad=7)


def _draw_albedo_gauge(ax, albedo, accent_color, muted_color):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("Ground reflectivity", fontsize=9, fontweight="semibold", pad=4)

    bar_x, bar_y, bar_width, bar_height = 0.08, 0.55, 0.84, 0.16
    ax.add_patch(Rectangle(
        (bar_x, bar_y), bar_width, bar_height,
        facecolor="#e4e8ea", edgecolor="none",
    ))

    if isinstance(albedo, (int, float)):
        fraction = min(max(float(albedo), 0), 1)
        ax.add_patch(Rectangle(
            (bar_x, bar_y), bar_width * fraction, bar_height,
            facecolor=accent_color, edgecolor="none",
        ))
        marker_x = bar_x + bar_width * fraction
        ax.plot([marker_x, marker_x], [bar_y - 0.04, bar_y + bar_height + 0.04],
                color=accent_color, linewidth=1.5)
        ax.text(0.5, 0.34, f"Albedo {albedo:g}", ha="center", va="center",
                color="#1f5d75", fontsize=8, fontweight="semibold")
        ax.text(0.5, 0.13, f"{fraction * 100:g}% of incident light reflected",
                ha="center", va="center", color=muted_color, fontsize=7)
    else:
        ax.text(0.5, 0.28, "Albedo not recorded", ha="center", va="center",
                color=muted_color, fontsize=8)


def create_array_configuration_figure(pvmaps_input):
    """Return conceptual geometry, orientation, and albedo visualizations."""
    import matplotlib.pyplot as plt

    array = (pvmaps_input or {}).get("array") or {}
    module = (pvmaps_input or {}).get("module") or {}
    config = array.get("config", "fixed")
    tilt = float(array.get("tilt") or 0)
    pitch = array.get("pitch")
    elevation = array.get("elevation")
    module_height = module.get("height")
    gs_height = array.get("gsHeight")
    azimuth = array.get("azimuth")
    albedo = array.get("albedo")

    fig = plt.figure(figsize=(10.5, 3.1), layout="constrained")
    grid = fig.add_gridspec(
        2, 2, width_ratios=[4.8, 1.25], height_ratios=[2.2, 1]
    )
    ax = fig.add_subplot(grid[:, 0])
    compass_ax = fig.add_subplot(grid[0, 1])
    albedo_ax = fig.add_subplot(grid[1, 1])
    ground_color = "#50845c"
    panel_color = "#1f5d75"
    accent_color = "#d49b2a"
    muted_color = "#7a848c"
    centers = (2.4, 6.4)
    center_y = 2.1
    panel_length = 2.25

    ax.plot([0.3, 8.5], [0, 0], color=ground_color, linewidth=3)

    if config == "GSVBF":
        mound_height = 0.65
        if isinstance(gs_height, (int, float)) and gs_height > 0:
            mound_height = min(1.0, 0.45 + gs_height * 0.15)
        ax.add_patch(Polygon(
            [(centers[0], 0), (4.4, mound_height), (centers[1], 0)],
            closed=True,
            facecolor="#d8c58a",
            edgecolor=ground_color,
            linewidth=1.5,
        ))
        angles = (90, 90)
    elif config == "tracking":
        angles = (20, 20)
    else:
        angles = (tilt, tilt)

    for center_x, angle in zip(centers, angles):
        xs, ys = _panel_segment(center_x, center_y, panel_length, angle)
        ax.plot(xs, ys, color=panel_color, linewidth=8, solid_capstyle="round")
        ax.plot([center_x, center_x], [0, center_y], color=muted_color, linewidth=2)
        ax.scatter([center_x], [center_y], color=accent_color, s=26, zorder=4)
        if config == "tracking":
            for ghost_angle in (-45, 45):
                ghost_xs, ghost_ys = _panel_segment(
                    center_x, center_y, panel_length, ghost_angle
                )
                ax.plot(ghost_xs, ghost_ys, color=panel_color, alpha=0.16,
                        linewidth=5, solid_capstyle="round")

    pitch_arrow = FancyArrowPatch(
        (centers[0], 0.35), (centers[1], 0.35), arrowstyle="<->",
        mutation_scale=12, color=accent_color, linewidth=1.6,
    )
    ax.add_patch(pitch_arrow)
    ax.text(sum(centers) / 2, 0.48,
            f"Pitch: {pitch:g} m" if isinstance(pitch, (int, float)) else "Pitch",
            ha="center", va="bottom", color=accent_color, fontsize=9)

    elevation_arrow = FancyArrowPatch(
        (0.85, 0), (0.85, center_y), arrowstyle="<->",
        mutation_scale=12, color=muted_color, linewidth=1.4,
    )
    ax.add_patch(elevation_arrow)
    elevation_label = (
        f"Center elevation\n{elevation:g} m"
        if isinstance(elevation, (int, float)) else "Center elevation"
    )
    ax.text(0.7, center_y / 2, elevation_label, ha="right", va="center",
            color=muted_color, fontsize=8)

    if config == "fixed":
        ax.text(centers[0], 3.35, f"Fixed tilt: {tilt:g} degrees",
                ha="center", color=panel_color, fontsize=9)
    elif config == "tracking":
        ax.text(centers[0], 3.35, "Panel angle changes during operation",
                ha="center", color=panel_color, fontsize=9)
    elif config == "GSVBF":
        sculpture_label = (
            f"Ground sculpture: {gs_height:g} m"
            if isinstance(gs_height, (int, float)) else "Ground sculpture"
        )
        ax.text(4.4, max(1.0, mound_height + 0.3), sculpture_label, ha="center",
                va="bottom", color=ground_color, fontsize=9)

    if isinstance(module_height, (int, float)):
        ax.text(7.85, center_y, f"Module height\n{module_height:g} m",
                ha="left", va="center", color=panel_color, fontsize=8)

    ax.set_xlim(0, 9)
    ax.set_ylim(-0.25, 3.75)
    ax.axis("off")
    ax.set_title(CONFIGURATION_TITLES.get(config, "Array configuration"),
                 loc="left", fontsize=12, fontweight="semibold")
    ax.text(8.85, -0.12, "Two adjacent rows shown to illustrate pitch",
            ha="right", va="top", color=muted_color, fontsize=8)
    _draw_orientation_compass(
        compass_ax, azimuth, panel_color, accent_color, muted_color
    )
    _draw_albedo_gauge(albedo_ax, albedo, accent_color, muted_color)
    return fig
