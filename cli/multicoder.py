"""MultiCoder CLI module.

This module provides the command-line interface for interacting
with the MultiCoder system.
"""
import argparse
import asyncio
import json
import logging
import os
import sys
import uuid
from typing import Any, Dict, Optional

# Ajouter le répertoire parent au chemin de recherche de Python
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import redis.asyncio as redis


class MultiCoderCLI:
    """Command-line interface for MultiCoder.
    
    Provides a user-friendly CLI for submitting code generation requests
    and displaying results.
    
    Attributes:
        redis_url: Redis connection string.
        request_channel: Channel to publish requests.
        response_channel: Channel to subscribe for responses.
        logger: Configured logger instance.
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        log_level: int = logging.INFO
    ) -> None:
        """Initialize the CLI client.
        
        Args:
            redis_url: Redis connection string.
            log_level: Logging level.
        """
        self.redis_url = redis_url
        self.request_channel = "multicoder:requests"
        self.response_channel = "multicoder:responses"
        
        # Setup logging
        self.logger = logging.getLogger("multicoder.cli")
        self.logger.setLevel(log_level)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Redis connection will be initialized in the run method
        self.redis_client = None
        self.pubsub = None
    
    async def send_request(self, prompt: str) -> str:
        """Send a code generation request and wait for response.
        
        Args:
            prompt: Natural language prompt describing the code to generate.
            
        Returns:
            Request ID for tracking.
        """
        request_id = str(uuid.uuid4())
        
        # Create request message
        message = {
            "sender": "cli",
            "action": "process",
            "payload": {
                "request_id": request_id,
                "prompt": prompt
            }
        }
        
        # Publish request
        message_json = json.dumps(message)
        await self.redis_client.publish(self.request_channel, message_json)
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
        self.logger.info(f"Waiting for response to request {request_id}")
        
        # Subscribe to responses
        await self.pubsub.subscribe(self.response_channel)
        
        # Set timeout
        end_time = asyncio.get_event_loop().time() + timeout
        
        try:
            while asyncio.get_event_loop().time() < end_time:
                message = await self.pubsub.get_message(timeout=1)
                
                if message and message["type"] == "message":
                    data = json.loads(message["data"].decode("utf-8"))
                    response_id = data.get("payload", {}).get("request_id")
                    
                    if response_id == request_id:
                        self.logger.info(f"Received response for request {request_id}")
                        return data.get("payload", {})
                
                # Small delay to prevent CPU spinning
                await asyncio.sleep(0.1)
            
            self.logger.warning(f"Timed out waiting for response to {request_id}")
            return None
            
        finally:
            # Unsubscribe from responses
            await self.pubsub.unsubscribe(self.response_channel)
    
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
        """Run the CLI in interactive mode."""
        print("\n🤖 MultiCoder Interactive Mode")
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
        """Run the CLI client.
        
        Args:
            prompt: Optional prompt to process in non-interactive mode.
        """
        try:
            # Initialize Redis connection
            self.redis_client = redis.Redis.from_url(self.redis_url)
            self.pubsub = self.redis_client.pubsub()
            
            if prompt:
                # Process a single prompt
                await self.process_prompt(prompt)
            else:
                # Interactive mode
                await self.interactive_mode()
                
        finally:
            # Clean up
            if self.pubsub:
                await self.pubsub.close()
            if self.redis_client:
                await self.redis_client.close()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="MultiCoder: AI-powered code generation")
    parser.add_argument(
        "--prompt", "-p",
        type=str,
        help="Prompt for code generation (non-interactive mode)"
    )
    parser.add_argument(
        "--redis-url",
        type=str,
        default="redis://localhost:6379/0",
        help="Redis connection URL (default: redis://localhost:6379/0)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    
    return parser.parse_args()


async def main() -> None:
    """Main entry point for the CLI."""
    args = parse_args()
    
    # Configure logging
    log_level = getattr(logging, args.log_level)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run CLI
    cli = MultiCoderCLI(redis_url=args.redis_url, log_level=log_level)
    await cli.run(args.prompt)


if __name__ == "__main__":
    asyncio.run(main())