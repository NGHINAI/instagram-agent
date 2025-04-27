import os
import sys
from loguru import logger

# Remove default logger
logger.remove()

# Add console logger with color formatting
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG" if os.getenv("NODE_ENV") != "production" else "INFO",
    colorize=True
)

# Add file logger
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)

logger.add(
    os.path.join(log_dir, "app.log"),
    rotation="10 MB",  # Rotate when file reaches 10 MB
    retention="1 week",  # Keep logs for 1 week
    compression="zip",  # Compress rotated logs
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG"
)

# Setup error handlers
def setup_error_handlers():
    """Set up process-level error handlers"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        # Skip KeyboardInterrupt to allow manual program termination
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.opt(exception=(exc_type, exc_value, exc_traceback)).error("Uncaught exception")
    
    def handle_unhandled_rejection(unhandled_rejection):
        logger.error(f"Unhandled rejection: {unhandled_rejection}")
    
    def handle_warning(message, category, filename, lineno, file=None, line=None):
        logger.warning(f"Warning: {message}")
    
    # Set handlers
    sys.excepthook = handle_exception
    
    # Python doesn't have direct equivalents for unhandledRejection and process.on('warning')
    # but we can use similar patterns with threading and warnings modules if needed
    import warnings
    warnings.showwarning = handle_warning

# Export the logger as default
export_default = logger