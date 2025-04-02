"""Demo script for the MultiCoder system.

This script demonstrates the MultiCoder system by running both
the server components and a client in the same process.
"""
import asyncio
import logging
import os
import sys

from core.agents import Coordinator, CodeGenerator, CodeValidator
from core.mcp.bus import message_bus

async def run_prompt(prompt: str):
    """Run a prompt through the system and display the result.
    
    Args:
        prompt: The code generation prompt.
    """
    print(f"\nProcessing prompt: {prompt}")
    print("Waiting for response...\n")
    
    # Request ID will just be a simple constant for this demo
    request_id = "demo-request"
    
    # Set up a future to get the result
    result_future = asyncio.Future()
    
    # Function to handle response
    async def handle_response(channel, message):
        action = message.get("action")
        payload = message.get("payload", {})
        
        if action == "notify" and payload.get("request_id") == request_id:
            if not result_future.done():
                result_future.set_result(payload)
    
    # Subscribe to response channel
    await message_bus.subscribe("multicoder:responses", handle_response)
    
    try:
        # Send request
        await message_bus.publish(
            "multicoder:requests",
            "demo-client",
            "process",
            {
                "request_id": request_id,
                "prompt": prompt
            }
        )
        
        # Wait for response (with timeout)
        response = await asyncio.wait_for(result_future, timeout=10.0)
        
        # Display results
        result = response.get("result", {})
        status = response.get("status", "unknown")
        
        if status == "completed":
            print("✅ Code generation successful!\n")
            code = result.get("code", "")
            print("-------- Generated Code --------")
            print(code)
            print("--------------------------------")
        else:
            print("❌ Code generation failed!\n")
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
                
    except asyncio.TimeoutError:
        print("⚠️ Request timed out. The system might be busy or experiencing issues.")
    finally:
        # Unsubscribe
        await message_bus.unsubscribe("multicoder:responses", handle_response)

async def main():
    """Run the demo."""
    # Configure simple logging
    logging.basicConfig(level=logging.WARNING)
    
    # Create and start the message bus
    await message_bus.start()
    
    # Create the agents
    coordinator = Coordinator(log_level=logging.WARNING)
    generator = CodeGenerator(log_level=logging.WARNING)
    validator = CodeValidator(log_level=logging.WARNING)
    
    # Start the agents
    await coordinator.start()
    await generator.start()
    await validator.start()
    
    print("\n🤖 MultiCoder MCP Demo\n")
    
    try:
        # Run example prompt
        await run_prompt("Crée une fonction Python qui inverse une chaîne sans utiliser [::-1]")
        
        # Run another example
        await run_prompt("Écris une fonction qui calcule la factorielle d'un nombre")
        
        print("\nDemo completed successfully!")
        
    finally:
        # Stop the agents
        await validator.stop()
        await generator.stop()
        await coordinator.stop()
        
        # Stop the message bus
        await message_bus.stop()

if __name__ == "__main__":
    asyncio.run(main())