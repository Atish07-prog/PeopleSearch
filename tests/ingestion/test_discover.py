from ingestion.discover import discover_tabular_files


def test_discovery_excludes_excel_temporary_lock_files(tmp_path) -> None:
    (tmp_path / "contacts.xlsx").write_bytes(b"data")
    (tmp_path / "~$contacts.xlsx").write_bytes(b"temporary lock")

    sources = list(discover_tabular_files(tmp_path))

    assert [source.relative_path for source in sources] == ["contacts.xlsx"]
