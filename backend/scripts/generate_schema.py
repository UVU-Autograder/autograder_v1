import json
from pathlib import Path
import sys

# Add backend directory to sys.path so we can import app
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.domains.assignments.schemas import AssignmentConfigV1

def main():
    schema = AssignmentConfigV1.model_json_schema()
    
    # We want to save the schema to docs/schemas/config_v1.schema.json
    repo_root = BACKEND_ROOT.parent
    schema_dir = repo_root / "docs" / "schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)
    
    schema_path = schema_dir / "config_v1.schema.json"
    schema_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"JSON Schema successfully written to: {schema_path}")

if __name__ == "__main__":
    main()
