"""
AI service for canvas interpretation using OpenAI's GPT-4 Vision model.
Handles image analysis and provides structured responses.
"""

import asyncio
from typing import Optional
import openai
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.exceptions import AIServiceException, ConfigurationException
from app.core.logging import get_logger
from app.models.schemas import AIAssistRequest, AIAssistResponse

logger = get_logger("ai_service")


class AIService:
    """Service for AI-powered canvas interpretation."""
    
    def __init__(self) -> None:
        """Initialize the AI service."""
        self._client: Optional[AsyncOpenAI] = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the OpenAI client."""
        if not settings.openai_api_key:
            logger.warning("OpenAI API key not configured. AI features will be disabled.")
            return
        
        try:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            logger.warning("AI features will be disabled due to initialization failure.")
            self._client = None
    
    @property
    def is_available(self) -> bool:
        """Check if AI service is available."""
        return self._client is not None
    
    async def interpret_canvas(self, image_data: str) -> str:
        """
        Interpret the canvas image using OpenAI's vision model.
        
        Args:
            image_data: Base64 encoded image data
            
        Returns:
            Interpretation of the canvas content
        """
        try:
            logger.info("Processing AI assist request")
            
            # Log the image format and size for debugging
            if image_data.startswith('data:image/'):
                format_part = image_data.split(',')[0]
                logger.info(f"Image format received: {format_part}")
                # Log image data size
                image_content = image_data.split(',')[1] if ',' in image_data else image_data
                logger.info(f"Image data size: {len(image_content)} characters")
                # Log first 100 characters of base64 data
                logger.info(f"Image data sample: {image_content[:100]}...")
            
            prompt = self._create_interpretation_prompt()
            openai_response = await self._make_openai_request(prompt, image_data)
            response = self._extract_interpretation(openai_response)
            
            # Log the full response for debugging
            logger.info(f"AI raw response: {response[:500]}...")
            
            # Log response type for debugging
            if "```mermaid" in response:
                logger.warning("AI generated Mermaid diagram - possible bias detected")
            elif "```" in response:
                logger.info(f"AI generated code block with format: {response.split('```')[1].split()[0]}")
            else:
                logger.info("AI generated plain text response")
            
            logger.info("AI interpretation completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error in AI interpretation: {str(e)}")
            raise AIServiceException(f"Failed to interpret canvas: {str(e)}")
    
    def _create_interpretation_prompt(self) -> str:
        """Create the prompt for AI interpretation."""
        return (
            "You are an expert at analyzing hand-drawn images from a digital whiteboard. "
            "IMPORTANT: You must carefully examine the ACTUAL image content and respond based only on what you see.\n\n"
            
            "STEP 1 - DESCRIBE WHAT YOU SEE:\n"
            "First, describe exactly what visual elements you observe in the image:\n"
            "- Is there text? What does it say?\n"
            "- Are there shapes? What kind (circles, rectangles, arrows)?\n"
            "- Are there connections or lines between elements?\n"
            "- What is the overall layout and structure?\n\n"
            
            "STEP 2 - IDENTIFY THE CONTENT TYPE:\n"
            "Based on what you actually see, categorize it:\n"
            "- Simple text/notes/words\n"
            "- A list or bullet points\n"
            "- Mathematical expressions\n"
            "- Flowchart (boxes connected by arrows showing process flow)\n"
            "- Mind map or hierarchy\n"
            "- Drawing/sketch\n"
            "- Table/grid\n"
            "- Empty or unclear\n\n"
            
            "STEP 3 - CHOOSE OUTPUT FORMAT:\n"
            "ONLY after identifying what you actually see, choose the appropriate format:\n\n"
            
            "IF you see simple text or words → Return as plain text\n"
            "IF you see a list of items → Return as Markdown bullet points\n"
            "IF you see math equations → Return as LaTeX\n"
            "IF you see boxes connected by arrows in a process → Return as Mermaid flowchart\n"
            "IF you see a hierarchy or mind map → Return as nested Markdown\n"
            "IF you see a simple drawing → Describe it in words\n"
            "IF you see a table → Return as Markdown table\n"
            "IF unclear or empty → Say so honestly\n\n"
            
            "CRITICAL RULES:\n"
            "❌ DO NOT create Mermaid flowcharts unless you see actual boxes and arrows\n"
            "❌ DO NOT assume content is a flowchart just because it's on a whiteboard\n"
            "❌ DO NOT make up content that isn't clearly visible in the image\n"
            "✅ BE HONEST about what you can and cannot see clearly\n"
            "✅ MATCH your output format to the actual input content\n\n"
            
            "EXAMPLES:\n"
            "- Image shows 'TODO: milk, eggs, bread' → Output: Simple text list\n"
            "- Image shows boxes with arrows → Output: Mermaid flowchart\n"
            "- Image shows math equation → Output: LaTeX\n"
            "- Image shows random doodle → Output: Description\n\n"
            
            "Now analyze the image step by step:"
        )
    
    async def _make_openai_request(self, prompt: str, image_data: str) -> openai.types.chat.ChatCompletion:
        """
        Make the actual OpenAI API request.
        
        Args:
            prompt: The text prompt for analysis
            image_data: Base64 encoded image data
        
        Returns:
            The OpenAI API response
        """
        if not self._client:
            raise AIServiceException("OpenAI client not initialized")
        
        try:
            # Add timeout to prevent hanging requests
            response = await asyncio.wait_for(
                self._client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a precise image analyzer. Only describe what you actually see in the image. Do not make assumptions or create content that isn't clearly visible."
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": image_data,
                                        "detail": "high"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=settings.openai_max_tokens,
                    temperature=0.0,  # Zero temperature for maximum consistency
                    top_p=0.1,  # Low top_p for more focused responses
                    frequency_penalty=0.0,
                    presence_penalty=0.0
                ),
                timeout=30.0  # 30 second timeout
            )
            
            return response
        
        except asyncio.TimeoutError:
            logger.error("OpenAI request timed out")
            raise AIServiceException(
                "AI request timed out. Please try again.",
                error_code="AI_REQUEST_TIMEOUT"
            )
        except openai.OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            formatted_error = self._format_openai_error(e)
            raise AIServiceException(formatted_error, error_code="OPENAI_API_ERROR")
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI request: {e}")
            raise AIServiceException(f"Unexpected error: {str(e)}", error_code="UNEXPECTED_ERROR")
    
    def _extract_interpretation(self, response: openai.types.chat.ChatCompletion) -> str:
        """
        Extract the interpretation from the OpenAI response.
        
        Args:
            response: The OpenAI API response
        
        Returns:
            The extracted interpretation text
        """
        if not response.choices:
            raise AIServiceException(
                "No response choices received from AI",
                error_code="AI_NO_RESPONSE"
            )
        
        choice = response.choices[0]
        if not choice.message or not choice.message.content:
            raise AIServiceException(
                "Empty response received from AI",
                error_code="AI_EMPTY_RESPONSE"
            )
        
        interpretation = choice.message.content.strip()
        
        # Basic validation of the response
        if len(interpretation) < 10:
            raise AIServiceException(
                "AI response too short, possibly incomplete",
                error_code="AI_RESPONSE_TOO_SHORT"
            )
        
        return interpretation
    
    def _format_openai_error(self, error: openai.OpenAIError) -> str:
        """
        Format OpenAI errors for user-friendly display.
        
        Args:
            error: The OpenAI error
        
        Returns:
            Formatted error message
        """
        error_messages = {
            "insufficient_quota": "OpenAI API quota exceeded. Please check your billing settings.",
            "invalid_api_key": "Invalid OpenAI API key. Please check your configuration.",
            "rate_limit_exceeded": "OpenAI rate limit exceeded. Please try again later.",
            "model_not_found": f"OpenAI model '{settings.openai_model}' not available.",
            "context_length_exceeded": "Image or prompt too large for processing.",
        }
        
        error_type = getattr(error, 'type', 'unknown')
        return error_messages.get(error_type, f"OpenAI API error: {str(error)}")
    
    async def health_check(self) -> bool:
        """
        Perform a health check on the AI service.
        
        Returns:
            True if service is healthy, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            # Simple test request to verify API connectivity
            await asyncio.wait_for(
                self._client.models.list(),
                timeout=5.0
            )
            return True
        except Exception as e:
            logger.error(f"AI service health check failed: {e}")
            return False
