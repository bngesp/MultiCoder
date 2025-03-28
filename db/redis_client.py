"""Redis client module for MultiCoder.

This module provides a wrapper around redis-py for common Redis operations
used in the MultiCoder system.
"""
import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Union

import redis.asyncio as redis

from utils.logging import configure_logger


class RedisClient:
    """Wrapper around redis-py for async Redis operations.
    
    Provides a consistent interface for Redis operations used in the
    MultiCoder system with appropriate error handling.
    
    Attributes:
        redis_url: Redis connection URL.
        client: Redis client instance.
        logger: Logger for this client.
    """
    
    def __init__(
        self, 
        redis_url: str = "redis://localhost:6379/0",
        log_level: str = "INFO"
    ) -> None:
        """Initialize Redis client.
        
        Args:
            redis_url: Redis connection URL.
            log_level: Logging level.
        """
        self.redis_url = redis_url
        self.client = None
        self.logger = logging.getLogger("multicoder.redis")
        self.logger.setLevel(getattr(logging, log_level))
    
    async def connect(self) -> None:
        """Connect to Redis server."""
        self.logger.debug(f"Connecting to Redis at {self.redis_url}")
        try:
            self.client = redis.Redis.from_url(self.redis_url)
            # Test connection
            await self.client.ping()
            self.logger.info(f"Connected to Redis at {self.redis_url}")
        except redis.RedisError as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis server."""
        if self.client:
            self.logger.debug("Disconnecting from Redis")
            await self.client.close()
            self.logger.info("Disconnected from Redis")
    
    async def publish(
        self, 
        channel: str, 
        sender: str,
        action: str,
        payload: Dict[str, Any]
    ) -> int:
        """Publish a message to a channel.
        
        Args:
            channel: Channel to publish to.
            sender: Name of the sender.
            action: Type of action.
            payload: Message payload.
            
        Returns:
            Number of clients that received the message.
        """
        if not self.client:
            await self.connect()
        
        message = {
            "sender": sender,
            "action": action,
            "payload": payload
        }
        
        try:
            message_json = json.dumps(message)
            result = await self.client.publish(channel, message_json)
            self.logger.debug(f"Published to {channel}: {action}")
            return result
        except (redis.RedisError, TypeError) as e:
            self.logger.error(f"Failed to publish to {channel}: {e}")
            raise
    
    async def subscribe(
        self,
        channels: List[str],
        callback: Callable[[str, Dict[str, Any]], Any]
    ) -> None:
        """Subscribe to channels and process messages with a callback.
        
        Args:
            channels: List of channels to subscribe to.
            callback: Async function to call for each message.
        """
        if not self.client:
            await self.connect()
        
        pubsub = self.client.pubsub()
        
        try:
            await pubsub.subscribe(*channels)
            self.logger.info(f"Subscribed to channels: {', '.join(channels)}")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"].decode("utf-8")
                    data = json.loads(message["data"].decode("utf-8"))
                    
                    self.logger.debug(f"Received on {channel}: {data['action']}")
                    
                    # Process with callback
                    await callback(channel, data)
                    
        except asyncio.CancelledError:
            self.logger.info("Subscription was canceled")
            # Clean up on cancellation
            await pubsub.unsubscribe()
            await pubsub.close()
            raise
        except Exception as e:
            self.logger.error(f"Error in subscription: {e}", exc_info=True)
            await pubsub.unsubscribe()
            await pubsub.close()
            raise