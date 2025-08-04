"""
FastBoard application factory and configuration.
Creates and configures the FastAPI application with all necessary components.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.api import endpoints, websocket


# Set up logging
setup_logging()
logger = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"AI service available: {endpoints.ai_service.is_available}")
    
    # Perform any startup tasks here
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")
    # Perform any cleanup tasks here


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    # Create FastAPI app with lifespan management
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # Add security middleware
    _add_middleware(app)
    
    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Include routers
    app.include_router(endpoints.router, tags=["API"])
    app.include_router(websocket.router, tags=["WebSocket"])
    
    # Add main routes
    _add_main_routes(app)
    
    # Add exception handlers
    _add_exception_handlers(app)
    
    logger.info("FastAPI application created and configured")
    return app


def _add_middleware(app: FastAPI) -> None:
    """Add security and utility middleware to the application."""
    
    # CORS middleware for cross-origin requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware for security
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["yourdomain.com", "www.yourdomain.com", "localhost"]
        )


def _add_main_routes(app: FastAPI) -> None:
    """Add main application routes."""
    
    # Initialize templates
    templates = Jinja2Templates(directory="templates")
    
    @app.get("/", response_class=HTMLResponse, tags=["Frontend"])
    async def read_root(request: Request) -> HTMLResponse:
        """
        Serve the main whiteboard page.
        
        Args:
            request: FastAPI request object
        
        Returns:
            HTML response with the main application template
        """
        template_context = {
            "request": request,
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "ai_available": endpoints.ai_service.is_available,
            "debug": settings.debug,
        }
        
        return templates.TemplateResponse("index.html", template_context)


def _add_exception_handlers(app: FastAPI) -> None:
    """Add custom exception handlers to the application."""
    
    from fastapi import HTTPException
    from fastapi.responses import JSONResponse
    from app.core.exceptions import FastBoardException, RateLimitException
    
    @app.exception_handler(FastBoardException)
    async def fastboard_exception_handler(request: Request, exc: FastBoardException) -> JSONResponse:
        """Handle FastBoard custom exceptions."""
        logger.error(f"FastBoard exception: {exc.message} (code: {exc.error_code})")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": exc.message,
                "detail": exc.detail,
                "code": exc.error_code,
            }
        )
    
    @app.exception_handler(RateLimitException)
    async def rate_limit_exception_handler(request: Request, exc: RateLimitException) -> JSONResponse:
        """Handle rate limit exceptions."""
        logger.warning(f"Rate limit exceeded: {exc.message}")
        
        headers = {}
        if exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)
        
        return JSONResponse(
            status_code=429,
            content={
                "error": exc.message,
                "code": exc.error_code,
            },
            headers=headers
        )
    
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle 404 errors."""
        return JSONResponse(
            status_code=404,
            content={"error": "Resource not found", "path": str(request.url.path)}
        )
    
    @app.exception_handler(500)
    async def internal_server_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle internal server errors."""
        logger.error(f"Internal server error: {exc}")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": "An unexpected error occurred" if not settings.debug else str(exc)
            }
        )


# Create the application instance
app = create_app()
