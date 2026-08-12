import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.settings import get_settings


def test_judge0_language_id_default():
    """Verify default Judge0 language ID is set to custom ID 711 for Python 3.11+."""
    settings = get_settings()
    assert settings.judge0_language_id == 711


def test_judge0_allowlisted_dependencies():
    """Verify preinstalled dependencies include pillow, pygame, and tabulate."""
    settings = get_settings()
    deps = settings.preinstalled_dependency_names
    assert "pillow" in deps
    assert "pygame" in deps
    assert "tabulate" in deps


def test_seed_sql_file_validity():
    """Verify SQL seed script exists and targets language ID 711 and Python 3.11.9."""
    repo_root = Path(__file__).resolve().parents[2]
    sql_file = repo_root / "scripts" / "seed_judge0_language_311.sql"
    assert sql_file.is_file()

    content = sql_file.read_text(encoding="utf-8")
    assert "711" in content
    assert "Python (3.11.9)" in content
    assert "/usr/local/python-3.11.9/bin/python3.11 main.py" in content


def test_judge0_dockerfile_runtime():
    """Verify judge0.Dockerfile installs Python 3.11.9 and allowlisted packages."""
    repo_root = Path(__file__).resolve().parents[2]
    dockerfile = repo_root / "judge0.Dockerfile"
    assert dockerfile.is_file()

    content = dockerfile.read_text(encoding="utf-8")
    assert "Python-3.11.9" in content
    assert "pytest" in content
    assert "pillow" in content
    assert "pygame" in content
    assert "tabulate" in content


def test_docker_compose_seed_mount_and_timeouts():
    """Verify docker-compose.poc.yml mounts seed SQL script and configures 30s timeouts."""
    repo_root = Path(__file__).resolve().parents[2]
    compose_file = repo_root / "docker-compose.poc.yml"
    assert compose_file.is_file()

    content = compose_file.read_text(encoding="utf-8")
    assert "./scripts/seed_judge0_language_311.sql:/docker-entrypoint-initdb.d/01_seed_language_311.sql:ro" in content
    assert 'CPU_TIME_LIMIT: "30"' in content
    assert 'TEST_EXECUTION_TIMEOUT_SECONDS: ${TEST_EXECUTION_TIMEOUT_SECONDS:-30}' in content
