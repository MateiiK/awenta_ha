import sys
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest


# Mock Home Assistant objects
class MockHass:
    def __init__(self):
        self.data = {}
        self.async_create_task = AsyncMock()


@pytest.fixture
def hass():
    return MockHass()


@pytest.fixture
def mock_credentials():
    return {
        "email": "test@example.com",
        "password": "testpassword"
    }


@pytest.fixture
def mock_login_response():
    return {
        "status": "ok",
        "params": {
            "id": "test_socket_id",
            "key": "test_socket_key"
        }
    }


@pytest.fixture
def mock_devices_response():
    return {
        "status": "ok",
        "params": [
            {
                "name": "Test Device",
                "mac": "AA:BB:CC:DD:EE:FF",
                "model": "AHR"
            }
        ]
    }
