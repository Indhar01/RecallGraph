"""Tests for the base integration interface."""

import pytest
from datetime import datetime
from typing import Dict, List, Any
from memograph.integrations.base import IntegrationBase


class MockIntegration(IntegrationBase):
    """Mock implementation of IntegrationBase for testing"""

    def __init__(self):
        self.sync_called = False
        self.get_modified_items_called = False
        self.push_item_called = False
        self.pull_item_called = False

    async def sync(self, direction: str = "bidirectional") -> Dict[str, Any]:
        """Mock sync implementation"""
        self.sync_called = True
        return {"pulled": 0, "pushed": 0, "conflicts": 0, "errors": []}

    async def get_modified_items(self, since: datetime) -> List[Dict[str, Any]]:
        """Mock get_modified_items implementation"""
        self.get_modified_items_called = True
        return []

    async def push_item(self, item: Dict[str, Any]) -> bool:
        """Mock push_item implementation"""
        self.push_item_called = True
        return True

    async def pull_item(self, item_id: str) -> Dict[str, Any]:
        """Mock pull_item implementation"""
        self.pull_item_called = True
        return {"id": item_id, "content": "mock content"}


def test_cannot_instantiate_abstract_class():
    """Test that IntegrationBase cannot be instantiated directly"""
    with pytest.raises(TypeError):
        IntegrationBase()  # type: ignore


@pytest.mark.asyncio
async def test_mock_integration_sync():
    """Test that mock integration sync method works"""
    integration = MockIntegration()
    result = await integration.sync(direction="bidirectional")

    assert integration.sync_called
    assert "pulled" in result
    assert "pushed" in result
    assert "conflicts" in result
    assert "errors" in result


@pytest.mark.asyncio
async def test_mock_integration_get_modified_items():
    """Test that mock integration get_modified_items method works"""
    integration = MockIntegration()
    since = datetime.now()
    result = await integration.get_modified_items(since)

    assert integration.get_modified_items_called
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_mock_integration_push_item():
    """Test that mock integration push_item method works"""
    integration = MockIntegration()
    item = {"id": "test", "content": "test content"}
    result = await integration.push_item(item)

    assert integration.push_item_called
    assert result is True


@pytest.mark.asyncio
async def test_mock_integration_pull_item():
    """Test that mock integration pull_item method works"""
    integration = MockIntegration()
    item_id = "test-id"
    result = await integration.pull_item(item_id)

    assert integration.pull_item_called
    assert "id" in result
    assert result["id"] == item_id
    assert "content" in result


@pytest.mark.asyncio
async def test_sync_direction_parameter():
    """Test that sync accepts different direction parameters"""
    integration = MockIntegration()

    # Test different directions
    for direction in ["pull", "push", "bidirectional"]:
        integration.sync_called = False
        result = await integration.sync(direction=direction)
        assert integration.sync_called
        assert isinstance(result, dict)
