import os

from app.core.environment import load_project_environment


def test_load_project_environment_preserves_explicit_values(tmp_path, monkeypatch) -> None:
    environment_file = tmp_path / ".env"
    environment_file.write_text(
        "DATABASE_URL=postgresql://from-file\nSEARCH_PROVIDER='postgres'\n# ignored\nINVALID LINE\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DATABASE_URL", "postgresql://explicit")
    monkeypatch.delenv("SEARCH_PROVIDER", raising=False)

    loaded = load_project_environment(environment_file)

    assert loaded == environment_file
    assert os.environ["DATABASE_URL"] == "postgresql://explicit"
    assert os.environ["SEARCH_PROVIDER"] == "postgres"
