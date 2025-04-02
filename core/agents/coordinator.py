"""Coordinator agent module.

This module contains the Coordinator agent responsible for orchestrating
the workflow between all other agents in the system.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

from .base import Agent


class Coordinator(Agent):
    """Coordinator agent that orchestrates the workflow.
    
    This agent receives requests from the CLI, coordinates processing
    between specialized agents, and returns the final results.
    
    Attributes:
        request_channel: Channel to receive requests from CLI.
        generator_channel: Channel to communicate with code generator.
        validator_channel: Channel to communicate with code validator.
        response_channel: Channel to send responses back to CLI.
        pending_requests: Dictionary of in-progress requests.
    """
    
    def __init__(
        self,
        log_level: int = logging.INFO
    ) -> None:
        """Initialize the coordinator agent.
        
        Args:
            log_level: Logging level.
        """
        # Define channels
        self.request_channel = "multicoder:requests"
        self.generator_channel = "multicoder:generator"
        self.validator_channel = "multicoder:validator"
        self.response_channel = "multicoder:responses"
        
        # Initialize base with all channels we need to listen to
        super().__init__(
            name="coordinator",
            channels=[self.request_channel, self.generator_channel, self.validator_channel],
            log_level=log_level
        )
        
        # Track pending requests
        self.pending_requests = {}
    
    async def process_message(self, channel: str, message: Dict[str, Any]) -> None:
        """Process incoming messages based on channel and action.
        
        Args:
            channel: Channel the message was received on.
            message: The message payload.
        """
        sender = message.get("sender")
        action = message.get("action")
        payload = message.get("payload", {})
        
        self.logger.info(f"Processing {action} from {sender} on {channel}")
        
        if channel == self.request_channel:
            # New request from CLI
            if action == "process":
                await self._handle_new_request(payload)
                
        elif channel == self.generator_channel:
            # Response from code generator
            if action == "generated":
                await self._handle_generated_code(payload)
                
        elif channel == self.validator_channel:
            # Response from code validator
            if action == "validated":
                await self._handle_validated_code(payload)
    
    async def _handle_new_request(self, payload: Dict[str, Any]) -> None:
        """Handle a new request from the CLI.
        
        Args:
            payload: Request details including prompt and request_id.
        """
        request_id = payload.get("request_id")
        prompt = payload.get("prompt")
        
        if not request_id or not prompt:
            self.logger.error("Invalid request: missing request_id or prompt")
            return
        
        # Store request info
        self.pending_requests[request_id] = {
            "prompt": prompt,
            "status": "processing",
            "result": None,
        }
        
        self.logger.info(f"Processing new request {request_id}: {prompt}")
        
        # Forward to code generator
        await self.publish(
            self.generator_channel,
            "generate",
            {
                "request_id": request_id,
                "prompt": prompt
            }
        )
    
    async def _handle_generated_code(self, payload: Dict[str, Any]) -> None:
        """Handle code received from the generator.
        
        Args:
            payload: Contains generated code and request_id.
        """
        request_id = payload.get("request_id")
        code = payload.get("code")
        
        if not request_id or not code:
            self.logger.error("Invalid generator response: missing request_id or code")
            return
        
        # Update request status
        if request_id in self.pending_requests:
            self.pending_requests[request_id]["code"] = code
            self.pending_requests[request_id]["status"] = "validating"
            
            # Forward to validator
            await self.publish(
                self.validator_channel,
                "validate",
                {
                    "request_id": request_id,
                    "code": code
                }
            )
        else:
            self.logger.warning(f"Received code for unknown request: {request_id}")
    
    async def _handle_validated_code(self, payload: Dict[str, Any]) -> None:
        """Handle validation results from the validator.
        
        Args:
            payload: Validation results and request_id.
        """
        request_id = payload.get("request_id")
        is_valid = payload.get("is_valid", False)
        issues = payload.get("issues", [])
        
        if not request_id:
            self.logger.error("Invalid validator response: missing request_id")
            return
        
        if request_id in self.pending_requests:
            request = self.pending_requests[request_id]
            code = request.get("code", "")
            
            # Update request status
            if is_valid:
                request["status"] = "completed"
                request["result"] = {
                    "code": code,
                    "valid": True
                }
                self.logger.info(f"Request {request_id} completed successfully")
            else:
                request["status"] = "failed"
                request["result"] = {
                    "code": code,
                    "valid": False,
                    "issues": issues
                }
                self.logger.warning(f"Request {request_id} validation failed: {issues}")
            
            # Send response back to CLI
            await self.publish(
                self.response_channel,
                "notify",
                {
                    "request_id": request_id,
                    "status": request["status"],
                    "result": request["result"]
                }
            )
            
            # Clean up
            # We could keep a history or clean up after some time
            # but for simplicity, remove completed requests
            del self.pending_requests[request_id]
        else:
            self.logger.warning(f"Received validation for unknown request: {request_id}")