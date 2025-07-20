"""
Tests for the main Cloud Function entry point.

This module tests the HTTP trigger handler, request validation, CORS handling,
error scenarios, and comprehensive logging functionality.

Requirements tested:
- 1.1: HTTP trigger handler for Cloud Scheduler
- 1.3: Complete within 15 minutes timeout handling
- 1.4: Comprehensive error handling and logging
- 8.1: Processing summary logging
- 8.4: CORS handling
"""

import json
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone
import sys
import os

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from user_activity_analysis.main import (
    validate_request,
    handle_cors,
    get_response_headers,
    execute_analysis_with_timeout,
    create_success_response,
    create_error_response,
    cleanup_resources,
    user_activity_analysis,
    health_check
)
from user_activity_analysis.user_activity_analyzer import BatchAnalysisResult, AnalysisStatus


class TestRequestValidation:
    """Test request validation functionality."""
    
    def test_validate_request_with_empty_body(self):
        """Test validation with empty request body (default Cloud Scheduler)."""
        mock_request = Mock()
        mock_request.get_json.return_value = None
        
        config = validate_request(mock_request)
        
        assert config['post_threshold'] == 5
        assert config['message_threshold'] == 10
        assert config['batch_timeout_minutes'] == 15
        assert config['max_users_per_batch'] == 100
    
    def test_validate_request_with_custom_config(self):
        """Test validation with custom configuration parameters."""
        mock_request = Mock()
        mock_request.get_json.return_value = {
            'post_threshold': 8,
            'message_threshold': 15,
            'batch_timeout_minutes': 10,
            'max_users_per_batch': 50
        }
        
        config = validate_request(mock_request)
        
        assert config['post_threshold'] == 8
        assert config['message_threshold'] == 15
        assert config['batch_timeout_minutes'] == 10
        assert config['max_users_per_batch'] == 50
    
    def test_validate_request_invalid_post_threshold(self):
        """Test validation with invalid post threshold."""
        mock_request = Mock()
        mock_request.get_json.return_value = {'post_threshold': 0}
        
        with pytest.raises(ValueError, match="post_threshold must be a positive integer"):
            validate_request(mock_request)
    
    def test_validate_request_invalid_message_threshold(self):
        """Test validation with invalid message threshold."""
        mock_request = Mock()
        mock_request.get_json.return_value = {'message_threshold': -1}
        
        with pytest.raises(ValueError, match="message_threshold must be a positive integer"):
            validate_request(mock_request)
    
    def test_validate_request_invalid_timeout(self):
        """Test validation with invalid timeout."""
        mock_request = Mock()
        mock_request.get_json.return_value = {'batch_timeout_minutes': 0}
        
        with pytest.raises(ValueError, match="batch_timeout_minutes must be a positive integer"):
            validate_request(mock_request)
    
    def test_validate_request_non_integer_values(self):
        """Test validation with non-integer values."""
        mock_request = Mock()
        mock_request.get_json.return_value = {'post_threshold': "invalid"}
        
        with pytest.raises(ValueError, match="post_threshold must be a positive integer"):
            validate_request(mock_request)


class TestCORSHandling:
    """Test CORS handling functionality."""
    
    def test_handle_cors_options_request(self):
        """Test CORS handling for OPTIONS preflight request."""
        mock_request = Mock()
        mock_request.method = "OPTIONS"
        
        response = handle_cors(mock_request)
        
        assert response is not None
        body, status, headers = response
        assert body == ""
        assert status == 204
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert "POST" in headers["Access-Control-Allow-Methods"]
        assert "Content-Type" in headers["Access-Control-Allow-Headers"]
    
    def test_handle_cors_non_options_request(self):
        """Test CORS handling for non-OPTIONS request."""
        mock_request = Mock()
        mock_request.method = "POST"
        
        response = handle_cors(mock_request)
        
        assert response is None
    
    def test_get_response_headers(self):
        """Test standard response headers."""
        headers = get_response_headers()
        
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert headers["Content-Type"] == "application/json"


class TestAnalysisExecution:
    """Test analysis execution with timeout handling."""
    
    @pytest.mark.asyncio
    async def test_execute_analysis_with_timeout_success(self):
        """Test successful analysis execution within timeout."""
        mock_analyzer = Mock()
        mock_result = Mock()
        mock_analyzer.analyze_user_activity = AsyncMock(return_value=mock_result)
        
        result = await execute_analysis_with_timeout(mock_analyzer, 15)
        
        assert result['success'] is True
        assert result['result'] == mock_result
        assert result['timeout_exceeded'] is False
    
    @pytest.mark.asyncio
    async def test_execute_analysis_with_timeout_exceeded(self):
        """Test analysis execution with timeout exceeded."""
        mock_analyzer = Mock()
        
        # Create a coroutine that takes longer than timeout
        async def slow_analysis():
            await asyncio.sleep(2)
            return Mock()
        
        mock_analyzer.analyze_user_activity = slow_analysis
        
        result = await execute_analysis_with_timeout(mock_analyzer, 0.001)  # Very short timeout
        
        assert result['success'] is False
        assert 'timed out' in result['error']
        assert result['timeout_exceeded'] is True
    
    @pytest.mark.asyncio
    async def test_execute_analysis_with_exception(self):
        """Test analysis execution with exception."""
        mock_analyzer = Mock()
        mock_analyzer.analyze_user_activity = AsyncMock(side_effect=Exception("Test error"))
        
        result = await execute_analysis_with_timeout(mock_analyzer, 15)
        
        assert result['success'] is False
        assert result['error'] == "Test error"
        assert result['timeout_exceeded'] is False


class TestResponseCreation:
    """Test response creation functions."""
    
    def test_create_success_response(self):
        """Test creation of success response."""
        mock_result = Mock()
        mock_result.total_users_processed = 10
        mock_result.successful_analyses = 8
        mock_result.failed_analyses = 1
        mock_result.skipped_analyses = 1
        mock_result.total_processing_time_seconds = 120.5
        mock_result.start_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_result.end_time = datetime(2024, 1, 1, 12, 2, 0, tzinfo=timezone.utc)
        mock_result.error_summary = {"timeout": 1}
        mock_result.user_results = [Mock(), Mock()]
        
        response = create_success_response(mock_result)
        
        assert response['success'] is True
        assert response['message'] == 'User activity analysis completed successfully'
        assert response['analysis_summary']['total_users_processed'] == 10
        assert response['analysis_summary']['successful_analyses'] == 8
        assert response['analysis_summary']['failed_analyses'] == 1
        assert response['analysis_summary']['skipped_analyses'] == 1
        assert response['analysis_summary']['total_processing_time_seconds'] == 120.5
        assert response['analysis_summary']['error_summary'] == {"timeout": 1}
        assert response['analysis_summary']['user_results_count'] == 2
        assert 'timestamp' in response
    
    def test_create_error_response(self):
        """Test creation of error response."""
        error_message = "Test error message"
        error_type = "test_error"
        
        response = create_error_response(error_message, error_type)
        
        assert response['success'] is False
        assert response['error'] == error_message
        assert response['error_type'] == error_type
        assert 'timestamp' in response
    
    def test_create_error_response_default_type(self):
        """Test creation of error response with default error type."""
        error_message = "Test error message"
        
        response = create_error_response(error_message)
        
        assert response['success'] is False
        assert response['error'] == error_message
        assert response['error_type'] == "analysis_error"


class TestResourceCleanup:
    """Test resource cleanup functionality."""
    
    @pytest.mark.asyncio
    async def test_cleanup_resources_success(self):
        """Test successful resource cleanup."""
        mock_db_client = Mock()
        mock_analyzer = Mock()
        
        # Should not raise any exceptions
        await cleanup_resources(mock_db_client, mock_analyzer)
        
        mock_db_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_resources_with_exception(self):
        """Test resource cleanup with exception (should not propagate)."""
        mock_db_client = Mock()
        mock_db_client.close.side_effect = Exception("Cleanup error")
        mock_analyzer = Mock()
        
        # Should not raise exception even if cleanup fails
        await cleanup_resources(mock_db_client, mock_analyzer)
        
        mock_db_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_resources_none_values(self):
        """Test resource cleanup with None values."""
        # Should not raise any exceptions
        await cleanup_resources(None, None)


class TestMainFunction:
    """Test the main Cloud Function entry point."""
    
    @patch('user_activity_analysis.main.get_cloud_sql_client')
    @patch('user_activity_analysis.main.ConfigManager')
    @patch('user_activity_analysis.main.UserActivityAnalyzer')
    @patch('user_activity_analysis.main.asyncio.run')
    def test_user_activity_analysis_success(self, mock_asyncio_run, mock_analyzer_class, 
                                          mock_config_manager, mock_get_db_client):
        """Test successful user activity analysis execution."""
        # Setup mocks
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.get_json.return_value = {}
        
        mock_db_client = Mock()
        mock_get_db_client.return_value = mock_db_client
        
        mock_config = Mock()
        mock_config_manager.return_value = mock_config
        
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock successful analysis result
        mock_batch_result = Mock()
        mock_batch_result.total_users_processed = 5
        mock_batch_result.successful_analyses = 4
        mock_batch_result.failed_analyses = 1
        mock_batch_result.skipped_analyses = 0
        mock_batch_result.total_processing_time_seconds = 60.0
        mock_batch_result.start_time = datetime.now(timezone.utc)
        mock_batch_result.end_time = datetime.now(timezone.utc)
        mock_batch_result.error_summary = {}
        mock_batch_result.user_results = []
        
        mock_execution_result = {
            'success': True,
            'result': mock_batch_result,
            'timeout_exceeded': False
        }
        mock_asyncio_run.return_value = mock_execution_result
        
        # Execute function
        response_data, status_code, headers = user_activity_analysis(mock_request)
        
        # Verify response
        assert status_code == 200
        assert headers["Access-Control-Allow-Origin"] == "*"
        
        response_json = json.loads(response_data)
        assert response_json['success'] is True
        assert 'analysis_summary' in response_json
        assert response_json['analysis_summary']['total_users_processed'] == 5
    
    def test_user_activity_analysis_cors_preflight(self):
        """Test CORS preflight request handling."""
        mock_request = Mock()
        mock_request.method = "OPTIONS"
        
        response_data, status_code, headers = user_activity_analysis(mock_request)
        
        assert status_code == 204
        assert response_data == ""
        assert headers["Access-Control-Allow-Origin"] == "*"
    
    def test_user_activity_analysis_validation_error(self):
        """Test request validation error handling."""
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.get_json.return_value = {'post_threshold': -1}
        
        response_data, status_code, headers = user_activity_analysis(mock_request)
        
        assert status_code == 400
        response_json = json.loads(response_data)
        assert response_json['success'] is False
        assert response_json['error_type'] == "validation_error"
    
    @patch('user_activity_analysis.main.get_cloud_sql_client')
    def test_user_activity_analysis_database_error(self, mock_get_db_client):
        """Test database initialization error handling."""
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.get_json.return_value = {}
        
        mock_get_db_client.side_effect = Exception("Database connection failed")
        
        response_data, status_code, headers = user_activity_analysis(mock_request)
        
        assert status_code == 500
        response_json = json.loads(response_data)
        assert response_json['success'] is False
        assert response_json['error_type'] == "database_error"
        assert "Database initialization failed" in response_json['error']
    
    @patch('user_activity_analysis.main.get_cloud_sql_client')
    @patch('user_activity_analysis.main.ConfigManager')
    def test_user_activity_analysis_config_error(self, mock_config_manager, mock_get_db_client):
        """Test configuration initialization error handling."""
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.get_json.return_value = {}
        
        mock_db_client = Mock()
        mock_get_db_client.return_value = mock_db_client
        
        mock_config_manager.side_effect = Exception("Config initialization failed")
        
        response_data, status_code, headers = user_activity_analysis(mock_request)
        
        assert status_code == 500
        response_json = json.loads(response_data)
        assert response_json['success'] is False
        assert response_json['error_type'] == "config_error"
    
    @patch('user_activity_analysis.main.get_cloud_sql_client')
    @patch('user_activity_analysis.main.ConfigManager')
    @patch('user_activity_analysis.main.UserActivityAnalyzer')
    @patch('user_activity_analysis.main.asyncio.run')
    def test_user_activity_analysis_timeout(self, mock_asyncio_run, mock_analyzer_class,
                                          mock_config_manager, mock_get_db_client):
        """Test analysis timeout handling."""
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.get_json.return_value = {}
        
        mock_db_client = Mock()
        mock_get_db_client.return_value = mock_db_client
        
        mock_config = Mock()
        mock_config_manager.return_value = mock_config
        
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock timeout result
        mock_execution_result = {
            'success': False,
            'error': 'Analysis timed out after 15 minutes',
            'timeout_exceeded': True
        }
        mock_asyncio_run.return_value = mock_execution_result
        
        response_data, status_code, headers = user_activity_analysis(mock_request)
        
        assert status_code == 408  # Request Timeout
        response_json = json.loads(response_data)
        assert response_json['success'] is False
        assert response_json['error_type'] == "timeout_error"
        assert "timed out" in response_json['error']


class TestHealthCheck:
    """Test health check endpoint."""
    
    @patch('user_activity_analysis.main.get_cloud_sql_client')
    @patch('user_activity_analysis.main.ConfigManager')
    def test_health_check_success(self, mock_config_manager, mock_get_db_client):
        """Test successful health check."""
        mock_request = Mock()
        mock_request.method = "GET"
        
        mock_db_client = Mock()
        mock_db_client.execute_query.return_value = [{'test': 1}]
        mock_get_db_client.return_value = mock_db_client
        
        mock_config = Mock()
        mock_config.ai_provider = "openai"
        mock_config_manager.return_value = mock_config
        
        response_data, status_code, headers = health_check(mock_request)
        
        assert status_code == 200
        response_json = json.loads(response_data)
        assert response_json['status'] == 'healthy'
        assert response_json['database'] == 'healthy'
        assert response_json['configuration']['ai_provider'] == 'openai'
    
    def test_health_check_cors_preflight(self):
        """Test health check CORS preflight."""
        mock_request = Mock()
        mock_request.method = "OPTIONS"
        
        response_data, status_code, headers = health_check(mock_request)
        
        assert status_code == 204
        assert response_data == ""
        assert headers["Access-Control-Allow-Origin"] == "*"
    
    @patch('user_activity_analysis.main.get_cloud_sql_client')
    def test_health_check_database_failure(self, mock_get_db_client):
        """Test health check with database failure."""
        mock_request = Mock()
        mock_request.method = "GET"
        
        mock_get_db_client.side_effect = Exception("Database connection failed")
        
        response_data, status_code, headers = health_check(mock_request)
        
        assert status_code == 503
        response_json = json.loads(response_data)
        assert response_json['status'] == 'unhealthy'
        assert 'error' in response_json


if __name__ == "__main__":
    pytest.main([__file__])