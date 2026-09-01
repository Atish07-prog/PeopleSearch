from ingestion.column_mapper import map_columns, map_row_values


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


def test_maps_lowercase_compact_company_name_header() -> None:
    assert map_columns(["companyname", "email"]) == {
        "name": "companyname",
        "email": "email",
    }


def test_maps_hyphenated_firm_name_and_numbered_mobile() -> None:
    assert map_columns(["Firm-Name", "Mobile1", "City"]) == {
        "name": "Firm-Name",
        "phone": "Mobile1",
        "city": "City",
    }


def test_row_mapping_falls_back_from_blank_company_to_customer_name() -> None:
    assert map_row_values(
        ["Company Name", "Customer Name", "Mobile"],
        {"Company Name": "NULL", "Customer Name": "Asha Stores", "Mobile": "9876543210"},
    ) == {
        "name": "Asha Stores",
        "phone": "9876543210",
    }


def test_maps_school_and_compact_company_name_headers() -> None:
    assert map_columns(["School Name", "co_name", "Phone"]) == {
        "name": "School Name",
        "phone": "Phone",
    }
    assert map_row_values(
        ["Company Name", "co_name"],
        {"Company Name": "N/A", "co_name": "Artha Enterprises"},
    ) == {"name": "Artha Enterprises"}


def test_row_mapping_falls_back_to_bill_company() -> None:
    assert map_row_values(
        ["Name", "FIRST_NAME", "SECOND_NAME", "BILL_COMPANY"],
        {"Name": "", "FIRST_NAME": "", "SECOND_NAME": "", "BILL_COMPANY": "Indian Oil Corporation Limited"},
    ) == {"name": "Indian Oil Corporation Limited"}


def test_maps_contextual_backslash_business_name_column() -> None:
    headers = ["\\", "CONTACT PERSON", "ADD1", "CITY", "PHONE", "MOBILE", "EMAIL"]

    assert map_columns(headers)["name"] == "\\"
    assert map_row_values(
        headers,
        {"\\": "Aacord Signs", "CONTACT PERSON": "", "ADD1": "Mangalya", "CITY": "Mumbai", "PHONE": "123", "MOBILE": "", "EMAIL": ""},
    )["name"] == "Aacord Signs"


def test_maps_ca_list_export_headers() -> None:
    headers = ["h_title||''||  h_first_name|", "mrh_email", "mrh_prof_tel", "mrh_prof_mobile", "pin"]

    assert map_columns(headers) == {
        "name": "h_title||''||  h_first_name|",
        "email": "mrh_email",
        "phone": "mrh_prof_tel",
        "pincode": "pin",
    }
