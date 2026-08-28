from pathlib import Path


def main() -> None:
    from app.core.environment import load_project_environment

    load_project_environment()
    sample_path = Path("data/sample/people.json")
    if not sample_path.exists():
        raise SystemExit(f"Sample data file not found: {sample_path}")

    print(f"Sample data is ready at {sample_path}")


if __name__ == "__main__":
    main()
