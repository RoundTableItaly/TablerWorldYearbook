import pandas as pd
import phonenumbers
from datetime import datetime
from . import settings
from enum import Enum


class PositionRank(Enum):
    NATIONAL = 1
    AREA = 2
    CLUB = 3


def calculate_age(birth_date, reference_date):
    return reference_date.year - birth_date.year - ((reference_date.month, reference_date.day) < (birth_date.month, birth_date.day))


def clean(df):
    print("Contacts clean STARTED")

    # Read settings
    config = settings.read()

    # Clean functions
    def clean_name(cell):
        return cell.title()

    def clean_phonenumbers(cell):
        if not cell:
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
            return None
        else:
            return str(cell).lower()

    def clean_address(cell):
        if not cell:
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
        if not cell:
            return None

        item = cell[0]
        sector = item.get("sector", None)
        function = item.get("function", None)

        if function is None:
            return None
        else:
            return f"{function.capitalize()}"

    def name_partner(cell):
        if not cell:
            return None

        member_info = [x for x in cell if x.get("name") == "Member Info"]
        if not member_info:
            return None

        name_partner = [x for x in member_info[0].get("rows") if x.get("key") == "Name partner"]
        if not name_partner:
            return None

        return name_partner[0].get("value")

    def profile_pic_file(df):
        return f"rt{df['rt_club_number']:02}_{df['last_name'].replace(' ', '')}_{df['first_name'].replace(' ', '')}.jpg"

    def rt_positions_current(cell):
        def is_current(x):
            end_date = x.get("end_date")
            if end_date is None:
                return True

            YEARBOOK_DATE = config.get("contacts").get("yearbook_date")
            end_date_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            cur_date_dt = datetime.strptime(YEARBOOK_DATE, "%Y-%m-%d").date()
            if end_date_dt > cur_date_dt:
                return True
            else:
                return False

        current_positions = [x for x in cell if is_current(x)]
        return current_positions

    def rt_global_positions(cell, args):
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

    def is_member(cell):
        MEMBER = config.get("contacts").get("positions").get("club").get("member")
        is_member = False

        for pos in cell:
            if MEMBER in pos.get("position"):
                is_member = True
                break

        return is_member

    def is_past_member(cell):
        PAST_MEMBER = config.get("contacts").get("positions").get("club").get("past_member")
        is_past_member = False

        for pos in cell:
            if PAST_MEMBER in pos.get("position"):
                is_past_member = True
                break

        return is_past_member

    def is_member_over_25(df):
        MEMBER = config.get("contacts").get("positions").get("club").get("member")
        YEARBOOK_DATE = config.get("contacts").get("yearbook_date")
        yearbook_date_dt = datetime.strptime(YEARBOOK_DATE, "%Y-%m-%d").date()

        is_member = False
        for pos in df["rt_global_positions_club"]:
            if MEMBER in pos.get("position"):
                is_member = True
                break

        birth_date = df["birth_date"]

        if pd.isna(birth_date):
            return None

        age = calculate_age(birth_date.date(), yearbook_date_dt)
        over_25 = age >= 25

        return is_member and over_25

    def is_member_under_25(df):
        MEMBER = config.get("contacts").get("positions").get("club").get("member")
        YEARBOOK_DATE = config.get("contacts").get("yearbook_date")
        yearbook_date_dt = datetime.strptime(YEARBOOK_DATE, "%Y-%m-%d").date()

        is_member = False
        for pos in df["rt_global_positions_club"]:
            if MEMBER in pos.get("position"):
                is_member = True
                break

        birth_date = df["birth_date"]

        if pd.isna(birth_date):
            return None

        age = calculate_age(birth_date.date(), yearbook_date_dt)
        under_25 = age < 25

        return is_member and under_25

    def is_honorary_member_for_life_club(cell):
        HONORARY_MEMBER = config.get("contacts").get("positions").get("club").get("honorary_member")
        is_honorary_member_for_life_club = False

        for pos in cell:
            if HONORARY_MEMBER in pos.get("position") and pd.isna(pos.get("end_date")):
                is_honorary_member_for_life_club = True
                break

        return is_honorary_member_for_life_club

    def is_honorary_member_for_life_national(cell):
        HONORARY_MEMBER = config.get("contacts").get("positions").get("national").get("honorary_member")
        is_honorary_member_for_life_national = False

        for pos in cell:
            if HONORARY_MEMBER in pos.get("position") and pd.isna(pos.get("end_date")):
                is_honorary_member_for_life_national = True
                break

        return is_honorary_member_for_life_national

    def is_honorary_member_for_year_club(cell):
        HONORARY_MEMBER = config.get("contacts").get("positions").get("club").get("honorary_member")
        is_honorary_member_for_year_club = False

        for pos in cell:
            if HONORARY_MEMBER in pos.get("position") and not pd.isna(pos.get("end_date")):
                is_honorary_member_for_year_club = True
                break

        return is_honorary_member_for_year_club

    def is_honorary_member_for_year_national(cell):
        HONORARY_MEMBER = config.get("contacts").get("positions").get("national").get("honorary_member")
        is_honorary_member_for_year_national = False

        for pos in cell:
            if HONORARY_MEMBER in pos.get("position") and not pd.isna(pos.get("end_date")):
                is_honorary_member_for_year_national = True
                break

        return is_honorary_member_for_year_national

    def has_membership_errors(df):
        return df["is_member"] and df["is_past_member"]

    # Clean dirty rows
    df.drop(df[df["rt_club_number"].isnull()].index, inplace=True)
    for club in config.get("contacts").get("remove").get("rt_club_number"):
        df.drop(df[df["rt_club_number"] == club].index, inplace=True)

    # Convert types
    df["rt_club_number"] = df["rt_club_number"].astype("int")
    df["birth_date"] = pd.to_datetime(df["birth_date"])
    df["last_modified"] = pd.to_datetime(df["last_modified"]).dt.tz_localize(None)
    df["created_on"] = pd.to_datetime(df["created_on"]).dt.tz_localize(None)
    df["last_sync"] = pd.to_datetime(df["last_sync"]).dt.tz_localize(None)

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

    df["is_member"] = df["rt_global_positions_club"].apply(is_member)
    df["is_past_member"] = df["rt_global_positions_club"].apply(is_past_member)
    df["is_member_over_25"] = df.apply(is_member_over_25, axis=1)
    df["is_member_under_25"] = df.apply(is_member_under_25, axis=1)
    df["is_honorary_member_for_life_club"] = df["rt_global_positions_club"].apply(is_honorary_member_for_life_club)
    df["is_honorary_member_for_life_national"] = df["rt_global_positions_national"].apply(is_honorary_member_for_life_national)
    df["is_honorary_member_for_year_club"] = df["rt_global_positions_club"].apply(is_honorary_member_for_year_club)
    df["is_honorary_member_for_year_national"] = df["rt_global_positions_national"].apply(is_honorary_member_for_year_national)
    df["has_membership_errors"] = df.apply(has_membership_errors, axis=1)

    # Remove contacts with no positions
    df = df[~df["rt_global_positions"].str.len().eq(0)].copy()
    # Remove contacts in status expelled, resigned
    for status in config.get("contacts").get("remove").get("rt_status"):
        df.drop(df[df["rt_status"] == status].index, inplace=True)

    # Recently modified contacts flag
    df["recently_modified"] = df["last_modified"] > config.get("contacts").get("recently_modified_contacts_from")

    # Create utility columns
    df["profile_pic_file"] = df.apply(profile_pic_file, axis=1)

    print("Contacts clean ENDED")
    return df
