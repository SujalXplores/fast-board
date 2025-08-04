"""
FastBoard - Real-time collaborative whiteboard application
Entry point for the application using the new modular structure
"""

from app.main import app

if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload and settings.debug,
        log_level=settings.log_level.lower()
    )
