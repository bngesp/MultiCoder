"""MCP Bus module.

This module provides the Message Communication Protocol bus for MultiCoder.
It implements a publisher-subscriber pattern in memory without external dependencies.
"""
import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Set

from utils.logging import configure_logger


class MessageBus:
    """Central message bus for inter-agent communication.
    
    This is a singleton class that manages message routing between
    agents using an in-memory event bus pattern.
    
    Attributes:
        _instance: Singleton instance
        _subscriptions: Mapping of channels to sets of callback functions
        _message_queue: Queue of messages waiting to be processed
        _logger: Logger instance
        _stop_event: Event to signal the message loop to stop
        _loop_task: Task for the message processing loop
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Create or return singleton instance."""
        if cls._instance is None:
            cls._instance = super(MessageBus, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, log_level: str = "INFO"):
        """Initialize the message bus.
        
        Args:
            log_level: Logging level
        """
        # Only initialize once (singleton)
        if self._initialized:
            return
            
        self._subscriptions: Dict[str, Set[Callable]] = {}
        self._message_queue = asyncio.Queue()
        self._logger = configure_logger("mcp.bus", log_level)
        self._stop_event = asyncio.Event()
        self._loop_task = None
        self._initialized = True
        
        self._logger.info("MCP Bus initialized")
    
    async def start(self) -> None:
        """Start the message bus processing loop."""
        if self._loop_task is not None:
            self._logger.warning("Message bus already running")
            return
            
        self._logger.info("Starting MCP Bus")
        self._stop_event.clear()
        self._loop_task = asyncio.create_task(self._process_messages())
    
    async def stop(self) -> None:
        """Stop the message bus."""
        if self._loop_task is None:
            self._logger.warning("Message bus not running")
            return
            
        self._logger.info("Stopping MCP Bus")
        self._stop_event.set()
        
        # Wait for the loop to finish
        await self._loop_task
        self._loop_task = None
        
        # Clear any remaining messages
        while not self._message_queue.empty():
            try:
                self._message_queue.get_nowait()
                self._message_queue.task_done()
            except asyncio.QueueEmpty:
                break
                
        self._logger.info("MCP Bus stopped")
    
    async def subscribe(self, channel: str, callback: Callable) -> None:
        """Subscribe to a channel.
        
        Args:
            channel: Channel name to subscribe to
            callback: Async function to call when a message is received
        """
        if channel not in self._subscriptions:
            self._subscriptions[channel] = set()
            
        self._subscriptions[channel].add(callback)
        self._logger.debug(f"Added subscription to channel: {channel}")
    
    async def unsubscribe(self, channel: str, callback: Callable) -> None:
        """Unsubscribe from a channel.
        
        Args:
            channel: Channel name to unsubscribe from
            callback: Callback function to remove
        """
        if channel in self._subscriptions and callback in self._subscriptions[channel]:
            self._subscriptions[channel].remove(callback)
            
            # Clean up empty sets
            if not self._subscriptions[channel]:
                del self._subscriptions[channel]
                
            self._logger.debug(f"Removed subscription from channel: {channel}")
    
    async def publish(
        self,
        channel: str,
        sender: str,
        action: str,
        payload: Dict[str, Any]
    ) -> None:
        """Publish a message to a channel.
        
        Args:
            channel: Channel to publish to
            sender: Name of the sender
            action: Type of action
            payload: Message payload
        """
        message = {
            "channel": channel,
            "data": {
                "sender": sender,
                "action": action,
                "payload": payload
            }
        }
        
        await self._message_queue.put(message)
        self._logger.debug(f"Published message to {channel}: {action}")
    
    async def _process_messages(self) -> None:
        """Process messages from the queue."""
        self._logger.info("Message processing loop started")
        
        try:
            while not self._stop_event.is_set():
                # Get next message with timeout to periodically check stop event
                try:
                    message = await asyncio.wait_for(
                        self._message_queue.get(),
                        timeout=0.1
                    )
                except asyncio.TimeoutError:
                    continue
                
                channel = message["channel"]
                data = message["data"]
                
                # Process message
                if channel in self._subscriptions:
                    subscribers = list(self._subscriptions[channel])
                    subscription_tasks = []
                    
                    for callback in subscribers:
                        task = asyncio.create_task(callback(channel, data))
                        subscription_tasks.append(task)
                    
                    # Wait for all subscribers to process the message
                    if subscription_tasks:
                        await asyncio.gather(*subscription_tasks, return_exceptions=True)
                
                # Mark message as processed
                self._message_queue.task_done()
                
        except asyncio.CancelledError:
            self._logger.info("Message processing loop cancelled")
        except Exception as e:
            self._logger.error(f"Error in message processing loop: {e}", exc_info=True)
        finally:
            self._logger.info("Message processing loop stopped")


# Singleton instance
message_bus = MessageBus()