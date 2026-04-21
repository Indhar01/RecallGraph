"""Notion API client wrapper for MemoGraph integration."""

from typing import Dict, List, Any, Optional
import os


class NotionClient:
    """Wrapper for Notion API client with MemoGraph-specific functionality.
    
    This class provides a clean interface to the Notion API, handling
    authentication and common operations for syncing with MemoGraph.
    
    Attributes:
        auth_token: Notion API integration token
        client: Underlying notion_client.Client instance
    
    Example:
        ```python
        client = NotionClient(auth_token="secret_...")
        if client.test_connection():
            pages = client.list_pages()
        ```
    """
    
    def __init__(self, auth_token: Optional[str] = None):
        """Initialize Notion client with authentication token.
        
        Args:
            auth_token: Notion API token. If None, reads from NOTION_API_TOKEN env var.
            
        Raises:
            ValueError: If no auth token is provided or found in environment.
            ImportError: If notion-client package is not installed.
        """
        try:
            from notion_client import Client
        except ImportError:
            raise ImportError(
                "notion-client package not installed. "
                "Install with: pip install notion-client"
            )
        
        self.auth_token = auth_token or os.getenv('NOTION_API_TOKEN')
        if not self.auth_token:
            raise ValueError(
                "Notion API token required. Provide auth_token parameter or "
                "set NOTION_API_TOKEN environment variable."
            )
        
        self.client = Client(auth=self.auth_token)
    
    def test_connection(self) -> bool:
        """Test connection to Notion API.
        
        Returns:
            True if connection successful, False otherwise.
        """
        try:
            self.client.users.me()
            return True
        except Exception as e:
            print(f"Notion API connection failed: {e}")
            return False
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get information about the authenticated user/bot.
        
        Returns:
            User information dictionary from Notion API.
        """
        return self.client.users.me()
    
    def search_pages(
        self,
        query: Optional[str] = None,
        filter_type: Optional[str] = None,
        sort_direction: str = "descending",
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Search for pages in the workspace.
        
        Args:
            query: Text query to search for (optional)
            filter_type: Filter by object type ("page" or "database")
            sort_direction: "ascending" or "descending" (by last_edited_time)
            page_size: Number of results per page (max 100)
            
        Returns:
            List of page objects matching the search criteria.
        """
        search_params: Dict[str, Any] = {
            "page_size": min(page_size, 100)
        }
        
        if query:
            search_params["query"] = query
        
        if filter_type:
            search_params["filter"] = {"property": "object", "value": filter_type}
        
        search_params["sort"] = {
            "direction": sort_direction,
            "timestamp": "last_edited_time"
        }
        
        response = self.client.search(**search_params)
        return response.get("results", [])
    
    def list_pages(self, database_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List pages, optionally filtered by database.
        
        Args:
            database_id: If provided, only return pages from this database
            
        Returns:
            List of page objects.
        """
        if database_id:
            response = self.client.databases.query(database_id=database_id)
            return response.get("results", [])
        else:
            return self.search_pages(filter_type="page")
    
    def get_page(self, page_id: str) -> Dict[str, Any]:
        """Retrieve a page by ID.
        
        Args:
            page_id: Notion page ID (with or without dashes)
            
        Returns:
            Page object from Notion API.
        """
        return self.client.pages.retrieve(page_id=page_id)
    
    def get_blocks(self, block_id: str, page_size: int = 100) -> List[Dict[str, Any]]:
        """Get child blocks of a block or page.
        
        Args:
            block_id: ID of the parent block or page
            page_size: Number of blocks to retrieve (max 100)
            
        Returns:
            List of block objects.
        """
        response = self.client.blocks.children.list(
            block_id=block_id,
            page_size=min(page_size, 100)
        )
        return response.get("results", [])
    
    def get_all_blocks(self, block_id: str) -> List[Dict[str, Any]]:
        """Get all child blocks recursively (handles pagination).
        
        Args:
            block_id: ID of the parent block or page
            
        Returns:
            List of all block objects, including nested blocks.
        """
        all_blocks = []
        has_more = True
        start_cursor = None
        
        while has_more:
            response = self.client.blocks.children.list(
                block_id=block_id,
                start_cursor=start_cursor,
                page_size=100
            )
            all_blocks.extend(response.get("results", []))
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")
        
        return all_blocks
    
    def create_page(
        self,
        parent: Dict[str, Any],
        properties: Dict[str, Any],
        children: Optional[List[Dict[str, Any]]] = None,
        icon: Optional[Dict[str, Any]] = None,
        cover: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new page in Notion.
        
        Args:
            parent: Parent object (database_id or page_id)
            properties: Page properties (title, etc.)
            children: Optional list of block children
            icon: Optional page icon
            cover: Optional page cover image
            
        Returns:
            Created page object.
            
        Example:
            ```python
            parent = {"database_id": "abc123"}
            properties = {
                "title": {"title": [{"text": {"content": "New Page"}}]}
            }
            page = client.create_page(parent, properties)
            ```
        """
        params: Dict[str, Any] = {
            "parent": parent,
            "properties": properties
        }
        
        if children:
            params["children"] = children
        if icon:
            params["icon"] = icon
        if cover:
            params["cover"] = cover
        
        return self.client.pages.create(**params)
    
    def update_page(
        self,
        page_id: str,
        properties: Optional[Dict[str, Any]] = None,
        icon: Optional[Dict[str, Any]] = None,
        cover: Optional[Dict[str, Any]] = None,
        archived: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Update an existing page's properties.
        
        Args:
            page_id: ID of the page to update
            properties: Properties to update
            icon: New icon (optional)
            cover: New cover (optional)
            archived: Whether to archive the page
            
        Returns:
            Updated page object.
        """
        params: Dict[str, Any] = {"page_id": page_id}
        
        if properties is not None:
            params["properties"] = properties
        if icon is not None:
            params["icon"] = icon
        if cover is not None:
            params["cover"] = cover
        if archived is not None:
            params["archived"] = archived
        
        return self.client.pages.update(**params)
    
    def append_blocks(
        self,
        block_id: str,
        children: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Append blocks as children to an existing block.
        
        Args:
            block_id: ID of the parent block
            children: List of block objects to append
            
        Returns:
            Response with appended blocks.
        """
        return self.client.blocks.children.append(
            block_id=block_id,
            children=children
        )
    
    def get_database(self, database_id: str) -> Dict[str, Any]:
        """Retrieve a database object.
        
        Args:
            database_id: Notion database ID
            
        Returns:
            Database object with schema information.
        """
        return self.client.databases.retrieve(database_id=database_id)
    
    def query_database(
        self,
        database_id: str,
        filter_params: Optional[Dict[str, Any]] = None,
        sorts: Optional[List[Dict[str, Any]]] = None,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Query a database with optional filters and sorting.
        
        Args:
            database_id: ID of the database to query
            filter_params: Filter conditions (optional)
            sorts: Sort parameters (optional)
            page_size: Number of results per page
            
        Returns:
            List of page objects from the database.
        """
        params: Dict[str, Any] = {
            "database_id": database_id,
            "page_size": min(page_size, 100)
        }
        
        if filter_params:
            params["filter"] = filter_params
        if sorts:
            params["sorts"] = sorts
        
        response = self.client.databases.query(**params)
        return response.get("results", [])
    
    def delete_block(self, block_id: str) -> Dict[str, Any]:
        """Delete (archive) a block.
        
        Args:
            block_id: ID of the block to delete
            
        Returns:
            Updated block object with archived=True.
        """
        return self.client.blocks.delete(block_id=block_id)