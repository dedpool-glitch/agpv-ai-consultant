"""One analysis workbook containing the saved runs and ordered daily yield."""

from io import BytesIO

from services.simulation_csv import daily_yield_rows, run_summary_rows


def build_simulation_workbook(runs):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    workbook = Workbook()
    for sheet, (headers, rows) in (
        (workbook.active, run_summary_rows(runs)),
        (workbook.create_sheet("Daily yield"), daily_yield_rows(runs)),
    ):
        sheet.title = "Runs" if sheet is workbook.active else "Daily yield"
        sheet.append(headers)
        for row in rows:
            sheet.append([row.get(header) for header in headers])
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        sheet.row_dimensions[1].height = 31
        for cell in sheet[1]:
            cell.fill = PatternFill("solid", fgColor="23685A")
            cell.font = Font(name="Aptos", size=11, bold=True, color="FFFFFF")
            cell.alignment = Alignment(vertical="center", wrap_text=True)
        for column_index, header in enumerate(headers, start=1):
            sheet.column_dimensions[get_column_letter(column_index)].width = (
                18 if header.endswith("_unit") or header.endswith("_origin")
                else min(max(len(header) + 3, 15), 38)
            )

    crop_runs = [(index, run["crop_result"]) for index, run in enumerate(runs, start=1)
                 if run.get("crop_result")]
    if crop_runs:
        sheet = workbook.create_sheet("Crop yield")
        sheet.append(["run_id", "crop", "sowing_date", "maturity_date",
                      "mean_grain_yield_t_ha", "open_sky_grain_yield_t_ha",
                      "difference_from_open_sky_t_ha", "difference_from_open_sky_percent",
                      "ground_position_index", "grain_yield_t_ha"])
        for run_id, crop in crop_runs:
            for position, value in enumerate(crop["grain_yield_t_ha_by_position"]):
                sheet.append([run_id, crop["crop"], crop["sowing_date"],
                              crop["maturity_date"], crop["mean_grain_yield_t_ha"],
                              crop.get("open_sky_grain_yield_t_ha"),
                              crop.get("difference_from_open_sky_t_ha"),
                              crop.get("difference_from_open_sky_percent"),
                              position, value])
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        for cell in sheet[1]:
            cell.fill = PatternFill("solid", fgColor="23685A")
            cell.font = Font(name="Aptos", size=11, bold=True, color="FFFFFF")
        for column in sheet.columns:
            sheet.column_dimensions[column[0].column_letter].width = min(
                max(len(str(column[0].value)) + 3, 17), 28
            )

    stream = BytesIO()
    workbook.save(stream)
    return stream.getvalue()
