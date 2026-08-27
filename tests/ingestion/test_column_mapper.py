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
