from test_ingestion_extractor import create_zip_bytes



def test_ingest_canvas_submissions_success(
    client, temp_workspaces, admin_headers, section_id, mock_official_run_dispatch
):
    zip_bytes = create_zip_bytes({
        "jaxonlarsen_12345_67890_student_functions.py": b"print('hello')"
    })

    response = client.post(
        "/staff/courses/cs1400/assignments/simple-python-functions/submissions/ingest",
        files={"file": ("submissions.zip", zip_bytes, "application/zip")},
        data={"section_id": str(section_id)},
        headers=admin_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "queue"
    assert body["workflow_type"] == "official"
    assert body["total_submission_count"] == 1
    assert body["run_id"] is not None

    run_id = body["run_id"]
    zip_dest = temp_workspaces / "workspaces" / f"official_{run_id}.zip"
    assert zip_dest.exists()
    assert zip_dest.read_bytes() == zip_bytes


def test_ingest_requires_section_id(client, admin_headers):
    zip_bytes = create_zip_bytes({
        "jaxonlarsen_12345_67890_student_functions.py": b"print('hello')"
    })
    response = client.post(
        "/staff/courses/cs1400/assignments/simple-python-functions/submissions/ingest",
        files={"file": ("submissions.zip", zip_bytes, "application/zip")},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_ingest_canvas_submissions_invalid_extension(client, admin_headers, section_id):
    response = client.post(
        "/staff/courses/cs1400/assignments/simple-python-functions/submissions/ingest",
        files={"file": ("submissions.txt", b"not a zip", "text/plain")},
        data={"section_id": str(section_id)},
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert "Only ZIP files are accepted" in response.json()["detail"]


def test_ingest_canvas_submissions_not_canvas_zip(client, admin_headers, section_id):
    zip_bytes = create_zip_bytes({
        "main.py": b"print('hello')"
    })

    response = client.post(
        "/staff/courses/cs1400/assignments/simple-python-functions/submissions/ingest",
        files={"file": ("submissions.zip", zip_bytes, "application/zip")},
        data={"section_id": str(section_id)},
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert "does not contain recognized Canvas submissions" in response.json()["detail"]


def test_ingest_canvas_submissions_traversal_blocked(client, admin_headers, section_id):
    zip_bytes = create_zip_bytes({
        "../escaped.txt": b"traversal"
    })

    response = client.post(
        "/staff/courses/cs1400/assignments/simple-python-functions/submissions/ingest",
        files={"file": ("submissions.zip", zip_bytes, "application/zip")},
        data={"section_id": str(section_id)},
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert "Invalid or unsafe ZIP" in response.json()["detail"]
