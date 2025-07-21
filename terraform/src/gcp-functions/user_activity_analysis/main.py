"""
Main Cloud Function entry point for User Activity Analysis.

This module provides the HTTP trigger handler for Cloud Scheduler that orchestrates
the complete user activity analysis workflow. It implements comprehensive error
handling, logging, request validation, and CORS support.

Requirements implemented:
- 1.1: HTTP trigger handler for Cloud Scheduler
- 1.3: Complete within 15 minutes to avoid overlapping executions
- 1.4: Comprehensive error handling and logging
- 8.1: Log start time, user count, and processing summary
- 8.4: CORS handling for HTTP requests
"""

import json
import logging
import os
import sys
import traceback
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import signal

import functions_framework

# Add parent directory to path for absolute imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Use absolute imports from the package root
from shared.cloud_sql_client import get_cloud_sql_client, close_cloud_sql_client
from user_activity_analysis.user_activity_analyzer import UserActivityAnalyzer

# ConfigManager removed - using simplified AI service

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global variables for graceful shutdown
_shutdown_requested = False
_current_analyzer: Optional[UserActivityAnalyzer] = None


def signal_handler(signum, frame):
    """Handle shutdown signals for graceful termination."""
    global _shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    _shutdown_requested = True


# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def run_async_safely(coro):
    """
    Run an async coroutine safely, handling both new and existing event loops.

    This function checks if there's already a running event loop and handles
    the coroutine execution appropriately for both Cloud Functions runtime
    and local testing environments.
    """
    try:
        # Try to get the current event loop
        loop = asyncio.get_running_loop()
        # If we're here, there's already a running loop (e.g., in tests)
        # We need to create a task and await it properly
        import concurrent.futures
        import threading

        # Run the coroutine in a new thread with its own event loop
        def run_in_thread():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()

    except RuntimeError:
        # No running loop, safe to use asyncio.run()
        return asyncio.run(coro)


def validate_request(request) -> Dict[str, Any]:
    """
    Validate incoming request for user activity analysis.

    Args:
        request: Flask request object

    Returns:
        Dictionary with validated request parameters

    Raises:
        ValueError: If request validation fails

    Requirements: Request validation for Cloud Scheduler
    """
    # For Cloud Scheduler, we expect either empty body or minimal configuration
    request_json = request.get_json(silent=True) or {}

    # Validate optional parameters
    config = {
        "post_threshold": request_json.get("post_threshold", 5),
        "message_threshold": request_json.get("message_threshold", 10),
        "batch_timeout_minutes": request_json.get("batch_timeout_minutes", 15),
        "max_users_per_batch": request_json.get("max_users_per_batch", 100),
    }

    # Validate thresholds
    if not isinstance(config["post_threshold"], int) or config["post_threshold"] < 1:
        raise ValueError("post_threshold must be a positive integer")

    if (
        not isinstance(config["message_threshold"], int)
        or config["message_threshold"] < 1
    ):
        raise ValueError("message_threshold must be a positive integer")

    if (
        not isinstance(config["batch_timeout_minutes"], int)
        or config["batch_timeout_minutes"] < 1
    ):
        raise ValueError("batch_timeout_minutes must be a positive integer")

    if (
        not isinstance(config["max_users_per_batch"], int)
        or config["max_users_per_batch"] < 1
    ):
        raise ValueError("max_users_per_batch must be a positive integer")

    logger.info(f"Request validated with config: {config}")
    return config


def handle_cors(request):
    """
    Handle CORS preflight requests.

    Args:
        request: Flask request object

    Returns:
        CORS response tuple or None if not a preflight request

    Requirements: 8.4 - CORS handling
    """
    if request.method == "OPTIONS":
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "3600",
        }
        return ("", 204, headers)

    return None


def get_response_headers() -> Dict[str, str]:
    """Get standard response headers including CORS."""
    return {"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}


async def execute_analysis_with_timeout(
    analyzer: UserActivityAnalyzer, timeout_minutes: int
) -> Dict[str, Any]:
    """
    Execute analysis with timeout handling.

    Args:
        analyzer: UserActivityAnalyzer instance
        timeout_minutes: Maximum execution time in minutes

    Returns:
        Analysis result dictionary

    Raises:
        asyncio.TimeoutError: If analysis exceeds timeout

    Requirements: 1.3 - Complete within 15 minutes timeout
    """
    global _shutdown_requested

    timeout_seconds = timeout_minutes * 60

    try:
        # Execute analysis with timeout
        result = await asyncio.wait_for(
            analyzer.analyze_user_activity(), timeout=timeout_seconds
        )

        return {"success": True, "result": result, "timeout_exceeded": False}

    except asyncio.TimeoutError:
        logger.error(f"Analysis timed out after {timeout_minutes} minutes")
        _shutdown_requested = True

        return {
            "success": False,
            "error": f"Analysis timed out after {timeout_minutes} minutes",
            "timeout_exceeded": True,
        }

    except Exception as e:
        logger.error(f"Analysis failed with error: {e}", exc_info=True)

        return {"success": False, "error": str(e), "timeout_exceeded": False}


def create_success_response(analysis_result) -> Dict[str, Any]:
    """
    Create success response from analysis result.

    Args:
        analysis_result: BatchAnalysisResult from analyzer

    Returns:
        Success response dictionary

    Requirements: 8.1 - Processing summary logging
    """
    # Convert dataclass to dict for JSON serialization
    result_dict = {
        "total_users_processed": analysis_result.total_users_processed,
        "successful_analyses": analysis_result.successful_analyses,
        "failed_analyses": analysis_result.failed_analyses,
        "skipped_analyses": analysis_result.skipped_analyses,
        "total_processing_time_seconds": analysis_result.total_processing_time_seconds,
        "start_time": analysis_result.start_time.isoformat(),
        "end_time": analysis_result.end_time.isoformat(),
        "error_summary": analysis_result.error_summary,
        "user_results_count": len(analysis_result.user_results),
    }

    return {
        "success": True,
        "message": "User activity analysis completed successfully",
        "analysis_summary": result_dict,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def create_error_response(
    error_message: str, error_type: str = "analysis_error"
) -> Dict[str, Any]:
    """
    Create error response with proper structure.

    Args:
        error_message: Error message to include
        error_type: Type of error for categorization

    Returns:
        Error response dictionary

    Requirements: 1.4 - Comprehensive error handling
    """
    return {
        "success": False,
        "error": error_message,
        "error_type": error_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def cleanup_resources(db_client, analyzer: Optional[UserActivityAnalyzer] = None):
    """
    Clean up resources with proper error handling.

    Args:
        db_client: Database client to close
        analyzer: Optional analyzer instance to clean up

    Requirements: Proper cleanup for async execution wrapper
    """
    try:
        if analyzer:
            # Any analyzer-specific cleanup would go here
            logger.debug("Analyzer cleanup completed")

        if db_client:
            db_client.close()
            logger.debug("Database client closed")

    except Exception as e:
        logger.warning(f"Error during cleanup: {e}")


@functions_framework.http
def user_activity_analysis(request):
    """
    Main Cloud Function entry point for user activity analysis.

    This function is triggered by Cloud Scheduler to perform automated
    user activity analysis. It orchestrates the complete workflow including
    user identification, content analysis, and result storage.

    Expected request:
    - Method: POST (from Cloud Scheduler)
    - Body: Optional JSON with configuration parameters

    Response:
    - Success: Analysis summary with metrics
    - Error: Error details with appropriate HTTP status

    Requirements:
    - 1.1: HTTP trigger handler for Cloud Scheduler
    - 1.3: Complete within 15 minutes to avoid overlapping executions
    - 1.4: Comprehensive error handling and logging
    - 8.1: Log start time, user count, and processing summary
    - 8.4: CORS handling
    """
    global _current_analyzer

    # Handle CORS preflight requests
    cors_response = handle_cors(request)
    if cors_response:
        return cors_response

    headers = get_response_headers()
    start_time = datetime.now(timezone.utc)

    logger.info(f"User activity analysis function started at {start_time}")

    db_client = None
    analyzer = None

    try:
        # Validate request
        try:
            config = validate_request(request)
        except ValueError as e:
            logger.error(f"Request validation failed: {e}")
            return (
                json.dumps(create_error_response(str(e), "validation_error")),
                400,
                headers,
            )

        # Initialize database client
        try:
            db_client = get_cloud_sql_client()
            logger.info("Database client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database client: {e}")
            return (
                json.dumps(
                    create_error_response(
                        f"Database initialization failed: {str(e)}", "database_error"
                    )
                ),
                500,
                headers,
            )

        # Configuration is now handled by the AI service directly

        # Initialize analyzer
        try:
            analyzer = UserActivityAnalyzer(
                db_client=db_client,
                post_threshold=config["post_threshold"],
                message_threshold=config["message_threshold"],
                batch_timeout_minutes=config["batch_timeout_minutes"],
            )
            _current_analyzer = analyzer
            logger.info(
                f"User activity analyzer initialized with thresholds: posts={config['post_threshold']}, messages={config['message_threshold']}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize analyzer: {e}")
            return (
                json.dumps(
                    create_error_response(
                        f"Analyzer initialization failed: {str(e)}", "analyzer_error"
                    )
                ),
                500,
                headers,
            )

        # Execute analysis with timeout
        try:
            logger.info("Starting user activity analysis execution")

            analysis_execution = execute_analysis_with_timeout(
                analyzer, config["batch_timeout_minutes"]
            )

            execution_result = run_async_safely(analysis_execution)

            if execution_result["success"]:
                analysis_result = execution_result["result"]

                # Log comprehensive summary
                logger.info(
                    f"Analysis completed successfully: "
                    f"{analysis_result.successful_analyses} successful, "
                    f"{analysis_result.failed_analyses} failed, "
                    f"{analysis_result.skipped_analyses} skipped out of "
                    f"{analysis_result.total_users_processed} total users"
                )

                response_data = create_success_response(analysis_result)

                return (json.dumps(response_data), 200, headers)

            else:
                # Analysis failed or timed out
                error_message = execution_result["error"]
                timeout_exceeded = execution_result.get("timeout_exceeded", False)

                if timeout_exceeded:
                    logger.error(f"Analysis execution timed out: {error_message}")
                    status_code = 408  # Request Timeout
                    error_type = "timeout_error"
                else:
                    logger.error(f"Analysis execution failed: {error_message}")
                    status_code = 500
                    error_type = "execution_error"

                return (
                    json.dumps(create_error_response(error_message, error_type)),
                    status_code,
                    headers,
                )

        except Exception as e:
            logger.error(
                f"Critical error during analysis execution: {e}", exc_info=True
            )
            return (
                json.dumps(
                    create_error_response(
                        f"Critical execution error: {str(e)}", "critical_error"
                    )
                ),
                500,
                headers,
            )

    except Exception as e:
        # Catch-all for any unexpected errors
        logger.error(
            f"Unexpected error in user activity analysis function: {e}", exc_info=True
        )
        logger.error(f"Full traceback: {traceback.format_exc()}")

        return (
            json.dumps(
                create_error_response(f"Unexpected error: {str(e)}", "unexpected_error")
            ),
            500,
            headers,
        )

    finally:
        # Cleanup resources
        end_time = datetime.now(timezone.utc)
        total_time = (end_time - start_time).total_seconds()

        logger.info(f"Function execution completed in {total_time:.2f} seconds")

        # Perform cleanup
        run_async_safely(cleanup_resources(db_client, analyzer))

        # Reset global state
        _current_analyzer = None

        logger.info("Resource cleanup completed")


# Health check endpoint for monitoring
@functions_framework.http
def health_check(request):
    """
    Health check endpoint for monitoring and alerting.

    Returns basic system status and configuration information.
    """
    # Handle CORS
    cors_response = handle_cors(request)
    if cors_response:
        return cors_response

    headers = get_response_headers()

    try:
        # Database connectivity check
        db_client = get_cloud_sql_client()

        # Simple query to verify database connection
        test_result = db_client.execute_query("SELECT 1 as test")

        if test_result and test_result[0]["test"] == 1:
            db_status = "healthy"
        else:
            db_status = "unhealthy"

        response = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": db_status,
            "configuration": {
                "ai_provider": "openrouter",
                "post_threshold": 5,  # Default values
                "message_threshold": 10,
            },
        }

        return (json.dumps(response), 200, headers)

    except Exception as e:
        logger.error(f"Health check failed: {e}")

        response = {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }

        return (json.dumps(response), 503, headers)

    finally:
        # Cleanup
        if "db_client" in locals():
            db_client.close()
