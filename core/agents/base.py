"""Base agent class for the MultiCoder system.

This module defines the base Agent class that all specific agents inherit from.
It handles common functionality like MCP communication and logging.
"""
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from core.mcp.bus import message_bus
from utils.logging import configure_logger


class Agent(ABC):
    """Base agent class with MCP communication capabilities.
    
    All agents in the system inherit from this class to get common
    communication and lifecycle management.
    
    Attributes:
        name: Unique name identifier for the agent.
        channels: List of MCP channels to subscribe to.
        logger: Configured logger instance.
    """
    
    def __init__(
        self, 
        name: str,
        channels: list[str] = None,
        log_level: int = logging.INFO
    ) -> None:
        """Initialize a new agent.
        
        Args:
            name: Unique identifier for this agent.
            channels: List of channels to subscribe to.
            log_level: Logging level for this agent.
        """
        self.name = name
        self.channels = channels or []
        
        # Setup logging
        self.logger = logging.getLogger(f"agent.{name}")
        self.logger.setLevel(log_level)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
        self.logger.info(f"Agent {name} initialized")

    async def start(self) -> None:
        """Start the agent and establish MCP connections."""
        self.logger.info(f"Starting agent {self.name}")
        
        # Subscribe to channels
        for channel in self.channels:
            await message_bus.subscribe(channel, self._handle_message)
            
        if self.channels:
            self.logger.info(f"Subscribed to channels: {', '.join(self.channels)}")
        
        # Call agent-specific initialization
        await self.initialize()
        
        self.logger.info(f"Agent {self.name} started")
    
    async def initialize(self) -> None:
        """Override this method to add agent-specific initialization."""
        pass
        
    async def stop(self) -> None:
        """Stop the agent and clean up resources."""
        self.logger.info(f"Stopping agent {self.name}")
        
        # Unsubscribe from all channels
        for channel in self.channels:
            await message_bus.unsubscribe(channel, self._handle_message)
            
        self.logger.info(f"Agent {self.name} stopped")
    
    async def _handle_message(self, channel: str, message: Dict[str, Any]) -> None:
        """Handle an incoming message.
        
        Args:
            channel: The channel the message was received on.
            message: The message data.
        """
        sender = message.get("sender")
        action = message.get("action")
        payload = message.get("payload", {})
        
        self.logger.info(
            f"Received message on channel {channel}: {action} from {sender}"
        )
        
        # Process message
        await self.process_message(channel, message)
    
    async def publish(
        self, 
        channel: str, 
        action: str, 
        payload: Dict[str, Any]
    ) -> None:
        """Publish a message to a channel.
        
        Args:
            channel: The channel to publish to.
            action: The action type for the message.
            payload: The data payload for the message.
        """
        await message_bus.publish(channel, self.name, action, payload)
        self.logger.debug(f"Published to {channel}: {action}")
    
    @abstractmethod
    async def process_message(self, channel: str, message: Dict[str, Any]) -> None:
        """Process an incoming message.
        
        Args:
            channel: The channel the message was received on.
            message: The message data.
        """
        pass