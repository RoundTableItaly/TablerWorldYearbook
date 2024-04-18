import logging
from pathlib import Path, PurePath
from jinja2 import Environment, PackageLoader, select_autoescape
import weasyprint
import pandas as pd

from .contacts import Membership, PositionRank

logger = logging.getLogger("TablerWordYearbook")

MODULE_PATH = Path(__file__).parent
TEMPLATE_DIR = PurePath.joinpath(MODULE_PATH, "templates", "report")
TEMPLATE_CSS = PurePath.joinpath(TEMPLATE_DIR, "report.css")

OUTPUT_FOLDER = PurePath.joinpath(Path(MODULE_PATH).parent, "output")
OUTPUT_PDF = PurePath.joinpath(OUTPUT_FOLDER, "report.pdf")
OUTPUT_HTML = PurePath.joinpath(OUTPUT_FOLDER, "report.html")


def report(df):
    logger.info("Report generation STARTED")

    areas = (
        df[["rt_area_name", "rt_area_subdomain"]]
        .drop_duplicates(ignore_index=True)
        .sort_values(by="rt_area_name")
        .to_dict(orient="records")
    )
    clubs = (
        df[["rt_club_name", "rt_club_subdomain", "rt_club_number", "rt_area_name", "rt_area_subdomain"]]
        .drop_duplicates(ignore_index=True)
        .sort_values(by="rt_club_number")
        .to_dict(orient="records")
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
        .to_dict(orient="records")
    )

    def is_position_present_in_list(cell, args):
        position = args
        is_present = False

        for x in cell:
            if position in x.get("position"):
                is_present = True

        return is_present

    def get_tablers_club_pos(club_number, position, is_deceased=False, hmfl=False, hmfy=False):
        tablers = df.loc[
            (df["rt_club_number"] == club_number)
            & (
                df["rt_global_positions_club"].apply(is_position_present_in_list, args=(position,))
                & (df["is_deceased"] == is_deceased)
                & (df["is_honorary_member_for_life_club"] == hmfl)
                & (df["is_honorary_member_for_year_club"] == hmfy)
            )
        ]

        return tablers.sort_values(by=["last_name", "first_name"]).to_dict(orient="records")

    def get_tabler_area_pos(area_name, position):
        tablers = df.loc[
            (df["rt_area_name"] == area_name) & (df["rt_global_positions_area"].apply(is_position_present_in_list, args=(position,)))
        ]
        t = tablers.head(1).to_dict(orient="records")

        return t[0] if len(t) > 0 else None

    def get_tabler_national_pos(position):
        tablers = df.loc[df["rt_global_positions_national"].apply(is_position_present_in_list, args=(position,))]
        t = tablers.head(1).to_dict(orient="records")

        return t[0] if len(t) > 0 else None

    def get_tablers(positionrank, value, membership):
        match positionrank:
            case PositionRank.CLUB:
                tablers = df.loc[df["rt_club_number"] == value]
            case PositionRank.AREA:
                tablers = df.loc[df["rt_area_name"] == value]
            case PositionRank.ANY:
                tablers = df
            case _:  # wildcard - simile ad un else, deve stare alla fine
                logger.info("Unknown error")

        tablers = tablers.loc[df[membership.value] == True].reset_index()

        return tablers.sort_values(by=["last_name", "first_name"]).to_dict(orient="records")

    # Jinja
    env = Environment(
        loader=PackageLoader("tablerworld"),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["TEMPLATE_DIR"] = TEMPLATE_DIR.as_uri()
    env.globals["OUTPUT_FOLDER"] = OUTPUT_FOLDER.as_uri()

    # HTML
    template = env.get_template("report/report.html")
    template_rendered = template.render(
        Membership=Membership,
        PositionRank=PositionRank,
        pd=pd,
        df=df,
        areas=areas,
        clubs=clubs,
        clubs_in_areas=clubs_in_areas,
        get_tablers_club_pos=get_tablers_club_pos,
        get_tabler_area_pos=get_tabler_area_pos,
        get_tabler_national_pos=get_tabler_national_pos,
        get_tablers=get_tablers,
    )
    # HTML write to file
    with open(OUTPUT_HTML, "wb") as f:
        f.write(template_rendered.encode("utf-8"))

    # Weasyprint
    weasyprint.DEFAULT_OPTIONS["dpi"] = 200
    weasyprint.DEFAULT_OPTIONS["presentational_hints"] = True

    html = weasyprint.HTML(string=template_rendered, base_url=str(TEMPLATE_DIR))
    font_config = weasyprint.text.fonts.FontConfiguration()
    css = weasyprint.CSS(filename=TEMPLATE_CSS, font_config=font_config)

    html.write_pdf(OUTPUT_PDF, stylesheets=[css], font_config=font_config)

    logger.info("Report generation ENDED")
