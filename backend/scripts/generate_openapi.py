import json
import sys
from pathlib import Path

# Add backend directory to sys.path so we can import app
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import create_app


def main():
    app = create_app()
    openapi_schema = app.openapi()

    # We want to save the schema to docs/schemas/openapi.json
    repo_root = BACKEND_ROOT.parent
    schema_dir = repo_root / "docs" / "schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)

    openapi_path = schema_dir / "openapi.json"
    new_content = json.dumps(openapi_schema, indent=2)
    current_content = openapi_path.read_text(encoding="utf-8") if openapi_path.exists() else None
    if current_content != new_content:
        openapi_path.write_text(new_content, encoding="utf-8")
        print(f"OpenAPI Schema updated at: {openapi_path}")
    else:
        print(f"OpenAPI Schema up to date at: {openapi_path}")

if __name__ == "__main__":
    main()
