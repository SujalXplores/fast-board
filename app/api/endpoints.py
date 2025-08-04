"""
REST API endpoints for FastBoard application.
Handles HTTP requests including AI assistance and health checks.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AIServiceException, RateLimitException
from app.core.logging import get_logger
from app.models.schemas import AIAssistRequest, AIAssistResponse
from app.services.ai_service import AIService
from app.utils.helpers import get_client_ip, RateLimiter

logger = get_logger("api_endpoints")

router = APIRouter(prefix=settings.api_v1_prefix)

# Rate limiter for AI requests
ai_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


def get_ai_service() -> AIService:
    """Dependency to get the AI service instance."""
    return ai_service


# Global AI service instance
ai_service = AIService()


@router.post("/ai-assist", response_model=AIAssistResponse)
async def ai_assist(
    request: Request,
    request_data: AIAssistRequest,
    ai_svc: AIService = Depends(get_ai_service)
) -> AIAssistResponse:
    """
    AI Assist endpoint - sends canvas data to OpenAI's GPT-4 Vision model.
    
    Args:
        request: FastAPI request object
        request_data: Canvas image data for analysis
        ai_svc: AI service instance
    
    Returns:
        AI interpretation response
    
    Raises:
        HTTPException: For various error conditions
    """
    client_ip = get_client_ip(request)
    identifier = client_ip or "unknown"
    
    # Rate limiting
    if not ai_rate_limiter.is_allowed(identifier):
        logger.warning(f"Rate limit exceeded for AI assist from {identifier}")
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": "60"}
        )
    
    # Check if AI service is available
    if not ai_svc.is_available:
        logger.error("AI assist requested but service is not available")
        raise HTTPException(
            status_code=503,
            detail="AI service is currently unavailable. Please check configuration."
        )
    
    try:
        logger.info(f"Processing AI assist request from {identifier}")
        
        # Process the AI request - extract image data from request
        interpretation = await ai_svc.interpret_canvas(request_data.image_data)
        
        # Create successful response
        response = AIAssistResponse(
            success=True,
            interpretation=interpretation,
            error=None
        )
        
        logger.info(f"AI assist completed successfully for {identifier}")
        return response
    
    except AIServiceException as e:
        logger.error(f"AI service error for {identifier}: {e.message}")
        
        # Create error response
        response = AIAssistResponse(
            success=False,
            interpretation=None,
            error=e.message
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Unexpected error in AI assist for {identifier}: {e}")
        
        # Create error response for unexpected errors
        response = AIAssistResponse(
            success=False,
            interpretation=None,
            error="An unexpected error occurred while processing your request."
        )
        
        return response


@router.get("/health")
async def health_check() -> JSONResponse:
    """
    Health check endpoint for monitoring service status.
    
    Returns:
        JSON response with service health information
    """
    try:
        # Basic health indicators
        health_data = {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "timestamp": time.time(),
        }
        
        # Check AI service health
        ai_healthy = await ai_service.health_check() if ai_service.is_available else False
        health_data["ai_service"] = {
            "available": ai_service.is_available,
            "healthy": ai_healthy
        }
        
        # Determine overall status
        overall_status = "healthy" if ai_healthy or not ai_service.is_available else "degraded"
        health_data["status"] = overall_status
        
        status_code = 200 if overall_status == "healthy" else 503
        
        return JSONResponse(
            content=health_data,
            status_code=status_code
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            },
            status_code=503
        )


@router.get("/info")
async def get_app_info() -> dict:
    """
    Get application information.
    
    Returns:
        Dictionary containing application information
    """
    return {
        "name": settings.app_name,
        "description": settings.app_description,
        "version": settings.app_version,
        "features": {
            "ai_assist": ai_service.is_available,
            "real_time_collaboration": True,
            "canvas_drawing": True,
        },
        "limits": {
            "max_canvas_size": settings.max_canvas_size,
            "max_stroke_points": settings.max_stroke_points,
            "ai_rate_limit": f"{ai_rate_limiter.max_requests} requests per {ai_rate_limiter.window_seconds} seconds"
        }
    }


# Import time for health check timestamp
import time
