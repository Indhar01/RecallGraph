"""Base class for all integrations with external systems."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class IntegrationBase(ABC):
    """Base class for all integrations"""

    @abstractmethod
    async def sync(self, direction: str = "bidirectional") -> Dict[str, Any]:
        """Sync data between MemoGraph and external system

        Args:
            direction: Sync direction - "pull", "push", or "bidirectional"

        Returns:
            Dict containing sync statistics (pulled, pushed, conflicts, errors)
        """
        pass

    @abstractmethod
    async def get_modified_items(self, since: datetime) -> List[Dict[str, Any]]:
        """Get items modified since timestamp

        Args:
            since: Timestamp to get modifications since

        Returns:
            List of modified items with their data
        """
        pass

    @abstractmethod
    async def push_item(self, item: Dict[str, Any]) -> bool:
        """Push item to external system

        Args:
            item: Item data to push

        Returns:
            True if push succeeded, False otherwise
        """
        pass

    @abstractmethod
    async def pull_item(self, item_id: str) -> Dict[str, Any]:
        """Pull item from external system

        Args:
            item_id: ID of item to pull

        Returns:
            Item data from external system
        """
        pass
