import os
from pathlib import Path
from jinja2 import Environment, PackageLoader, select_autoescape
import weasyprint
import pandas as pd


MODULE_PATH = os.path.dirname(__file__)
TEMPLATE_CSS = os.path.join(MODULE_PATH, "templates", "report", "report.css")

OUTPUT_PDF = os.path.join(Path(MODULE_PATH).parent, "dist", "report.pdf")
OUTPUT_HTML = os.path.join(Path(MODULE_PATH).parent, "dist", "report.html")


def report(df):
    areas = (
        df[["rt_area_name", "rt_area_subdomain"]]
        .drop_duplicates(ignore_index=True)
        .sort_values(by="rt_area_name")
        .copy()
    )
    clubs = (
        df[["rt_club_name", "rt_club_subdomain", "rt_club_number"]]
        .drop_duplicates(ignore_index=True)
        .sort_values(by="rt_club_number")
        .copy()
    )

    def fun_clubs(x):
        d = {}
        d["clubs"] = x[["rt_club_name", "rt_club_subdomain", "rt_club_number"]].to_dict(orient="records")
        return pd.Series(d, index=["clubs"])

    clubs_in_areas = (
        df[["rt_area_name", "rt_area_subdomain", "rt_club_name", "rt_club_subdomain", "rt_club_number"]]
        .drop_duplicates(ignore_index=True)
        .groupby(["rt_area_name", "rt_area_subdomain"])
        .apply(fun_clubs)
        .reset_index()
    )

    # Jinja
    env = Environment(
        loader=PackageLoader("tablerworld"),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # HTML
    template = env.get_template("report/report.html")
    template_rendered = template.render(pd=pd, df=df, areas=areas, clubs=clubs, clubs_in_areas=clubs_in_areas)
    # HTML write to file
    with open(OUTPUT_HTML, "wb") as f:
        f.write(template_rendered.encode("utf-8"))

    # Weasy print
    weasyprint.DEFAULT_OPTIONS["dpi"] = 200
    weasyprint.DEFAULT_OPTIONS["presentational_hints"] = True

    base_url = Path(OUTPUT_HTML).parent
    html = weasyprint.HTML(filename=OUTPUT_HTML, base_url=str(base_url))
    font_config = weasyprint.text.fonts.FontConfiguration()
    css = weasyprint.CSS(filename=TEMPLATE_CSS, font_config=font_config)

    html.write_pdf(OUTPUT_PDF, stylesheets=[css], font_config=font_config)
