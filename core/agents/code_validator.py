"""Code Validator agent module.

This module contains the CodeValidator agent responsible for
validating generated Python code for syntax and style.
"""
import ast
import asyncio
import logging
import re
from typing import Any, Dict, List, Tuple

from .base import Agent


class CodeValidator(Agent):
    """Agent responsible for validating Python code.
    
    This agent receives code from the generator, validates it for syntax
    and style compliance, and returns validation results.
    
    Attributes:
        input_channel: Channel to receive code for validation.
        output_channel: Channel to publish validation results.
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        log_level: int = logging.INFO
    ) -> None:
        """Initialize the code validator agent.
        
        Args:
            redis_url: Redis connection string.
            log_level: Logging level.
        """
        # Define channels
        self.input_channel = "multicoder:validator"
        self.output_channel = "multicoder:validator"
        
        super().__init__(
            name="code_validator",
            redis_url=redis_url,
            channels=[self.input_channel],
            log_level=log_level
        )
    
    async def process_message(self, channel: str, message: Dict[str, Any]) -> None:
        """Process incoming code validation requests.
        
        Args:
            channel: The channel the message was received on.
            message: The message data.
        """
        action = message.get("action")
        payload = message.get("payload", {})
        
        if action == "validate":
            request_id = payload.get("request_id")
            code = payload.get("code")
            
            if not request_id or not code:
                self.logger.error("Invalid validation request: missing request_id or code")
                return
            
            self.logger.info(f"Validating code for request {request_id}")
            
            # Validate the code
            is_valid, issues = await self._validate_code(code)
            
            # Send back the validation results
            await self.publish(
                self.output_channel,
                "validated",
                {
                    "request_id": request_id,
                    "is_valid": is_valid,
                    "issues": issues
                }
            )
    
    async def _validate_code(self, code: str) -> Tuple[bool, List[str]]:
        """Validate Python code for syntax and style issues.
        
        Args:
            code: Python code to validate.
            
        Returns:
            Tuple containing:
                - Boolean indicating if code is valid
                - List of issues found (empty if valid)
        """
        issues = []
        
        # Check for syntax errors
        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append(f"Syntax error: {str(e)}")
            return False, issues
        
        # Check line length (PEP 8: 79 characters)
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if len(line) > 79:
                issues.append(f"Line {i+1} is too long ({len(line)} > 79 characters)")
        
        # Check for common style issues
        if re.search(r"^\s*import\s+\*", code, re.MULTILINE):
            issues.append("Wildcard imports (import *) are discouraged")
        
        # Check indentation consistency
        indent_sizes = set()
        for line in lines:
            if line.strip() and line[0].isspace():
                indent = len(line) - len(line.lstrip())
                if indent > 0:
                    indent_sizes.add(indent)
        
        # Commenté pour éviter les faux positifs
        # if len(indent_sizes) > 1:
        #     issues.append("Inconsistent indentation detected")
        
        # Check for docstrings
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                docstring = ast.get_docstring(node)
                if not docstring:
                    if isinstance(node, ast.FunctionDef):
                        issues.append(f"Function '{node.name}' is missing a docstring")
                    elif isinstance(node, ast.ClassDef):
                        issues.append(f"Class '{node.name}' is missing a docstring")
        
        # Consider the code valid if there are no serious issues
        is_valid = len(issues) == 0
        
        return is_valid, issues