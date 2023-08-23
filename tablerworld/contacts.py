import pandas as pd
import phonenumbers


def clean(df):
    # Clean functions
    def clean_name(cell):
        return cell.title()

    def clean_phonenumbers(cell):
        if not cell:
            return "-"

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
            phone = "-"

        phone = phone.encode("ascii", errors="ignore").decode()
        phone_parsed = phonenumbers.parse(phone, "IT")
        phone_international = phonenumbers.format_number(phone_parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        return phone_international

    def email(cell):
        return str(cell).lower()

    def clean_address(cell):
        if not cell:
            return "-"

        item = cell[0]

        street1 = item.get("street1")
        # street2 = item.get("street2")
        postal_code = item.get("postal_code")
        city = item.get("city")

        street1 = str(street1).title()
        # street2 = str(street2).title()
        postal_code = str(postal_code).title()
        city = str(city).title()

        return f"{street1} - {postal_code} {city}"

    def clean_companies(cell):
        if not cell:
            return "-"

        item = cell[0]
        sector = item.get("sector", None)
        function = item.get("function", None)

        return f"{function.capitalize()}"

    def name_partner(cell):
        if not cell:
            return ""

        member_info = [x for x in cell if x.get("name") == "Member Info"]
        if not member_info:
            return ""

        name_partner = [x for x in member_info[0].get("rows") if x.get("key") == "Name partner"]
        if not name_partner:
            return ""

        return name_partner[0].get("value")

    def profile_pic_file(df):
        return f"rt{df['rt_club_number']:02}_{df['last_name'].replace(' ', '')}_{df['first_name'].replace(' ', '')}.jpg"

    df["first_name"] = df["first_name"].apply(clean_name)
    df["last_name"] = df["last_name"].apply(clean_name)
    df["phonenumbers"] = df["phonenumbers"].apply(clean_phonenumbers)
    df["email"] = df["email"].apply(email)
    df["address"] = df["address"].apply(clean_address)
    df["job"] = df["companies"].apply(clean_companies)
    df["name_partner"] = df["custom_fields"].apply(name_partner)

    # Clean dirty rows
    df.drop(df[df["rt_club_number"].isnull()].index, inplace=True)

    # Convert types
    df["rt_club_number"] = df["rt_club_number"].astype("int")
    df["birth_date"] = pd.to_datetime(df["birth_date"])

    # Create utility columns
    df["profile_pic_file"] = df.apply(profile_pic_file, axis=1)

    return df
