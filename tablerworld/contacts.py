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

    def clean_address(cell):
        if not cell:
            return "-"

        item = cell[0]

        street1 = item.get("street1", None)
        street2 = item.get("street2", None)
        postal_code = item.get("postal_code", None)
        city = item.get("city", None)

        return f"{street1} - {postal_code} {city}"

    def clean_companies(cell):
        if not cell:
            return "-"

        item = cell[0]
        sector = item.get("sector", None)
        function = item.get("function", None)

        return f"{function.capitalize()}"

    df["first_name"] = df["first_name"].apply(clean_name)
    df["last_name"] = df["last_name"].apply(clean_name)
    df["phonenumbers"] = df["phonenumbers"].apply(clean_phonenumbers)
    df["address"] = df["address"].apply(clean_address)
    df["job"] = df["companies"].apply(clean_companies)

    return df
