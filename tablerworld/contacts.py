import pandas as pd
import phonenumbers
from datetime import datetime


def clean(df):
    print("Contacts clean STARTED")

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

    def rt_global_positions_current(cell):
        def is_current(x):
            end_date = x.get("end_date")
            if end_date is None:
                return True
            elif datetime.strptime(end_date, "%Y-%m-%d").date() > datetime.now().date():
                return True
            else:
                return False

        current_positions = [x for x in cell if is_current(x)]
        return current_positions

    def rt_global_positions_relevant(cell):
        RELEVANT_POSITIONS = [
            "Members / Member",
            "Members / Honorary Member",
            "VIP / Honorary Member",
            "Past Members / Past Member",
            "Board / Past-President",
            "Board / President",
            "Board / Vice-President",
            "Board / Secretary",
            "Board / Treasurer",
            "Board Assistants / C.S.O.",
            "Board / I.R.O.",
            "Board / P.R.O.",
            "Board Assistants / Webmaster",
            "Board Assistants / Editor",
            "Board / C.S.O.",
            "Board Assistants / P.R.O.",
            "Board Assistants / R.S.O.",
            "Board Assistants / Shopkeeper",
            "Board Assistants / Secretary",
        ]

        def is_relevant(x):
            short_description = x.get("combination").get("short_description")
            position = short_description.rsplit(sep=" › ")
            position = position[-1]
            return position in RELEVANT_POSITIONS

        positions = [x for x in cell if is_relevant(x)]
        return positions

    def rt_global_positions_national(cell):
        res = []

        for x in cell:
            short_description = x.get("combination").get("short_description")
            position = short_description.rsplit(sep=" › ")

            if len(position) == 7:
                # It'a Club position
                continue
            elif len(position) == 5:
                # It's an Area position
                continue
            elif len(position) == 3:
                # It's a National position
                res.append(position[-1])

        return res

    def rt_global_positions_area(cell):
        res = []

        for x in cell:
            short_description = x.get("combination").get("short_description")
            position = short_description.rsplit(sep=" › ")

            if len(position) == 7:
                # It'a Club position
                continue
            elif len(position) == 5:
                # It's an Area position
                res.append(position[-1])
            elif len(position) == 3:
                # It's a National position
                continue

        return res

    def rt_global_positions_club(cell):
        res = []

        for x in cell:
            short_description = x.get("combination").get("short_description")
            position = short_description.rsplit(sep=" › ")

            if len(position) == 7:
                # It'a Club position
                res.append(position[-1])
            elif len(position) == 5:
                # It's an Area position
                continue
            elif len(position) == 3:
                # It's a National position
                continue

        return res

    def rt_global_positions_club_remove_redundant_positions(cell):
        HONORARY_MEMBER = "Members / Honorary Member"
        PAST_MEMBER = "Past Members / Past Member"

        if HONORARY_MEMBER in cell and PAST_MEMBER in cell:
            cell.remove(PAST_MEMBER)
        return cell

    # Apply
    df["first_name"] = df["first_name"].apply(clean_name)
    df["last_name"] = df["last_name"].apply(clean_name)
    df["phonenumbers"] = df["phonenumbers"].apply(clean_phonenumbers)
    df["email"] = df["email"].apply(email)
    df["address"] = df["address"].apply(clean_address)
    df["job"] = df["companies"].apply(clean_companies)
    df["name_partner"] = df["custom_fields"].apply(name_partner)
    df["rt_global_positions"] = df["rt_global_positions"].apply(rt_global_positions_current)
    df["rt_global_positions"] = df["rt_global_positions"].apply(rt_global_positions_relevant)
    df["rt_global_positions_national"] = df["rt_global_positions"].apply(rt_global_positions_national)
    df["rt_global_positions_area"] = df["rt_global_positions"].apply(rt_global_positions_area)
    df["rt_global_positions_club"] = df["rt_global_positions"].apply(rt_global_positions_club)
    df["rt_global_positions_club"] = df["rt_global_positions_club"].apply(
        rt_global_positions_club_remove_redundant_positions
    )

    # Recently modified contacts flag
    RECENTLY_MODIFIED_CONTACTS_FROM = "2023-09-06T05:00:00"
    df["recently_modified"] = df["last_modified"] > RECENTLY_MODIFIED_CONTACTS_FROM

    # Clean dirty rows
    df.drop(df[df["rt_club_number"].isnull()].index, inplace=True)
    df.drop(df[df["rt_club_number"] == 1].index, inplace=True)  # Remove RT 1 Milano
    df.drop(df[df["rt_club_number"] == 19].index, inplace=True)  # Remove RT 19 Livorno
    df.drop(df[df["rt_club_number"] == 20].index, inplace=True)  # Remove RT 20 Mantova
    df.drop(df[df["rt_club_number"] == 26].index, inplace=True)  # Remove RT 26 Asolo
    df.drop(df[df["rt_club_number"] == 39].index, inplace=True)  # Remove RT 39 Bergamo
    df.drop(df[df["rt_club_number"] == 47].index, inplace=True)  # Remove RT 47 Arezzo
    df.drop(df[df["rt_club_number"] == 50].index, inplace=True)  # Remove RT 50 Perugia
    df.drop(df[df["rt_club_number"] == 55].index, inplace=True)  # Remove RT 55 Pinerolo

    # Remove members expelled, resigned or without relevant positions
    df.drop(df[df["rt_status"] == "resigned"].index, inplace=True)
    df.drop(df[df["rt_status"] == "expulsed"].index, inplace=True)
    df = df[~df["rt_global_positions"].str.len().eq(0)].copy()

    # Convert types
    df["rt_club_number"] = df["rt_club_number"].astype("int")
    df["birth_date"] = pd.to_datetime(df["birth_date"])
    df["last_modified"] = pd.to_datetime(df["last_modified"]).dt.tz_localize(None)
    df["created_on"] = pd.to_datetime(df["created_on"]).dt.tz_localize(None)
    df["last_sync"] = pd.to_datetime(df["last_sync"]).dt.tz_localize(None)

    # Create utility columns
    df["profile_pic_file"] = df.apply(profile_pic_file, axis=1)

    print("Contacts clean ENDED")
    return df
