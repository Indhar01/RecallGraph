"""Notion integration for MemoGraph.

This module provides integration with Notion's API for bidirectional
synchronization of pages, blocks, properties, and databases.

Example:
    ```python
    from memograph.integrations.notion import NotionIntegration

    # Initialize integration
    integration = NotionIntegration(auth_token="secret_...")

    # Sync data
    result = await integration.sync(direction="pull")
    print(f"Pulled {result['pages_pulled']} pages")
    ```
"""

from memograph.integrations.notion.client import NotionClient
from memograph.integrations.notion.integration import NotionIntegration
from memograph.integrations.notion.auth import NotionAuth

__all__ = [
    "NotionClient",
    "NotionIntegration",
    "NotionAuth",
]
