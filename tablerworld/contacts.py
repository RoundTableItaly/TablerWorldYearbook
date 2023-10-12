import pandas as pd
import phonenumbers
import datetime
import math
from . import settings
from enum import Enum
import numpy as np


class PositionRank(Enum):
    ANY = None
    CLUB = "rt_global_positions_club"
    AREA = "rt_global_positions_area"
    NATIONAL = "rt_global_positions_national"


class Membership(Enum):
    IS_MEMBER = "is_member"
    IS_PAST_MEMBER = "is_past_member"
    IS_MEMBER_OVER_25 = "is_member_over_25"
    IS_MEMBER_UNDER_25 = "is_member_under_25"
    IS_HONORARY_MEMBER_IN_MEMORIAM_CLUB = "is_honorary_member_in_memoriam_club"
    IS_HONORARY_MEMBER_FOR_LIFE_CLUB = "is_honorary_member_for_life_club"
    IS_HONORARY_MEMBER_FOR_LIFE_NATIONAL = "is_honorary_member_for_life_national"
    IS_HONORARY_MEMBER_FOR_YEAR_CLUB = "is_honorary_member_for_year_club"
    IS_HONORARY_MEMBER_FOR_YEAR_NATIONAL = "is_honorary_member_for_year_national"
    IS_GREAT_FRIEND = "is_great_friend"
    HAS_MEMBERSHIP_ERRORS = "has_membership_errors"


def calculate_age(birth_date, reference_date):
    return reference_date.year - birth_date.year - ((reference_date.month, reference_date.day) < (birth_date.month, birth_date.day))


def clean(df, df_manual_contacts):
    print("Contacts clean STARTED")

    # Read settings
    config = settings.read()

    # Clean functions
    def clean_name(cell):
        return cell.strip().title()

    def clean_phonenumbers(cell):
        if not cell or not isinstance(cell, list):
            return None

        mobile = None
        home = None
        for item in cell:
            if item.get("type", None) == "home":
                home = item.get("value", None)
            if item.get("type", None) == "mobile":
                mobile = item.get("value", None)

        if mobile is not None:
            phone = mobile
        elif home is not None:
            phone = home
        else:
            phone = None

        phone = phone.encode("ascii", errors="ignore").decode()
        phone_parsed = phonenumbers.parse(phone, "IT")
        phone_international = phonenumbers.format_number(phone_parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        return phone_international

    def email(cell):
        if cell is None:
            return str()
        else:
            return str(cell).lower()

    def clean_address(cell):
        if not cell or not isinstance(cell, list):
            return None

        item = cell[0]

        street1 = item.get("street1")
        # street2 = item.get("street2")
        postal_code = item.get("postal_code")
        city = item.get("city")

        if not all((street1, postal_code, city)):
            return None

        street1 = str(street1).title()
        # street2 = str(street2).title()
        postal_code = str(postal_code).title()
        city = str(city).title()

        return f"{street1} - {postal_code} {city}"

    def clean_companies(cell):
        if not cell or not isinstance(cell, list):
            return None

        item = cell[0]
        sector = item.get("sector", None)
        function = item.get("function", None)

        return None if function is None else f"{function.strip()}"

    def name_partner(cell):
        if not cell or not isinstance(cell, list):
            return None

        member_info = [x for x in cell if x.get("name") == "Member Info"]
        if not member_info:
            return None

        name_partner = [x for x in member_info[0].get("rows") if x.get("key") == "Name partner"]
        return name_partner[0].get("value") if name_partner else None

    def profile_pic_file(df):
        if df["profile_pic"]:
            return f"rt{df['rt_club_number']:02}_{df['last_name'].replace(' ', '')}_{df['first_name'].replace(' ', '')}.jpg"
        else:
            return None

    def rt_positions_current(cell):
        if not cell or not isinstance(cell, list):
            return []

        def is_current(x):
            start_date = x.get("start_date")
            end_date = x.get("end_date")

            YEARBOOK_DATE = config.get("contacts").get("yearbook_date")
            yb_date_dt = datetime.datetime.strptime(YEARBOOK_DATE, "%Y-%m-%d").date()

            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()

            if end_date is None:
                end_date_dt = yb_date_dt + datetime.timedelta(days=1)
            else:
                end_date_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

            if start_date < yb_date_dt and end_date_dt > yb_date_dt:
                return True
            else:
                return False

        current_positions = [x for x in cell if is_current(x)]
        return current_positions

    def rt_global_positions(cell, args):
        if not cell or not isinstance(cell, list):
            return []

        res = []
        position_type = args

        for x in cell:
            short_description = x.get("combination").get("short_description")
            position = short_description.rsplit(sep=" › ")
            position_len = len(position)

            if position_type == PositionRank.NATIONAL and position_len != 3:
                continue
            if position_type == PositionRank.AREA and position_len != 5:
                continue
            if position_type == PositionRank.CLUB and position_len != 7:
                continue

            x["position"] = position[-1]
            res.append(x)

        return res

    def is_member(df):
        honorary_member = (
            is_honorary_member_in_memoriam_club(df)
            or is_honorary_member_for_life_club(df)
            or is_honorary_member_for_life_national(df)
            or is_honorary_member_for_year_club(df)
            or is_honorary_member_for_year_national(df)
        )
        if honorary_member:
            return False

        is_manual_contact = df["is_manual_contact"]
        if is_manual_contact:
            return False

        MEMBER = config.get("contacts").get("positions").get("club").get("member")
        is_member = False

        for pos in df["rt_global_positions_club"]:
            if MEMBER in pos.get("position"):
                is_member = True
                break

        return is_member

    def is_past_member(df):
        honorary_member = (
            is_honorary_member_in_memoriam_club(df)
            or is_honorary_member_for_life_club(df)
            or is_honorary_member_for_life_national(df)
            or is_honorary_member_for_year_club(df)
            or is_honorary_member_for_year_national(df)
        )
        if honorary_member:
            return False

        is_manual_contact = df["is_manual_contact"]
        if is_manual_contact:
            return False

        PAST_MEMBER = config.get("contacts").get("positions").get("club").get("past_member")
        is_past_member = False

        for pos in df["rt_global_positions_club"]:
            if PAST_MEMBER in pos.get("position"):
                is_past_member = True
                break

        return is_past_member

    def is_member_over_25(df):
        honorary_member = (
            is_honorary_member_in_memoriam_club(df)
            or is_honorary_member_for_life_club(df)
            or is_honorary_member_for_life_national(df)
            or is_honorary_member_for_year_club(df)
            or is_honorary_member_for_year_national(df)
        )
        if honorary_member:
            return False

        is_manual_contact = df["is_manual_contact"]
        if is_manual_contact:
            return False

        MEMBER = config.get("contacts").get("positions").get("club").get("member")
        AGE_DATE = config.get("contacts").get("age_date")
        age_date_dt = datetime.datetime.strptime(AGE_DATE, "%Y-%m-%d").date()

        is_member = False
        for pos in df["rt_global_positions_club"]:
            if MEMBER in pos.get("position"):
                is_member = True
                break

        birth_date = df["birth_date"]

        if pd.isna(birth_date) and is_member:
            return True

        age = calculate_age(birth_date.date(), age_date_dt)
        over_25 = age >= 25

        return is_member and over_25

    def is_member_under_25(df):
        honorary_member = (
            is_honorary_member_in_memoriam_club(df)
            or is_honorary_member_for_life_club(df)
            or is_honorary_member_for_life_national(df)
            or is_honorary_member_for_year_club(df)
            or is_honorary_member_for_year_national(df)
        )
        if honorary_member:
            return False

        is_manual_contact = df["is_manual_contact"]
        if is_manual_contact:
            return False

        MEMBER = config.get("contacts").get("positions").get("club").get("member")
        AGE_DATE = config.get("contacts").get("age_date")
        age_date_dt = datetime.datetime.strptime(AGE_DATE, "%Y-%m-%d").date()

        is_member = False
        for pos in df["rt_global_positions_club"]:
            if MEMBER in pos.get("position"):
                is_member = True
                break

        birth_date = df["birth_date"]

        if pd.isna(birth_date):
            return False

        age = calculate_age(birth_date.date(), age_date_dt)
        under_25 = age < 25

        return is_member and under_25

    def is_honorary_member_in_memoriam_club(df):
        is_manual_contact = df["is_manual_contact"]
        if is_manual_contact:
            return False

        HONORARY_MEMBER = config.get("contacts").get("positions").get("club").get("honorary_member")
        is_honorary_member_in_memoriam_club = False

        for pos in df["rt_global_positions_club"]:
            if HONORARY_MEMBER in pos.get("position") and pd.isna(pos.get("end_date")) and df["is_deceased"]:
                is_honorary_member_in_memoriam_club = True
                break

        return is_honorary_member_in_memoriam_club

    def is_honorary_member_for_life_club(df):
        is_manual_contact = df["is_manual_contact"]
        if is_manual_contact:
            return df["is_honorary_member_for_life_club"]

        HONORARY_MEMBER = config.get("contacts").get("positions").get("club").get("honorary_member")
        is_honorary_member_for_life_club = False

        for pos in df["rt_global_positions_club"]:
            if HONORARY_MEMBER in pos.get("position") and pd.isna(pos.get("end_date")) and not df["is_deceased"]:
                is_honorary_member_for_life_club = True
                break

        return is_honorary_member_for_life_club

    def is_honorary_member_for_life_national(df):
        HONORARY_MEMBER = config.get("contacts").get("positions").get("national").get("honorary_member")
        is_honorary_member_for_life_national = False

        for pos in df["rt_global_positions_national"]:
            if HONORARY_MEMBER in pos.get("position") and pd.isna(pos.get("end_date")) and not df["is_deceased"]:
                is_honorary_member_for_life_national = True
                break

        return is_honorary_member_for_life_national

    def is_honorary_member_for_year_club(df):
        is_manual_contact = df["is_manual_contact"]
        if is_manual_contact:
            return False

        HONORARY_MEMBER = config.get("contacts").get("positions").get("club").get("honorary_member")
        is_honorary_member_for_year_club = False

        for pos in df["rt_global_positions_club"]:
            if HONORARY_MEMBER in pos.get("position") and not pd.isna(pos.get("end_date")) and not df["is_deceased"]:
                is_honorary_member_for_year_club = True
                break

        return is_honorary_member_for_year_club

    def is_honorary_member_for_year_national(df):
        HONORARY_MEMBER = config.get("contacts").get("positions").get("national").get("honorary_member")
        is_honorary_member_for_year_national = False

        for pos in df["rt_global_positions_national"]:
            if HONORARY_MEMBER in pos.get("position") and not pd.isna(pos.get("end_date")) and not df["is_deceased"]:
                is_honorary_member_for_year_national = True
                break

        return is_honorary_member_for_year_national

    def has_membership_errors(df):
        age = df["is_member_over_25"] and df["is_member_under_25"]
        double_status_club = (
            0
            + df["is_honorary_member_in_memoriam_club"]
            + df["is_honorary_member_for_life_club"]
            + df["is_honorary_member_for_year_club"]
            + df["is_honorary_member_for_year_national"]
        ) > 1

        member_and_past_member = df["is_member"] and df["is_past_member"]
        member_status = (not df["is_member"]) and (df["is_member_over_25"] or df["is_member_under_25"])

        return member_and_past_member or age or double_status_club and member_status

    # Merge manual contacts
    df_manual_contacts = pd.merge(
        df_manual_contacts,
        df[
            [
                "uname",
                "birth_date",
                "email",
                "phonenumbers",
                "profile_pic",
                "rt_global_positions",
                "rt_local_positions",
                "address",
                "companies",
                "custom_fields",
            ]
        ],
        how="left",
        on="uname",
    )
    df_manual_contacts = pd.merge(
        df_manual_contacts,
        df[["rt_club_number", "rt_club_name", "rt_club_subdomain", "rt_area_name", "rt_area_subdomain"]].drop_duplicates(),
        how="left",
        on="rt_club_number",
    )
    df = pd.concat([df, df_manual_contacts])
    df.reset_index(inplace=True, drop=True)

    # Replace nan values
    df.fillna({"is_great_friend": False}, inplace=True)
    df = df.replace({np.nan: None})

    # Clean dirty rows
    df.drop(df[df["rt_club_number"].isnull()].index, inplace=True)
    for club in config.get("contacts").get("remove").get("rt_club_number"):
        df.drop(df[df["rt_club_number"] == club].index, inplace=True)

    # Remove contacts with no positions - MANUAL CONTACT DO NOT HAVE POSITIONS
    # df = df[~df["rt_global_positions"].str.len().eq(0)].copy()

    # Remove contacts in status expelled, resigned
    for status in config.get("contacts").get("remove").get("rt_status"):
        df.drop(df[df["rt_status"] == status].index, inplace=True)

    # Convert types
    df["is_great_friend"] = df["is_great_friend"].astype("bool")
    df["is_manual_contact"] = df["is_manual_contact"].astype("bool")
    df["rt_club_number"] = df["rt_club_number"].astype("int")
    df["birth_date"] = pd.to_datetime(df["birth_date"])
    df["last_modified"] = pd.to_datetime(df["last_modified"]).dt.tz_localize(None)
    df["created_on"] = pd.to_datetime(df["created_on"]).dt.tz_localize(None)
    df["last_sync"] = pd.to_datetime(df["last_sync"]).dt.tz_localize(None)

    # Recently modified contacts flag
    df["recently_modified"] = df["last_modified"] > config.get("contacts").get("recently_modified_contacts_from")

    # Create utility columns
    df["profile_pic_file"] = df.apply(profile_pic_file, axis=1)

    # Apply
    df["first_name"] = df["first_name"].apply(clean_name)
    df["last_name"] = df["last_name"].apply(clean_name)
    df["phonenumbers"] = df["phonenumbers"].apply(clean_phonenumbers)
    df["email"] = df["email"].apply(email)
    df["address"] = df["address"].apply(clean_address)
    df["job"] = df["companies"].apply(clean_companies)
    df["name_partner"] = df["custom_fields"].apply(name_partner)

    df["rt_local_positions"] = df["rt_local_positions"].apply(rt_positions_current)
    df["rt_global_positions"] = df["rt_global_positions"].apply(rt_positions_current)
    df["rt_global_positions_national"] = df["rt_global_positions"].apply(rt_global_positions, args=(PositionRank.NATIONAL,))
    df["rt_global_positions_area"] = df["rt_global_positions"].apply(rt_global_positions, args=(PositionRank.AREA,))
    df["rt_global_positions_club"] = df["rt_global_positions"].apply(rt_global_positions, args=(PositionRank.CLUB,))

    df["is_member"] = df.apply(is_member, axis=1)
    df["is_past_member"] = df.apply(is_past_member, axis=1)
    df["is_member_over_25"] = df.apply(is_member_over_25, axis=1)
    df["is_member_under_25"] = df.apply(is_member_under_25, axis=1)
    df["is_honorary_member_in_memoriam_club"] = df.apply(is_honorary_member_in_memoriam_club, axis=1)
    df["is_honorary_member_for_life_club"] = df.apply(is_honorary_member_for_life_club, axis=1)
    df["is_honorary_member_for_life_national"] = df.apply(is_honorary_member_for_life_national, axis=1)
    df["is_honorary_member_for_year_club"] = df.apply(is_honorary_member_for_year_club, axis=1)
    df["is_honorary_member_for_year_national"] = df.apply(is_honorary_member_for_year_national, axis=1)
    df["has_membership_errors"] = df.apply(has_membership_errors, axis=1)

    # Reorder columns
    df["is_honorary_member_for_life_club"] = df.pop("is_honorary_member_for_life_club")
    df["is_great_friend"] = df.pop("is_great_friend")
    df["is_manual_contact"] = df.pop("is_manual_contact")
    df["has_membership_errors"] = df.pop("has_membership_errors")

    print("Contacts clean ENDED")
    return df
