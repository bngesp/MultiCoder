"""Main entry point for the MultiCoder system.

This module provides the entry point for running the complete
MultiCoder system with all agents or individual components.
"""
import argparse
import asyncio
import logging
import os
import sys
from typing import List, Optional

# Ajouter le répertoire parent au chemin de recherche de Python
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config.settings import get_config
from core.agents import Coordinator, CodeGenerator, CodeValidator
from utils.logging import configure_logger as configure_logging



async def run_coordinator(log_level: str) -> None:
    """Run the coordinator agent.
    
    Args:
        log_level: Logging level.
    """
    # Import here to avoid circular imports
    from core.mcp.bus import message_bus
    
    # Start the MCP bus first
    await message_bus.start()
    
    # Create and start the agent
    agent = Coordinator(log_level=getattr(logging, log_level))
    await agent.start()
    
    try:
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nStopping coordinator...")
    finally:
        await agent.stop()
        await message_bus.stop()


async def run_generator(log_level: str) -> None:
    """Run the code generator agent.
    
    Args:
        log_level: Logging level.
    """
    # Import here to avoid circular imports
    from core.mcp.bus import message_bus
    
    # Start the MCP bus first
    await message_bus.start()
    
    # Create and start the agent
    agent = CodeGenerator(log_level=getattr(logging, log_level))
    await agent.start()
    
    try:
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nStopping code generator...")
    finally:
        await agent.stop()
        await message_bus.stop()


async def run_validator(log_level: str) -> None:
    """Run the code validator agent.
    
    Args:
        log_level: Logging level.
    """
    # Import here to avoid circular imports
    from core.mcp.bus import message_bus
    
    # Start the MCP bus first
    await message_bus.start()
    
    # Create and start the agent
    agent = CodeValidator(log_level=getattr(logging, log_level))
    await agent.start()
    
    try:
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nStopping code validator...")
    finally:
        await agent.stop()
        await message_bus.stop()


async def run_all(log_level: str) -> None:
    """Run all the agents together.
    
    Args:
        log_level: Logging level.
    """
    # Import here to avoid circular imports
    from core.mcp.bus import message_bus
    
    # Create all agents
    coordinator = Coordinator(log_level=getattr(logging, log_level))
    generator = CodeGenerator(log_level=getattr(logging, log_level))
    validator = CodeValidator(log_level=getattr(logging, log_level))
    
    # Start the MCP bus first
    await message_bus.start()
    
    # Start all agents
    await coordinator.start()
    await generator.start()
    await validator.start()
    
    print("\n🤖 MultiCoder system running (Press Ctrl+C to stop)")
    
    try:
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nStopping all agents...")
    finally:
        # Stop all agents
        await validator.stop()
        await generator.stop()
        await coordinator.stop()
        
        # Stop the MCP bus last
        await message_bus.stop()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed arguments.
    """
    config = get_config()
    
    parser = argparse.ArgumentParser(description="MultiCoder: Multi-agent code generation system")
    parser.add_argument(
        "--component", "-c",
        type=str,
        choices=["all", "coordinator", "generator", "validator"],
        default="all",
        help="Component to run (default: all)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=config["logging"]["level"],
        help=f"Set logging level (default: {config['logging']['level']})"
    )
    
    return parser.parse_args()


async def main() -> None:
    """Main entry point for the application."""
    args = parse_args()
    
    # Configure logging
    configure_logging("multicoder", args.log_level)
    
    # Run the selected component
    if args.component == "coordinator":
        await run_coordinator(args.log_level)
    elif args.component == "generator":
        await run_generator(args.log_level)
    elif args.component == "validator":
        await run_validator(args.log_level)
    else:  # all
        await run_all(args.log_level)


if __name__ == "__main__":
    asyncio.run(main())