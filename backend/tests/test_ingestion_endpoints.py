import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.db.base import Base, import_domain_models  # noqa: E402
from app.db.seed import initialize_database  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import create_app  # noqa: E402
from test_ingestion_extractor import create_zip_bytes  # noqa: E402


@pytest.fixture(autouse=True)
def db_session():
    import_domain_models()
    Base.metadata.drop_all(bind=engine)
    initialize_database(seed=True)
    with SessionLocal() as session:
        yield session
    Base.metadata.drop_all(bind=engine)
    initialize_database(seed=True)


@pytest.fixture(autouse=True)
def temp_workspace_storage(tmp_path, monkeypatch):
    from app.core.settings import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "artifact_storage_dir", str(tmp_path / "artifacts"))
    yield tmp_path


@pytest.fixture()
def client():
    return TestClient(create_app())


def test_ingest_canvas_submissions_success(client, temp_workspace_storage):
    # 1. Create a valid Canvas ZIP in memory
    zip_bytes = create_zip_bytes({
        "jaxonlarsen_12345_67890_student_functions.py": b"print('hello')"
    })

    # 2. POST to endpoint
    response = client.post(
        "/staff/courses/cs1400/assignments/simple-python-functions/submissions/ingest",
        files={"file": ("submissions.zip", zip_bytes, "application/zip")}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "queue"
    assert body["workflow_type"] == "official"
    assert body["total_submission_count"] == 1
    assert body["run_id"] is not None

    # Check if files were created on disk under transient workspaces
    run_id = body["run_id"]
    zip_dest = temp_workspace_storage / "workspaces" / f"official_{run_id}.zip"
    assert zip_dest.exists()
    assert zip_dest.read_bytes() == zip_bytes


def test_ingest_canvas_submissions_invalid_extension(client):
    response = client.post(
        "/staff/courses/cs1400/assignments/simple-python-functions/submissions/ingest",
        files={"file": ("submissions.txt", b"not a zip", "text/plain")}
    )
    assert response.status_code == 400
    assert "Only ZIP files are accepted" in response.json()["detail"]


def test_ingest_canvas_submissions_not_canvas_zip(client):
    zip_bytes = create_zip_bytes({
        "main.py": b"print('hello')"
    })

    response = client.post(
        "/staff/courses/cs1400/assignments/simple-python-functions/submissions/ingest",
        files={"file": ("submissions.zip", zip_bytes, "application/zip")}
    )
    assert response.status_code == 400
    assert "does not contain recognized Canvas submissions" in response.json()["detail"]


def test_ingest_canvas_submissions_traversal_blocked(client):
    zip_bytes = create_zip_bytes({
        "../escaped.txt": b"traversal"
    })

    response = client.post(
        "/staff/courses/cs1400/assignments/simple-python-functions/submissions/ingest",
        files={"file": ("submissions.zip", zip_bytes, "application/zip")}
    )
    assert response.status_code == 400
    assert "Invalid or unsafe ZIP" in response.json()["detail"]
