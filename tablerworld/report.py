import os
from jinja2 import Environment, PackageLoader, select_autoescape
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import pandas as pd

MODULE_PATH = os.path.dirname(__file__)
TEMPLATE_HTML = os.path.join(MODULE_PATH, "templates/report/report.html")
TEMPLATE_CSS = os.path.join(MODULE_PATH, "templates/report/report.css")

OUTPUT_PDF = "dist/report.pdf"
OUTPUT_HTML = "dist/report.html"


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

    # Jinja
    env = Environment(
        loader=PackageLoader("tablerworld"),
        autoescape=select_autoescape(),
    )

    # HTML
    template = env.get_template("report/report.html")
    template_rendered = template.render(pd=pd, df=df, areas=areas, clubs=clubs)
    # HTML write to file
    with open(OUTPUT_HTML, "wb") as f:
        f.write(template_rendered.encode("utf-8"))

    # Weasy print
    html = HTML(string=template_rendered)
    font_config = FontConfiguration()
    css = CSS(filename=TEMPLATE_CSS, font_config=font_config)

    html.write_pdf(OUTPUT_PDF, stylesheets=[css], font_config=font_config)
