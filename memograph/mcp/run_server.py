#!/usr/bin/env python3
"""Run the MemoGraph MCP server using the official MCP SDK.

This script starts the MCP server that exposes MemoGraph functionality
to MCP-compatible AI clients like Claude Desktop, Cline, etc.

Usage:
    python -m memograph.mcp.run_server --vault ~/my-vault

    Or set environment variable:
    export MEMOGRAPH_VAULT=~/my-vault
    python -m memograph.mcp.run_server
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .server import MemoGraphMCPServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Global MemoGraph server instance
memograph_server: Optional[MemoGraphMCPServer] = None


async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    if not memograph_server:
        return []

    schemas = memograph_server.get_tools_schema()

    # Convert our schema format to MCP Tool format
    tools = []
    for schema in schemas:
        tool = Tool(
            name=schema["name"],
            description=schema["description"],
            inputSchema=schema["inputSchema"],
        )
        tools.append(tool)

    return tools


async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool execution."""
    if not memograph_server:
        return [TextContent(type="text", text="Error: Server not initialized")]

    try:
        # Route to appropriate handler
        if name == "search_vault":
            result = await memograph_server.search_vault(**arguments)
        elif name == "create_memory":
            result = await memograph_server.create_memory(**arguments)
        elif name == "query_with_context":
            result = await memograph_server.query_with_context(**arguments)
        elif name == "get_vault_stats":
            result = await memograph_server.get_vault_stats()
        elif name == "list_memories":
            result = await memograph_server.list_memories(**arguments)
        elif name == "get_memory":
            result = await memograph_server.get_memory(**arguments)
        elif name == "import_document":
            result = await memograph_server.import_document(**arguments)
        else:
            result = {
                "success": False,
                "error": f"Unknown tool: {name}",
            }

        # Format result as text content
        import json

        result_text = json.dumps(result, indent=2)
        return [TextContent(type="text", text=result_text)]

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        import json

        error_result = {
            "success": False,
            "error": str(e),
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


async def run_server(vault_path: str, llm_provider: str, llm_model: Optional[str]):
    """Run the MCP server using the official SDK."""
    global memograph_server

    # Initialize MemoGraph server
    memograph_server = MemoGraphMCPServer(
        vault_path=vault_path,
        llm_provider=llm_provider,
        llm_model=llm_model,
    )

    logger.info(f"Initialized MemoGraph MCP server with vault: {vault_path}")

    # Create MCP server
    server = Server("memograph")

    # Register handlers
    @server.list_tools()
    async def list_tools_handler():
        return await handle_list_tools()

    @server.call_tool()
    async def call_tool_handler(name: str, arguments: dict):
        return await handle_call_tool(name, arguments)

    # Run stdio server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("MemoGraph MCP Server started (stdio mode)")
        logger.info(f"Vault: {vault_path}")
        logger.info(f"Provider: {llm_provider}")
        logger.info("Ready for requests...")

        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """Main entry point for MCP server."""
    parser = argparse.ArgumentParser(
        description="MemoGraph MCP Server - Expose vault to AI assistants"
    )
    parser.add_argument(
        "--vault",
        default=os.environ.get("MEMOGRAPH_VAULT", "~/my-vault"),
        help="Path to MemoGraph vault (default: $MEMOGRAPH_VAULT or ~/my-vault)",
    )
    parser.add_argument(
        "--provider",
        default=os.environ.get("MEMOGRAPH_PROVIDER"),
        choices=["ollama", "claude"],
        help="LLM provider for query_with_context (optional, only needed for AI-generated answers)",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("MEMOGRAPH_MODEL"),
        help="LLM model name (default: provider default)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Validate vault path
    vault_path = Path(args.vault).expanduser()
    if not vault_path.exists():
        logger.warning(f"Vault path does not exist, will be created: {vault_path}")
        vault_path.mkdir(parents=True, exist_ok=True)

    # Run server
    try:
        asyncio.run(
            run_server(
                vault_path=str(vault_path),
                llm_provider=args.provider,
                llm_model=args.model,
            )
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
