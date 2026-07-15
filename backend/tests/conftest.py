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


class FakeRedis:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value, *args, **kwargs):
        self.data[key] = str(value)
        return True

    def setex(self, key, time, value):
        self.data[key] = str(value)
        return True

    def decrby(self, key, count):
        val = int(self.data.get(key) or 0) - count
        self.data[key] = str(val)
        return val

    def delete(self, *keys):
        count = 0
        for k in keys:
            if k in self.data:
                self.data.pop(k)
                count += 1
        return count

    def rpush(self, key, *values):
        if key not in self.data:
            self.data[key] = []
        if len(values) == 1 and isinstance(values[0], (list, tuple)):
            self.data[key].extend([str(v) for v in values[0]])
        else:
            self.data[key].extend([str(v) for v in values])
        return len(self.data[key])

    def expire(self, key, time):
        return True

    def lrange(self, key, start, end):
        lst = self.data.get(key)
        if lst is None:
            return []
        if end == -1:
            return lst[start:]
        return lst[start:end+1]

    def pipeline(self):
        return FakePipeline(self)


class FakePipeline:
    def __init__(self, client):
        self.client = client
        self.commands = []

    def watch(self, *args, **kwargs):
        return self

    def unwatch(self, *args, **kwargs):
        return self

    def multi(self, *args, **kwargs):
        return self

    def set(self, key, value, *args, **kwargs):
        self.commands.append(("set", key, value))
        return self

    def execute(self):
        for cmd, key, val in self.commands:
            if cmd == "set":
                self.client.set(key, val)
        self.commands = []
        return []


@pytest.fixture(autouse=True)
def mock_redis_global():
    fake = FakeRedis()
    with patch("redis.Redis.from_url", return_value=fake):
        yield fake

