"""Code Generator agent module.

This module contains the CodeGenerator agent responsible for converting
natural language prompts into executable Python code.
"""
import asyncio
import logging
import re
from typing import Any, Dict, Optional

from .base import Agent


class CodeGenerator(Agent):
    """Agent responsible for generating Python code from prompts.
    
    This agent receives code generation requests and produces
    Python code based on natural language descriptions.
    
    Attributes:
        input_channel: Channel to receive code generation requests.
        output_channel: Channel to publish generated code.
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        log_level: int = logging.INFO
    ) -> None:
        """Initialize the code generator agent.
        
        Args:
            redis_url: Redis connection string.
            log_level: Logging level.
        """
        # Define channels
        self.input_channel = "multicoder:generator"
        self.output_channel = "multicoder:generator"
        
        super().__init__(
            name="code_generator",
            redis_url=redis_url,
            channels=[self.input_channel],
            log_level=log_level
        )
    
    async def process_message(self, channel: str, message: Dict[str, Any]) -> None:
        """Process incoming code generation requests.
        
        Args:
            channel: The channel the message was received on.
            message: The message data.
        """
        action = message.get("action")
        payload = message.get("payload", {})
        
        if action == "generate":
            request_id = payload.get("request_id")
            prompt = payload.get("prompt")
            
            if not request_id or not prompt:
                self.logger.error("Invalid generation request: missing request_id or prompt")
                return
            
            self.logger.info(f"Generating code for request {request_id}")
            
            # Generate code from prompt
            code = await self._generate_code(prompt)
            
            # Send back the generated code
            await self.publish(
                self.output_channel,
                "generated",
                {
                    "request_id": request_id,
                    "code": code
                }
            )
    
    async def _generate_code(self, prompt: str) -> str:
        """Generate Python code based on the prompt.
        
        This is a simplified implementation for MVP purposes.
        In a real system, this would use more sophisticated NLP/ML methods.
        
        Args:
            prompt: Natural language description of code to generate.
            
        Returns:
            Generated Python code as a string.
        """
        self.logger.debug(f"Generating code for prompt: {prompt}")
        
        # Simple pattern matching for MVP demonstration
        # In a real implementation, this would use a large language model
        
        # Example: "Crée une fonction Python qui inverse une chaîne sans utiliser [::-1]"
        if re.search(r"inverse.*cha[îi]ne", prompt.lower()):
            code = '''def reverse_string(s: str) -> str:
    """Reverse a string without using the slice operator.
    
    Args:
        s: The input string to reverse.
        
    Returns:
        The reversed string.
    """
    result = ""
    for char in s:
        result = char + result
    return result
'''
        else:
            # Default fallback for other prompts
            code = '''def process_data(data):
    """Process the provided data.
    
    Args:
        data: The input data to process.
        
    Returns:
        The processed result.
    """
    # TODO: Implement specific logic based on requirements
    result = data
    return result
'''
        
        return code