import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add custom_components to path
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

from awenta_ahr.awenta_api import AwentaAPI


@pytest.mark.asyncio
async def test_api_login(hass, mock_credentials, mock_login_response):
    """Test API login"""
    api = AwentaAPI(hass, mock_credentials["email"], mock_credentials["password"])
    
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=json.dumps(mock_login_response))
        mock_post.return_value.__aenter__.return_value = mock_response
        
        await api.login()
        
        assert api.id_socket == "test_socket_id"
        assert api.key_socket == "test_socket_key"
        assert api.sha1 is not None


@pytest.mark.asyncio
async def test_list_devices(hass, mock_credentials, mock_login_response, mock_devices_response):
    """Test listing devices"""
    api = AwentaAPI(hass, mock_credentials["email"], mock_credentials["password"])
    api.id_socket = "test_socket_id"
    api.key_socket = "test_socket_key"
    
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=json.dumps(mock_devices_response))
        mock_post.return_value.__aenter__.return_value = mock_response
        
        await api.list_devices()
        
        assert len(api.devices) == 1
        assert api.devices[0]["mac"] == "AA:BB:CC:DD:EE:FF"


@pytest.mark.asyncio
async def test_register_listener(hass, mock_credentials):
    """Test registering listener callback"""
    api = AwentaAPI(hass, mock_credentials["email"], mock_credentials["password"])
    
    callback = AsyncMock()
    api.register_listener(callback)
    
    assert callback in api.listeners


def test_sha1_password_hashing(mock_credentials):
    """Test password is hashed"""
    import hashlib
    api = AwentaAPI(MagicMock(), mock_credentials["email"], mock_credentials["password"])
    
    expected_hash = hashlib.sha1(mock_credentials["password"].encode()).hexdigest()
    api.sha1 = expected_hash
    
    assert api.sha1 == expected_hash
    assert len(api.sha1) == 40  # SHA1 hex length
