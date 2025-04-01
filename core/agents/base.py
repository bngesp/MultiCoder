"""Base agent class for the MultiCoder system.

This module defines the base Agent class that all specific agents inherit from.
It handles common functionality like PubSub communication and logging.
"""
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import redis.asyncio as redis


class Agent(ABC):
    """Base agent class with Redis PubSub communication capabilities.
    
    All agents in the system inherit from this class to get common
    communication and lifecycle management.
    
    Attributes:
        name: Unique name identifier for the agent.
        redis_url: Connection URL for Redis.
        channels: List of PubSub channels to subscribe to.
        logger: Configured logger instance.
        redis_client: Redis client connection.
        pubsub: Redis PubSub connection.
    """
    
    def __init__(
        self, 
        name: str,
        redis_url: str = "redis://localhost:6379/0", 
        channels: list[str] = None,
        log_level: int = logging.INFO
    ) -> None:
        """Initialize a new agent.
        
        Args:
            name: Unique identifier for this agent.
            redis_url: Redis connection string.
            channels: List of channels to subscribe to.
            log_level: Logging level for this agent.
        """
        self.name = name
        self.redis_url = redis_url
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
            
        # Redis will be initialized in the start method
        self.redis_client = None
        self.pubsub = None
        
        self.logger.info(f"Agent {name} initialized")

    async def start(self) -> None:
        """Start the agent and establish Redis connections."""
        self.logger.info(f"Starting agent {self.name}")
        self.redis_client = redis.Redis.from_url(self.redis_url)
        self.pubsub = self.redis_client.pubsub()
        
        # Subscribe to channels
        if self.channels:
            await self.pubsub.subscribe(*self.channels)
            self.logger.info(f"Subscribed to channels: {', '.join(self.channels)}")
        
        # Start listening for messages
        asyncio.create_task(self._listen())
        
        # Call agent-specific initialization
        await self.initialize()
        
        self.logger.info(f"Agent {self.name} started")
    
    async def initialize(self) -> None:
        """Override this method to add agent-specific initialization."""
        pass
        
    async def stop(self) -> None:
        """Stop the agent and clean up resources."""
        self.logger.info(f"Stopping agent {self.name}")
        
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.aclose()
            
        if self.redis_client:
            await self.redis_client.aclose()
            
        self.logger.info(f"Agent {self.name} stopped")
    
    async def _listen(self) -> None:
        """Listen for messages on subscribed channels."""
        self.logger.info(f"Agent {self.name} listening for messages")
        
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"].decode("utf-8")
                    data = json.loads(message["data"].decode("utf-8"))
                    
                    self.logger.info(
                        f"Received message on channel {channel}: {data}"
                    )
                    
                    # Process message
                    await self.process_message(channel, data)
        except asyncio.CancelledError:
            self.logger.info(f"Message listening canceled for {self.name}")
        except Exception as e:
            self.logger.error(f"Error in message listener: {e}", exc_info=True)
    
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
        message = {
            "sender": self.name,
            "action": action,
            "payload": payload
        }
        
        message_json = json.dumps(message)
        await self.redis_client.publish(channel, message_json)
        self.logger.debug(f"Published to {channel}: {message}")
    
    @abstractmethod
    async def process_message(self, channel: str, message: Dict[str, Any]) -> None:
        """Process an incoming message.
        
        Args:
            channel: The channel the message was received on.
            message: The message data.
        """
        pass