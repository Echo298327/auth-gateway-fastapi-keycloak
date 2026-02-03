import functools
from typing import Dict, Any, Callable
from auth_gateway_serverkit.logger import init_logger

logger = init_logger(__name__)


def exception_handler(default_error_message: str = "An unexpected error occurred"):
    """
    Decorator to handle exceptions in async service functions.

    Args:
        default_error_message: Default error message if none provided

    Returns:
        Decorated function that handles exceptions and returns consistent response format
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Dict[str, Any]:
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                # use logger to log the actual exception details and return a generic error message for clients
                error_msg = str(e) if str(e) else f"Unknown error of type {type(e).__name__}"
                logger.exception(f"Error in {func.__name__}: {error_msg}")
                return {
                    "status": "failed",
                    "message": default_error_message
                }

        return wrapper

    return decorator
