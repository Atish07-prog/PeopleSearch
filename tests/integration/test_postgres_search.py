"""Opt-in PostgreSQL provider checks against isolated fixture rows."""

import os
import uuid

import pytest

from app.api.schemas.search import PersonSearchRequest
from app.providers.postgres_provider import PostgresPeopleProvider


pytestmark = pytest.mark.integration


@pytest.fixture
def postgres_search_url() -> str:
    database_url = os.getenv("POSTGRES_INTEGRATION_DATABASE_URL")
    if not database_url:
        pytest.skip("Set POSTGRES_INTEGRATION_DATABASE_URL to run PostgreSQL integration tests")

    import psycopg
    from psycopg.types.json import Jsonb

    run_id = uuid.uuid4()
    source_id = uuid.uuid4()
    profiles = [
        ("Integration Exact", "integration exact"),
        ("Integration Exact Partners", "integration exact partners"),
        ("A Integration Exact Company", "a integration exact company"),
        ("NULL", "null"),
    ]
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO ingestion_runs (id, dataset_root, status) VALUES (%s, %s, %s)",
            (run_id, "integration-test", "completed"),
        )
        cursor.execute(
            """
            INSERT INTO source_files (id, ingestion_run_id, relative_path, extension, size_bytes, modified_at, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (source_id, run_id, "integration.csv", ".csv", 1, "integration-test", "completed"),
        )
        for row_number, (display_name, normalized_name) in enumerate(profiles, start=1):
            cursor.execute(
                """
                INSERT INTO staged_records
                    (ingestion_run_id, source_file_id, source_sheet, source_row_number,
                     source_headers, raw_cells, raw_values, mapped_values, validation_issues,
                     exact_row_fingerprint, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    run_id,
                    source_id,
                    "CSV",
                    row_number,
                    Jsonb(["Name"]),
                    Jsonb([display_name]),
                    Jsonb({"Name": display_name}),
                    Jsonb({"name": display_name}),
                    Jsonb([]),
                    f"{row_number:064x}",
                    "staged",
                ),
            )
            staged_record_id = cursor.fetchone()[0]
            cursor.execute(
                """
                INSERT INTO search_profiles (id, staged_record_id, record_type, display_name, normalized_name)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (uuid.uuid4(), staged_record_id, "unclassified", display_name, normalized_name),
            )
        connection.commit()
    try:
        yield database_url
    finally:
        with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
            cursor.execute("DELETE FROM ingestion_runs WHERE id = %s", (run_id,))
            connection.commit()


def test_postgres_provider_ranks_exact_prefix_and_substring_matches(postgres_search_url: str) -> None:
    results = PostgresPeopleProvider(postgres_search_url).search_people(PersonSearchRequest(query="Integration Exact", limit=10))

    assert results.total == 3
    assert [person.name for person in results.people] == [
        "Integration Exact",
        "Integration Exact Partners",
        "A Integration Exact Company",
    ]


def test_postgres_provider_excludes_placeholder_names(postgres_search_url: str) -> None:
    results = PostgresPeopleProvider(postgres_search_url).search_people(PersonSearchRequest(query="NULL", limit=10))

    assert results.total == 0
