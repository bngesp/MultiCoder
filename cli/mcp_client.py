"""MultiCoder MCP client.

This module provides a client to interact with the MultiCoder system
using the Message Communication Protocol (MCP).
"""
import asyncio
import json
import logging
import sys
import uuid
from typing import Any, Dict, Optional

from core.mcp.bus import message_bus
from utils.logging import configure_logger


class MCPClient:
    """Client for interacting with the MultiCoder MCP system.
    
    This client can send requests to the MultiCoder system and
    receive responses through the MCP bus.
    
    Attributes:
        request_channel: Channel to publish requests.
        response_channel: Channel to subscribe for responses.
        logger: Configured logger instance.
    """
    
    def __init__(
        self,
        log_level: str = "INFO"
    ) -> None:
        """Initialize the MCP client.
        
        Args:
            log_level: Logging level.
        """
        self.request_channel = "multicoder:requests"
        self.response_channel = "multicoder:responses"
        
        # Setup logging
        self.logger = configure_logger("multicoder.cli", log_level)
        
        # Response tracking
        self._waiting_for_responses = {}
        self._response_events = {}
    
    async def initialize(self) -> None:
        """Initialize the MCP client and start the message bus."""
        await message_bus.start()
        await message_bus.subscribe(self.response_channel, self._handle_response)
        self.logger.info("MCP client initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the MCP client and stop the message bus."""
        self.logger.info("MCP client shutting down")
        await message_bus.unsubscribe(self.response_channel, self._handle_response)
        await message_bus.stop()
    
    async def _handle_response(self, channel: str, message: Dict[str, Any]) -> None:
        """Handle responses from the MultiCoder system.
        
        Args:
            channel: The channel the message was received on.
            message: The message data.
        """
        action = message.get("action")
        payload = message.get("payload", {})
        
        if action == "notify":
            request_id = payload.get("request_id")
            
            if request_id in self._waiting_for_responses:
                self._waiting_for_responses[request_id] = payload
                
                # Signal that the response has been received
                if request_id in self._response_events:
                    self._response_events[request_id].set()
                    
                self.logger.info(f"Received response for request {request_id}")
    
    async def send_request(self, prompt: str) -> str:
        """Send a code generation request.
        
        Args:
            prompt: Natural language prompt describing the code to generate.
            
        Returns:
            Request ID for tracking.
        """
        request_id = str(uuid.uuid4())
        
        # Register that we're waiting for a response
        self._waiting_for_responses[request_id] = None
        self._response_events[request_id] = asyncio.Event()
        
        # Create request message
        await message_bus.publish(
            self.request_channel,
            "cli",
            "process",
            {
                "request_id": request_id,
                "prompt": prompt
            }
        )
        
        self.logger.info(f"Sent request {request_id}: {prompt}")
        
        return request_id
    
    async def wait_for_response(self, request_id: str, timeout: int = 60) -> Optional[Dict[str, Any]]:
        """Wait for a response to a specific request.
        
        Args:
            request_id: The ID of the request to wait for.
            timeout: Maximum time to wait in seconds.
            
        Returns:
            Response data or None if timed out.
        """
        if request_id not in self._waiting_for_responses:
            self.logger.error(f"Not waiting for request {request_id}")
            return None
            
        self.logger.info(f"Waiting for response to request {request_id}")
        
        try:
            # Wait for the response
            event = self._response_events[request_id]
            await asyncio.wait_for(event.wait(), timeout)
            
            # Get and return the response
            response = self._waiting_for_responses[request_id]
            return response
        except asyncio.TimeoutError:
            self.logger.warning(f"Timed out waiting for response to {request_id}")
            return None
        finally:
            # Clean up
            if request_id in self._waiting_for_responses:
                del self._waiting_for_responses[request_id]
            if request_id in self._response_events:
                del self._response_events[request_id]
    
    async def process_prompt(self, prompt: str, timeout: int = 60) -> None:
        """Process a prompt and display the results.
        
        Args:
            prompt: The prompt to process.
            timeout: Maximum time to wait for response.
        """
        try:
            # Send request
            request_id = await self.send_request(prompt)
            
            # Wait for and display progress
            print(f"Processing request: {prompt}")
            print("Waiting for response...", end="", flush=True)
            
            # Wait for response
            response = await self.wait_for_response(request_id, timeout)
            
            # Display results
            print("\r" + " " * 50 + "\r", end="")  # Clear waiting message
            
            if response:
                result = response.get("result", {})
                status = response.get("status", "unknown")
                
                if status == "completed":
                    print("\n✅ Code generation successful!\n")
                    code = result.get("code", "")
                    print("-------- Generated Code --------")
                    print(code)
                    print("--------------------------------")
                else:
                    print("\n❌ Code generation failed!\n")
                    issues = result.get("issues", [])
                    if issues:
                        print("Issues:")
                        for issue in issues:
                            print(f" - {issue}")
                    code = result.get("code", "")
                    if code:
                        print("\nPartial code:")
                        print("-------- Generated Code --------")
                        print(code)
                        print("--------------------------------")
            else:
                print("\n⚠️ Request timed out. The system might be busy or experiencing issues.")
                
        except Exception as e:
            self.logger.error(f"Error processing prompt: {e}", exc_info=True)
            print(f"\n❌ Error: {e}")
    
    async def interactive_mode(self) -> None:
        """Run the client in interactive mode."""
        print("\n🤖 MultiCoder (MCP) Interactive Mode")
        print("Type 'exit' or 'quit' to exit\n")
        
        while True:
            try:
                prompt = input("🔍 Enter your code request: ")
                
                if prompt.lower() in ["exit", "quit"]:
                    break
                
                if prompt:
                    await self.process_prompt(prompt)
                    print("\n")
            
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            
            except Exception as e:
                self.logger.error(f"Error in interactive mode: {e}", exc_info=True)
                print(f"❌ Error: {e}")
    
    async def run(self, prompt: Optional[str] = None) -> None:
        """Run the MCP client.
        
        Args:
            prompt: Optional prompt to process in non-interactive mode.
        """
        try:
            # Initialize client
            await self.initialize()
            
            if prompt:
                # Process a single prompt
                await self.process_prompt(prompt)
            else:
                # Interactive mode
                await self.interactive_mode()
                
        finally:
            # Clean up
            await self.shutdown()