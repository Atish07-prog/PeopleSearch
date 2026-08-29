from ingestion.column_mapper import map_columns


def test_maps_category_two_justdial_headers() -> None:
    mapping = map_columns(["Name", "Email", "Contact", "Address", "Pincode", "City", "Website", "Mobile"])

    assert mapping == {
        "name": "Name",
        "email": "Email",
        "phone": "Contact",
        "address": "Address",
        "pincode": "Pincode",
        "city": "City",
        "website": "Website",
    }


def test_maps_compact_business_name_header() -> None:
    assert map_columns(["BusinessName", "Mobile", "Email"]) == {
        "name": "BusinessName",
        "email": "Email",
        "phone": "Mobile",
    }


def test_maps_compact_camel_case_contact_headers() -> None:
    assert map_columns(["CompanyName", "ContactName", "MobileNo", "EmailID"]) == {
        "name": "CompanyName",
        "email": "EmailID",
        "phone": "MobileNo",
    }
