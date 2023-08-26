from pathlib import Path, PurePath
from jinja2 import Environment, PackageLoader, select_autoescape
import weasyprint
import pandas as pd


MODULE_PATH = Path(__file__).parent
TEMPLATE_DIR = PurePath.joinpath(MODULE_PATH, "templates", "report")
TEMPLATE_CSS = PurePath.joinpath(TEMPLATE_DIR, "report.css")

DIST_FOLDER = PurePath.joinpath(Path(MODULE_PATH).parent, "dist")
OUTPUT_PDF = PurePath.joinpath(DIST_FOLDER, "report.pdf")
OUTPUT_HTML = PurePath.joinpath(DIST_FOLDER, "report.html")


def report(df):
    print("Report generation STARTED")

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

    def get_tablers_club_pos(club_number, position):
        tablers = df.loc[
            (df["rt_club_number"] == club_number) & (df["rt_global_positions_club"].apply(lambda x: position in x))
        ]
        return tablers.sort_values(by="last_name").to_dict(orient="records")

    def get_tabler_area_pos(area_name, position):
        tablers = df.loc[
            (df["rt_area_name"] == area_name) & (df["rt_global_positions_area"].apply(lambda x: position in x))
        ]
        t = tablers.head(1).to_dict(orient="records")

        return t[0] if len(t) > 0 else None

    # Jinja

    env = Environment(
        loader=PackageLoader("tablerworld"),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["TEMPLATE_DIR"] = TEMPLATE_DIR.as_uri()
    env.globals["DIST_FOLDER"] = DIST_FOLDER.as_uri()

    # HTML
    template = env.get_template("report/report.html")
    template_rendered = template.render(
        pd=pd,
        df=df,
        areas=areas,
        clubs=clubs,
        clubs_in_areas=clubs_in_areas,
        get_tablers_club_pos=get_tablers_club_pos,
        get_tabler_area_pos=get_tabler_area_pos,
    )
    # HTML write to file
    with open(OUTPUT_HTML, "wb") as f:
        f.write(template_rendered.encode("utf-8"))

    # Weasy print
    weasyprint.DEFAULT_OPTIONS["dpi"] = 200
    weasyprint.DEFAULT_OPTIONS["presentational_hints"] = True

    html = weasyprint.HTML(string=template_rendered, base_url=str(TEMPLATE_DIR))
    font_config = weasyprint.text.fonts.FontConfiguration()
    css = weasyprint.CSS(filename=TEMPLATE_CSS, font_config=font_config)

    html.write_pdf(OUTPUT_PDF, stylesheets=[css], font_config=font_config)

    print("Report generation ENDED")