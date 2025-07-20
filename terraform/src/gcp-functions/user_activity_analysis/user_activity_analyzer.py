"""
Main User Activity Analyzer orchestrator.

This module provides the UserActivityAnalyzer class that coordinates the complete
user activity analysis workflow, including user batch processing, error isolation,
comprehensive logging, and analysis result aggregation.

Requirements implemented:
- 1.1: Automated hourly job monitoring user activity
- 1.3: Complete within 15 minutes to avoid overlapping executions
- 1.4: Log detailed error information and continue processing other users
- 8.1: Log start time, user count, and processing summary
- 8.2: Log user ID, analysis type triggered, and completion status
- 8.3: Log detailed error information including user context and failure reason
"""

import logging
import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID
from dataclasses import dataclass, asdict
from enum import Enum

from .activity_threshold_checker import ActivityThresholdChecker
from .analysis_state_manager import AnalysisStateManager
from .ai_service_factory import create_ai_service, AIAnalysisService
from .config import ConfigManager
from shared.cloud_sql_client import CloudSQLClient

logger = logging.getLogger(__name__)


class AnalysisStatus(Enum):
    """Status of user analysis."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


@dataclass
class UserAnalysisResult:
    """Result of analyzing a single user."""
    user_id: UUID
    email: str
    status: AnalysisStatus
    analysis_types_performed: List[str]
    processing_time_seconds: float
    error_message: Optional[str] = None
    activity_counts: Optional[Dict[str, int]] = None
    analysis_scope: Optional[Dict[str, Any]] = None


@dataclass
class BatchAnalysisResult:
    """Result of analyzing a batch of users."""
    total_users_processed: int
    successful_analyses: int
    failed_analyses: int
    skipped_analyses: int
    total_processing_time_seconds: float
    start_time: datetime
    end_time: datetime
    user_results: List[UserAnalysisResult]
    error_summary: Dict[str, int]


class UserActivityAnalyzer:
    """
    Main orchestrator for user activity analysis.
    
    This class coordinates the complete analysis workflow:
    - Identifies users needing analysis based on activity thresholds
    - Processes users in batches with error isolation
    - Orchestrates AI analysis for writing style, topics, bio, and negative patterns
    - Aggregates results and provides comprehensive reporting
    - Implements comprehensive logging and monitoring
    
    Requirements implemented:
    - 1.1: Automated analysis workflow coordination
    - 1.3: Batch processing with timeout management
    - 1.4: Error isolation and detailed logging
    - 8.1, 8.2, 8.3: Comprehensive logging and monitoring
    """

    def __init__(
        self,
        db_client: CloudSQLClient,
        ai_service: Optional[AIAnalysisService] = None,
        post_threshold: int = 5,
        message_threshold: int = 10,
        batch_timeout_minutes: int = 15
    ):
        """
        Initialize the user activity analyzer.
        
        Args:
            db_client: Database client for data operations
            ai_service: AI analysis service (created from config if None)
            post_threshold: Minimum posts to trigger analysis
            message_threshold: Minimum messages to trigger analysis
            batch_timeout_minutes: Maximum time for batch processing
        """
        self.db_client = db_client
        self.ai_service = ai_service or create_ai_service()
        self.post_threshold = post_threshold
        self.message_threshold = message_threshold
        self.batch_timeout_seconds = batch_timeout_minutes * 60
        
        # Initialize component services
        self.threshold_checker = ActivityThresholdChecker(db_client)
        self.threshold_checker.set_thresholds(post_threshold, message_threshold)
        self.state_manager = AnalysisStateManager(db_client)
        
        # Analysis tracking
        self.analysis_start_time: Optional[datetime] = None
        self.current_batch_results: List[UserAnalysisResult] = []

    async def analyze_user_activity(self) -> BatchAnalysisResult:
        """
        Main entry point for user activity analysis.
        
        Coordinates the complete analysis workflow:
        1. Get users needing analysis based on thresholds
        2. Process users in batches with error isolation
        3. Aggregate results and generate comprehensive report
        
        Returns:
            BatchAnalysisResult with complete analysis summary
            
        Requirements: 1.1, 1.3, 1.4, 8.1
        """
        self.analysis_start_time = datetime.now(timezone.utc)
        logger.info(f"Starting user activity analysis at {self.analysis_start_time}")
        
        try:
            # Get users needing analysis
            users_for_analysis = await self.get_users_for_analysis()
            total_users = len(users_for_analysis)
            
            logger.info(f"Found {total_users} users needing analysis")
            
            if total_users == 0:
                return self._create_empty_batch_result()
            
            # Process users in batch with timeout
            batch_results = await self._process_with_timeout(users_for_analysis)
            
            # Generate final summary
            end_time = datetime.now(timezone.utc)
            processing_time = (end_time - self.analysis_start_time).total_seconds()
            
            final_result = BatchAnalysisResult(
                total_users_processed=total_users,
                successful_analyses=sum(1 for r in batch_results if r.status == AnalysisStatus.SUCCESS),
                failed_analyses=sum(1 for r in batch_results if r.status == AnalysisStatus.FAILED),
                skipped_analyses=sum(1 for r in batch_results if r.status == AnalysisStatus.SKIPPED),
                total_processing_time_seconds=processing_time,
                start_time=self.analysis_start_time,
                end_time=end_time,
                user_results=batch_results,
                error_summary=self._generate_error_summary(batch_results)
            )
            
            # Log comprehensive summary
            self._log_batch_summary(final_result)
            
            return final_result
            
        except Exception as e:
            logger.error(f"Critical error in user activity analysis: {e}", exc_info=True)
            # Return partial results if available
            end_time = datetime.now(timezone.utc)
            processing_time = (end_time - self.analysis_start_time).total_seconds()
            
            return BatchAnalysisResult(
                total_users_processed=len(self.current_batch_results),
                successful_analyses=sum(1 for r in self.current_batch_results if r.status == AnalysisStatus.SUCCESS),
                failed_analyses=sum(1 for r in self.current_batch_results if r.status == AnalysisStatus.FAILED),
                skipped_analyses=sum(1 for r in self.current_batch_results if r.status == AnalysisStatus.SKIPPED),
                total_processing_time_seconds=processing_time,
                start_time=self.analysis_start_time,
                end_time=end_time,
                user_results=self.current_batch_results,
                error_summary=self._generate_error_summary(self.current_batch_results)
            )

    async def get_users_for_analysis(self) -> List[Dict[str, Any]]:
        """
        Get users who need analysis based on activity thresholds.
        
        Returns:
            List of user data dictionaries for users needing analysis
            
        Requirements: 2.1, 2.2, 2.3, 2.4
        """
        try:
            users_needing_analysis = await self.state_manager.get_users_needing_analysis(
                self.post_threshold,
                self.message_threshold
            )
            
            logger.info(f"Threshold check found {len(users_needing_analysis)} users needing analysis")
            
            # Log breakdown by trigger type
            post_triggered = sum(1 for user in users_needing_analysis if user['post_count'] >= self.post_threshold)
            message_triggered = sum(1 for user in users_needing_analysis if user['message_count'] >= self.message_threshold)
            both_triggered = sum(1 for user in users_needing_analysis 
                               if user['post_count'] >= self.post_threshold and user['message_count'] >= self.message_threshold)
            
            logger.info(f"Analysis triggers: {post_triggered} by posts, {message_triggered} by messages, {both_triggered} by both")
            
            return users_needing_analysis
            
        except Exception as e:
            logger.error(f"Error getting users for analysis: {e}", exc_info=True)
            raise

    async def process_user_batch(self, users: List[Dict[str, Any]]) -> List[UserAnalysisResult]:
        """
        Process a batch of users with error isolation.
        
        Each user is processed independently to ensure that failures
        don't affect other users in the batch.
        
        Args:
            users: List of user data dictionaries
            
        Returns:
            List of UserAnalysisResult objects
            
        Requirements: 1.4, 8.2
        """
        results = []
        
        # Process users concurrently but with controlled concurrency
        semaphore = asyncio.Semaphore(5)  # Limit concurrent processing
        
        async def process_single_user_with_semaphore(user_data: Dict[str, Any]) -> UserAnalysisResult:
            async with semaphore:
                return await self.analyze_single_user(user_data)
        
        # Create tasks for all users
        tasks = [process_single_user_with_semaphore(user_data) for user_data in users]
        
        # Process with error isolation
        for i, task in enumerate(asyncio.as_completed(tasks)):
            try:
                result = await task
                results.append(result)
                self.current_batch_results.append(result)
                
                # Log progress
                if (i + 1) % 10 == 0 or (i + 1) == len(tasks):
                    logger.info(f"Processed {i + 1}/{len(tasks)} users")
                    
            except Exception as e:
                # This should not happen as analyze_single_user handles its own errors
                logger.error(f"Unexpected error in batch processing: {e}", exc_info=True)
                # Create a failed result for tracking
                failed_result = UserAnalysisResult(
                    user_id=UUID('00000000-0000-0000-0000-000000000000'),  # Placeholder
                    email="unknown",
                    status=AnalysisStatus.FAILED,
                    analysis_types_performed=[],
                    processing_time_seconds=0,
                    error_message=f"Batch processing error: {e}"
                )
                results.append(failed_result)
                self.current_batch_results.append(failed_result)
        
        return results

    async def analyze_single_user(self, user_data: Dict[str, Any]) -> UserAnalysisResult:
        """
        Analyze a single user with comprehensive error handling.
        
        Implements the complete individual user analysis workflow:
        1. Record analysis start
        2. Retrieve and prepare content for analysis
        3. Orchestrate AI analysis for all analysis types
        4. Store results and update user records
        5. Update analysis tracking
        
        Args:
            user_data: User data dictionary from get_users_for_analysis
            
        Returns:
            UserAnalysisResult with analysis outcome
            
        Requirements: 3.1, 3.2, 3.3, 4.1, 4.2, 5.1, 5.2, 6.1, 6.2
        """
        user_id = user_data['user_id']
        email = user_data['email']
        start_time = time.time()
        
        logger.info(f"Starting analysis for user {user_id} ({email})")
        
        try:
            # Record analysis start
            await self.state_manager.record_analysis_start(user_id)
            
            # Retrieve and prepare content for analysis
            content_data = await self._retrieve_user_content(user_id)
            
            if not self._has_sufficient_content(content_data):
                logger.info(f"User {user_id} has insufficient content for analysis")
                return UserAnalysisResult(
                    user_id=user_id,
                    email=email,
                    status=AnalysisStatus.SKIPPED,
                    analysis_types_performed=[],
                    processing_time_seconds=time.time() - start_time,
                    error_message="Insufficient content for analysis"
                )
            
            # Orchestrate AI analysis for all analysis types
            analysis_results = await self._orchestrate_ai_analysis(user_id, content_data)
            
            # Store results and update user records
            await self._store_analysis_results(user_id, analysis_results)
            
            # Update analysis tracking
            analysis_scope = self._create_analysis_scope(content_data, analysis_results)
            await self.update_analysis_tracking(user_id, {
                'analysis_scope': analysis_scope,
                'last_post_id': content_data.get('last_post_id'),
                'last_message_id': content_data.get('last_message_id')
            })
            
            processing_time = time.time() - start_time
            analysis_types = list(analysis_results.keys())
            
            logger.info(f"Successfully completed analysis for user {user_id} in {processing_time:.2f}s. Types: {analysis_types}")
            
            return UserAnalysisResult(
                user_id=user_id,
                email=email,
                status=AnalysisStatus.SUCCESS,
                analysis_types_performed=analysis_types,
                processing_time_seconds=processing_time,
                activity_counts={
                    'posts': len(content_data.get('posts', [])),
                    'messages': len(content_data.get('messages', []))
                },
                analysis_scope=analysis_scope
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_message = str(e)
            
            logger.error(f"Analysis failed for user {user_id} ({email}): {error_message}", exc_info=True)
            
            # Clean up failed analysis state
            try:
                await self.state_manager.cleanup_failed_analysis(user_id)
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup analysis state for user {user_id}: {cleanup_error}")
            
            return UserAnalysisResult(
                user_id=user_id,
                email=email,
                status=AnalysisStatus.FAILED,
                analysis_types_performed=[],
                processing_time_seconds=processing_time,
                error_message=error_message
            )

    async def _retrieve_user_content(self, user_id: UUID) -> Dict[str, Any]:
        """
        Retrieve and prepare user content for analysis.
        
        Args:
            user_id: User ID to retrieve content for
            
        Returns:
            Dictionary with user content and metadata
            
        Requirements: 1.2, 2.1, 2.2, 7.3
        """
        try:
            # Get new content since last analysis
            content = await self.state_manager.get_new_content_since_analysis(user_id)
            
            # Get current user profile data for context
            user_profile = await self._get_user_profile_data(user_id)
            
            # Separate posts by type
            scheduled_posts = []
            dismissed_posts = []
            
            for post in content['posts']:
                if post['status'] in ['scheduled', 'posted']:
                    scheduled_posts.append(post)
                elif post['status'] == 'dismissed' or post.get('user_feedback') == 'negative':
                    dismissed_posts.append(post)
            
            # Track last processed IDs for incremental processing
            last_post_id = None
            last_message_id = None
            
            if content['posts']:
                last_post_id = max(post['id'] for post in content['posts'])
            
            if content['messages']:
                last_message_id = max(msg['id'] for msg in content['messages'])
            
            return {
                'posts': content['posts'],
                'messages': content['messages'],
                'scheduled_posts': scheduled_posts,
                'dismissed_posts': dismissed_posts,
                'user_profile': user_profile,
                'last_post_id': last_post_id,
                'last_message_id': last_message_id,
                'content_counts': {
                    'total_posts': len(content['posts']),
                    'scheduled_posts': len(scheduled_posts),
                    'dismissed_posts': len(dismissed_posts),
                    'messages': len(content['messages'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error retrieving content for user {user_id}: {e}")
            raise

    async def _get_user_profile_data(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get current user profile data for analysis context.
        
        Args:
            user_id: User ID to get profile for
            
        Returns:
            Dictionary with user profile data
        """
        try:
            # Get user basic info
            user_query = """
                SELECT id, email, bio, created_at
                FROM users
                WHERE id = :user_id AND is_active = true AND deleted_at IS NULL
            """
            
            user_results = await self.db_client.execute_query_async(user_query, {"user_id": str(user_id)})
            user_data = user_results[0] if user_results else None
            
            if not user_data:
                raise ValueError(f"User {user_id} not found or inactive")
            
            # Get user preferences
            preferences_query = """
                SELECT writing_style_analysis, negative_analysis
                FROM user_preferences
                WHERE user_id = :user_id
            """
            
            pref_results = await self.db_client.execute_query_async(preferences_query, {"user_id": str(user_id)})
            preferences = pref_results[0] if pref_results else {}
            
            return {
                'user_id': UUID(user_data['id']),
                'email': user_data['email'],
                'bio': user_data['bio'],
                'created_at': user_data['created_at'],
                'writing_style_analysis': preferences.get('writing_style_analysis'),
                'negative_analysis': preferences.get('negative_analysis')
            }
            
        except Exception as e:
            logger.error(f"Error getting user profile for {user_id}: {e}")
            raise

    def _has_sufficient_content(self, content_data: Dict[str, Any]) -> bool:
        """
        Check if user has sufficient content for meaningful analysis.
        
        Args:
            content_data: Content data from _retrieve_user_content
            
        Returns:
            True if sufficient content exists for analysis
        """
        counts = content_data['content_counts']
        
        # Need at least some posts or messages for analysis
        has_posts = counts['total_posts'] >= self.post_threshold
        has_messages = counts['messages'] >= self.message_threshold
        
        # Also check for minimum content for specific analysis types
        has_scheduled_for_writing_analysis = counts['scheduled_posts'] >= 2
        has_dismissed_for_negative_analysis = counts['dismissed_posts'] >= 1
        
        return (has_posts or has_messages) and (has_scheduled_for_writing_analysis or has_dismissed_for_negative_analysis or has_messages >= 5)

    async def _orchestrate_ai_analysis(self, user_id: UUID, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate AI analysis for all applicable analysis types.
        
        Args:
            user_id: User ID being analyzed
            content_data: Content data for analysis
            
        Returns:
            Dictionary with analysis results by type
            
        Requirements: 3.1, 3.2, 3.3, 4.1, 4.2, 5.1, 5.2, 6.1, 6.2
        """
        analysis_results = {}
        user_profile = content_data['user_profile']
        
        try:
            # Writing Style Analysis (if sufficient scheduled posts)
            if len(content_data.get('scheduled_posts', [])) >= 2:
                logger.debug(f"Performing writing style analysis for user {user_id}")
                
                scheduled_content = [post['content'] for post in content_data['scheduled_posts']]
                existing_analysis = user_profile.get('writing_style_analysis')
                
                writing_style_result = await self.ai_service.analyze_writing_style(
                    content_list=scheduled_content,
                    existing_analysis=existing_analysis
                )
                
                analysis_results['writing_style'] = writing_style_result
                logger.debug(f"Writing style analysis completed for user {user_id}")
            
            # Topics of Interest Analysis (if sufficient scheduled posts)
            if len(content_data.get('scheduled_posts', [])) >= 1:
                logger.debug(f"Performing topics analysis for user {user_id}")
                
                scheduled_content = [post['content'] for post in content_data['scheduled_posts']]
                
                topics_result = await self.ai_service.analyze_topics_of_interest(scheduled_content)
                
                analysis_results['topics_of_interest'] = topics_result
                logger.debug(f"Topics analysis completed for user {user_id}")
            
            # Bio Update Analysis (if sufficient scheduled posts and existing bio)
            if len(content_data.get('scheduled_posts', [])) >= 1 and user_profile.get('bio'):
                logger.debug(f"Performing bio update analysis for user {user_id}")
                
                scheduled_content = [post['content'] for post in content_data['scheduled_posts']]
                current_bio = user_profile['bio']
                
                bio_result = await self.ai_service.update_user_bio(
                    current_bio=current_bio,
                    recent_content=scheduled_content
                )
                
                analysis_results['bio_update'] = bio_result
                logger.debug(f"Bio update analysis completed for user {user_id}")
            
            # Negative Analysis (if dismissed posts exist)
            if len(content_data.get('dismissed_posts', [])) >= 1:
                logger.debug(f"Performing negative analysis for user {user_id}")
                
                # Separate dismissed posts by feedback type
                dismissed_with_feedback = []
                dismissed_without_feedback = []
                
                for post in content_data['dismissed_posts']:
                    if post.get('user_feedback') == 'negative':
                        dismissed_with_feedback.append(post)
                    else:
                        dismissed_without_feedback.append(post)
                
                negative_result = await self.ai_service.analyze_negative_patterns(
                    dismissed_posts=dismissed_without_feedback,
                    feedback_posts=dismissed_with_feedback
                )
                
                analysis_results['negative_analysis'] = negative_result
                logger.debug(f"Negative analysis completed for user {user_id}")
            
            logger.info(f"AI analysis orchestration completed for user {user_id}. Analysis types: {list(analysis_results.keys())}")
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error in AI analysis orchestration for user {user_id}: {e}")
            raise

    async def _store_analysis_results(self, user_id: UUID, analysis_results: Dict[str, Any]) -> None:
        """
        Store analysis results in the database.
        
        Args:
            user_id: User ID to store results for
            analysis_results: Analysis results by type
            
        Requirements: 3.1, 3.2, 3.3, 4.1, 4.2, 5.1, 5.2
        """
        try:
            # Update writing style analysis if present
            if 'writing_style' in analysis_results:
                await self._update_writing_style_analysis(user_id, analysis_results['writing_style'])
            
            # Update topics of interest if present
            if 'topics_of_interest' in analysis_results:
                await self._update_topics_of_interest(user_id, analysis_results['topics_of_interest'])
            
            # Update user bio if present
            if 'bio_update' in analysis_results:
                await self._update_user_bio(user_id, analysis_results['bio_update'])
            
            # Update negative analysis if present
            if 'negative_analysis' in analysis_results:
                await self._update_negative_analysis(user_id, analysis_results['negative_analysis'])
            
            logger.debug(f"Analysis results stored for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing analysis results for user {user_id}: {e}")
            raise

    async def _update_writing_style_analysis(self, user_id: UUID, writing_style_result: str) -> None:
        """Update writing style analysis in user preferences."""
        query = """
            INSERT INTO user_preferences (user_id, writing_style_analysis, updated_at)
            VALUES (:user_id, :writing_style_analysis, NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET
                writing_style_analysis = EXCLUDED.writing_style_analysis,
                updated_at = EXCLUDED.updated_at
        """
        
        await self.db_client.execute_update_async(query, {
            "user_id": str(user_id),
            "writing_style_analysis": writing_style_result
        })

    async def _update_topics_of_interest(self, user_id: UUID, topics_result: List[Dict[str, Any]]) -> None:
        """Update topics of interest (this would typically involve a topics table)."""
        # For now, we'll store in a simple format
        # In a full implementation, this might involve a separate topics table
        logger.debug(f"Topics analysis result for user {user_id}: {len(topics_result)} topics identified")

    async def _update_user_bio(self, user_id: UUID, bio_result: str) -> None:
        """Update user bio with AI-enhanced version."""
        query = """
            UPDATE users
            SET bio = :bio, updated_at = NOW()
            WHERE id = :user_id
        """
        
        await self.db_client.execute_update_async(query, {
            "user_id": str(user_id),
            "bio": bio_result
        })

    async def _update_negative_analysis(self, user_id: UUID, negative_result: str) -> None:
        """Update negative analysis in user preferences."""
        query = """
            INSERT INTO user_preferences (user_id, negative_analysis, updated_at)
            VALUES (:user_id, :negative_analysis, NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET
                negative_analysis = EXCLUDED.negative_analysis,
                updated_at = EXCLUDED.updated_at
        """
        
        await self.db_client.execute_update_async(query, {
            "user_id": str(user_id),
            "negative_analysis": negative_result
        })

    def _create_analysis_scope(self, content_data: Dict[str, Any], analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create analysis scope record for tracking.
        
        Args:
            content_data: Content data that was analyzed
            analysis_results: Results of the analysis
            
        Returns:
            Analysis scope dictionary
            
        Requirements: 7.2
        """
        counts = content_data['content_counts']
        
        return {
            'posts_analyzed': {
                'scheduled_count': counts['scheduled_posts'],
                'dismissed_count': counts['dismissed_posts'],
                'total_count': counts['total_posts'],
                'post_ids': [str(post['id']) for post in content_data['posts']],
                'date_range': {
                    'start': min(post['created_at'] for post in content_data['posts'] if 'created_at' in post).isoformat() if content_data['posts'] and any('created_at' in post for post in content_data['posts']) else None,
                    'end': max(post['created_at'] for post in content_data['posts'] if 'created_at' in post).isoformat() if content_data['posts'] and any('created_at' in post for post in content_data['posts']) else None
                }
            },
            'messages_analyzed': {
                'total_count': counts['messages'],
                'message_ids': [str(msg['id']) for msg in content_data['messages']],
                'date_range': {
                    'start': min(msg['created_at'] for msg in content_data['messages'] if 'created_at' in msg).isoformat() if content_data['messages'] and any('created_at' in msg for msg in content_data['messages']) else None,
                    'end': max(msg['created_at'] for msg in content_data['messages'] if 'created_at' in msg).isoformat() if content_data['messages'] and any('created_at' in msg for msg in content_data['messages']) else None
                }
            },
            'analysis_types_performed': list(analysis_results.keys()),
            'analysis_timestamp': datetime.now(timezone.utc).isoformat()
        }

    async def update_analysis_tracking(self, user_id: UUID, analysis_data: Dict[str, Any]) -> None:
        """
        Update analysis tracking records after successful analysis.
        
        Args:
            user_id: User ID to update tracking for
            analysis_data: Analysis data including scope and results
            
        Requirements: 7.1, 7.2, 7.3
        """
        try:
            analysis_timestamp = datetime.now(timezone.utc)
            
            # Extract scope information from analysis data
            analysis_scope = analysis_data.get('analysis_scope', {})
            last_post_id = analysis_data.get('last_post_id')
            last_message_id = analysis_data.get('last_message_id')
            
            await self.state_manager.record_analysis_completion(
                user_id=user_id,
                analysis_timestamp=analysis_timestamp,
                analysis_scope=analysis_scope,
                last_post_id=last_post_id,
                last_message_id=last_message_id
            )
            
            logger.debug(f"Updated analysis tracking for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating analysis tracking for user {user_id}: {e}", exc_info=True)
            raise

    def _create_empty_batch_result(self) -> BatchAnalysisResult:
        """Create an empty batch result when no users need analysis."""
        end_time = datetime.now(timezone.utc)
        processing_time = (end_time - self.analysis_start_time).total_seconds()
        
        return BatchAnalysisResult(
            total_users_processed=0,
            successful_analyses=0,
            failed_analyses=0,
            skipped_analyses=0,
            total_processing_time_seconds=processing_time,
            start_time=self.analysis_start_time,
            end_time=end_time,
            user_results=[],
            error_summary={}
        )

    async def _process_with_timeout(self, users: List[Dict[str, Any]]) -> List[UserAnalysisResult]:
        """
        Process users with timeout protection.
        
        Args:
            users: List of users to process
            
        Returns:
            List of UserAnalysisResult objects
            
        Requirements: 1.3
        """
        try:
            # Process with timeout
            results = await asyncio.wait_for(
                self.process_user_batch(users),
                timeout=self.batch_timeout_seconds
            )
            return results
            
        except asyncio.TimeoutError:
            logger.error(f"Batch processing timed out after {self.batch_timeout_seconds} seconds")
            
            # Return partial results with timeout status for unprocessed users
            processed_user_ids = {result.user_id for result in self.current_batch_results}
            
            for user_data in users:
                user_id = user_data['user_id']
                if user_id not in processed_user_ids:
                    timeout_result = UserAnalysisResult(
                        user_id=user_id,
                        email=user_data['email'],
                        status=AnalysisStatus.TIMEOUT,
                        analysis_types_performed=[],
                        processing_time_seconds=self.batch_timeout_seconds,
                        error_message="Processing timed out"
                    )
                    self.current_batch_results.append(timeout_result)
            
            return self.current_batch_results

    def _generate_error_summary(self, results: List[UserAnalysisResult]) -> Dict[str, int]:
        """
        Generate error summary from batch results.
        
        Args:
            results: List of user analysis results
            
        Returns:
            Dictionary with error type counts
        """
        error_summary = {}
        
        for result in results:
            if result.status != AnalysisStatus.SUCCESS and result.error_message:
                # Categorize errors
                error_type = "unknown_error"
                error_msg = result.error_message.lower()
                
                # Check for AI service errors first (more specific)
                if ("ai service" in error_msg or "openai" in error_msg or "anthropic" in error_msg or 
                    ("ai" in error_msg and "service" in error_msg)):
                    error_type = "ai_service_error"
                elif "rate limit" in error_msg:
                    error_type = "rate_limit_error"
                elif "database" in error_msg or "sql" in error_msg or "connection" in error_msg:
                    error_type = "database_error"
                elif "timeout" in error_msg:
                    error_type = "timeout_error"
                elif "threshold" in error_msg:
                    error_type = "threshold_error"
                
                error_summary[error_type] = error_summary.get(error_type, 0) + 1
        
        return error_summary

    def _log_batch_summary(self, result: BatchAnalysisResult) -> None:
        """
        Log comprehensive batch analysis summary.
        
        Args:
            result: Batch analysis result to log
            
        Requirements: 8.1, 8.2, 8.3
        """
        # Main summary log
        logger.info(
            f"Batch analysis completed: "
            f"{result.successful_analyses} successful, "
            f"{result.failed_analyses} failed, "
            f"{result.skipped_analyses} skipped out of {result.total_users_processed} users. "
            f"Processing time: {result.total_processing_time_seconds:.2f} seconds"
        )
        
        # Success rate calculation
        if result.total_users_processed > 0:
            success_rate = (result.successful_analyses / result.total_users_processed) * 100
            logger.info(f"Analysis success rate: {success_rate:.1f}%")
        
        # Error summary
        if result.error_summary:
            logger.warning(f"Error summary: {result.error_summary}")
        
        # Performance metrics
        if result.successful_analyses > 0:
            avg_processing_time = result.total_processing_time_seconds / result.total_users_processed
            logger.info(f"Average processing time per user: {avg_processing_time:.2f} seconds")
        
        # Analysis type breakdown
        analysis_type_counts = {}
        for user_result in result.user_results:
            if user_result.status == AnalysisStatus.SUCCESS:
                for analysis_type in user_result.analysis_types_performed:
                    analysis_type_counts[analysis_type] = analysis_type_counts.get(analysis_type, 0) + 1
        
        if analysis_type_counts:
            logger.info(f"Analysis types performed: {analysis_type_counts}")
        
        # Log individual failures for debugging
        failed_users = [r for r in result.user_results if r.status == AnalysisStatus.FAILED]
        if failed_users:
            logger.warning(f"Failed analyses for users: {[str(r.user_id) for r in failed_users[:10]]}")  # Limit to first 10
            if len(failed_users) > 10:
                logger.warning(f"... and {len(failed_users) - 10} more failed analyses")

    async def get_analysis_status_summary(self) -> Dict[str, Any]:
        """
        Get current analysis status summary across all users.
        
        Returns:
            Dictionary with analysis status information
            
        Requirements: 8.1, 8.2
        """
        try:
            # Get progress summary from state manager
            progress_summary = await self.state_manager.get_analysis_progress_summary()
            
            # Get threshold summary
            threshold_summary = await self.threshold_checker.get_batch_analysis_summary(
                self.post_threshold, self.message_threshold
            )
            
            # Combine summaries
            status_summary = {
                'analysis_progress': progress_summary,
                'threshold_analysis': threshold_summary,
                'current_thresholds': self.threshold_checker.get_current_thresholds(),
                'last_check_time': datetime.now(timezone.utc).isoformat()
            }
            
            return status_summary
            
        except Exception as e:
            logger.error(f"Error getting analysis status summary: {e}", exc_info=True)
            return {
                'error': str(e),
                'last_check_time': datetime.now(timezone.utc).isoformat()
            }

    def get_batch_result_summary(self, result: BatchAnalysisResult) -> Dict[str, Any]:
        """
        Get a dictionary summary of batch analysis results.
        
        Args:
            result: BatchAnalysisResult to summarize
            
        Returns:
            Dictionary with batch result summary
        """
        return {
            'summary': {
                'total_users_processed': result.total_users_processed,
                'successful_analyses': result.successful_analyses,
                'failed_analyses': result.failed_analyses,
                'skipped_analyses': result.skipped_analyses,
                'success_rate_percent': (result.successful_analyses / result.total_users_processed * 100) if result.total_users_processed > 0 else 0,
                'total_processing_time_seconds': result.total_processing_time_seconds,
                'average_processing_time_seconds': result.total_processing_time_seconds / result.total_users_processed if result.total_users_processed > 0 else 0
            },
            'timing': {
                'start_time': result.start_time.isoformat(),
                'end_time': result.end_time.isoformat(),
                'duration_seconds': result.total_processing_time_seconds
            },
            'errors': result.error_summary,
            'analysis_types_performed': self._get_analysis_type_summary(result.user_results)
        }

    def _get_analysis_type_summary(self, user_results: List[UserAnalysisResult]) -> Dict[str, int]:
        """Get summary of analysis types performed across all users."""
        analysis_type_counts = {}
        for user_result in user_results:
            if user_result.status == AnalysisStatus.SUCCESS:
                for analysis_type in user_result.analysis_types_performed:
                    analysis_type_counts[analysis_type] = analysis_type_counts.get(analysis_type, 0) + 1
        return analysis_type_counts