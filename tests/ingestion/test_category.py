from ingestion.category import plan_category


def test_category_plan_reports_selected_file_extensions(tmp_path) -> None:
    (tmp_path / "one.csv").write_text("Name\nAsha\n", encoding="utf-8")
    (tmp_path / "two.txt").write_text("ignored", encoding="utf-8")

    summary = plan_category(tmp_path, max_files=10)

    assert summary.selected_files == 1
    assert summary.statuses == {".csv": 1}
