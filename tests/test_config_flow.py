import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

from awenta_ahr.config_flow import ConfigFlow
from awenta_ahr.const import DOMAIN


@pytest.mark.asyncio
async def test_config_flow_user_step(mock_credentials):
    """Test config flow user step"""
    flow = ConfigFlow()
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = MagicMock()
    flow.async_create_entry = MagicMock(return_value="result")
    
    result = await flow.async_step_user(mock_credentials)
    
    # Check entry was created
    assert flow.async_create_entry.called
    call_kwargs = flow.async_create_entry.call_args[1]
    assert call_kwargs["title"] == "Awenta HRV"
    assert call_kwargs["data"] == mock_credentials


@pytest.mark.asyncio
async def test_config_flow_shows_form():
    """Test config flow shows form when no input"""
    flow = ConfigFlow()
    flow.async_show_form = MagicMock(return_value="form_result")
    
    result = await flow.async_step_user(None)
    
    # Check form was shown
    assert flow.async_show_form.called
    call_kwargs = flow.async_show_form.call_args[1]
    assert call_kwargs["step_id"] == "user"
    assert "data_schema" in call_kwargs
