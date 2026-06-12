from unittest.mock import MagicMock, patch
import pytest
import httpx

@pytest.fixture
def mock_httpx_client():
    """Generic fixture to mock httpx.Client calls in integrations.
    Usage in test:
        def test_api_calls(mock_httpx_client):
            mock_httpx_client.get.return_value = httpx.Response(200, json={"status": "ok"})
    """
    with patch("httpx.Client") as mock_class:
        mock_instance = MagicMock(spec=httpx.Client)
        mock_class.return_value = mock_instance
        yield mock_instance
