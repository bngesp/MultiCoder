"""CLI entrypoint for MCP client.

This module provides the entry point for the MultiCoder CLI
with MCP communication.
"""
import argparse
import asyncio
import logging
import os
import sys

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from config.settings import get_config
from cli.mcp_client import MCPClient
from utils.logging import configure_logger


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed arguments.
    """
    config = get_config()
    
    parser = argparse.ArgumentParser(description="MultiCoder: AI-powered code generation")
    parser.add_argument(
        "--prompt", "-p",
        type=str,
        help="Prompt for code generation (non-interactive mode)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=config["logging"]["level"],
        help=f"Set logging level (default: {config['logging']['level']})"
    )
    
    return parser.parse_args()


async def main() -> None:
    """Main entry point for the CLI."""
    args = parse_args()
    
    # Configure logging
    log_level = args.log_level
    configure_logger("multicoder", log_level)
    
    # Run CLI
    client = MCPClient(log_level=log_level)
    await client.run(args.prompt)


if __name__ == "__main__":
    asyncio.run(main())