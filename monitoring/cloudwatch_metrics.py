import os
import boto3
import json
from datetime import datetime
from typing import Dict, Any, Optional

class CloudWatchMetrics:
    """Service for sending custom metrics to AWS CloudWatch"""
    
    def __init__(self):
        """Initialize CloudWatch client"""
        try:
            self.cloudwatch = boto3.client('cloudwatch', region_name=os.getenv('AWS_REGION', 'us-east-1'))
            self.namespace = 'MyAIGist/UserBehavior'
            self.resource_namespace = 'MyAIGist/Infrastructure'
            print("✅ CloudWatch metrics service initialized successfully")
        except Exception as e:
            print(f"⚠️ CloudWatch metrics initialization failed: {e}")
            self.cloudwatch = None
    
    def send_metric(self, metric_name: str, value: float, unit: str = 'Count', 
                   dimensions: Optional[Dict[str, str]] = None, namespace: str = None) -> bool:
        """
        Send a custom metric to CloudWatch
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement (Count, Seconds, Bytes, etc.)
            dimensions: Optional dimensions for the metric
            namespace: Optional custom namespace (defaults to UserBehavior)
        
        Returns:
            bool: Success status
        """
        if not self.cloudwatch:
            return False
        
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.utcnow()
            }
            
            if dimensions:
                metric_data['Dimensions'] = [
                    {'Name': k, 'Value': v} for k, v in dimensions.items()
                ]
            
            self.cloudwatch.put_metric_data(
                Namespace=namespace or self.namespace,
                MetricData=[metric_data]
            )
            
            print(f"📊 Sent metric: {metric_name}={value} {unit}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending metric {metric_name}: {e}")
            return False
    
    def track_content_processed(self, content_type: str, summary_level: str, 
                              processing_time: float, success: bool = True) -> None:
        """Track content processing metrics"""
        
        # Content processing count by type
        self.send_metric('ContentProcessed', 1, 'Count', {
            'ContentType': content_type,
            'SummaryLevel': summary_level,
            'Status': 'Success' if success else 'Failed'
        })
        
        # Processing time
        self.send_metric('ProcessingTime', processing_time, 'Seconds', {
            'ContentType': content_type,
            'SummaryLevel': summary_level
        })
        
        # Success/failure rate
        self.send_metric('ProcessingSuccess' if success else 'ProcessingFailure', 1, 'Count', {
            'ContentType': content_type
        })
    
    def track_question_asked(self, question_length: int, response_time: float, 
                           has_context: bool = True, success: bool = True) -> None:
        """Track Q&A system usage"""
        
        # Question count
        self.send_metric('QuestionsAsked', 1, 'Count', {
            'HasContext': 'Yes' if has_context else 'No',
            'Status': 'Success' if success else 'Failed'
        })
        
        # Question length distribution
        length_category = 'Short' if question_length < 50 else 'Medium' if question_length < 150 else 'Long'
        self.send_metric('QuestionLength', question_length, 'Count', {
            'LengthCategory': length_category
        })
        
        # Response time
        self.send_metric('QuestionResponseTime', response_time, 'Seconds', {
            'HasContext': 'Yes' if has_context else 'No'
        })
    
    def track_media_transcription(self, media_type: str, file_size: int, 
                                transcription_time: float, success: bool = True) -> None:
        """Track media file transcription"""
        
        # Media transcription count
        self.send_metric('MediaTranscribed', 1, 'Count', {
            'MediaType': media_type,
            'Status': 'Success' if success else 'Failed'
        })
        
        # File size distribution
        size_category = 'Small' if file_size < 5*1024*1024 else 'Medium' if file_size < 15*1024*1024 else 'Large'
        self.send_metric('MediaFileSize', file_size, 'Bytes', {
            'MediaType': media_type,
            'SizeCategory': size_category
        })
        
        # Transcription time
        self.send_metric('TranscriptionTime', transcription_time, 'Seconds', {
            'MediaType': media_type
        })
    
    def track_voice_usage(self, feature_type: str, duration: float = 0, success: bool = True) -> None:
        """Track voice feature usage"""
        
        # Voice feature usage
        self.send_metric('VoiceFeatureUsed', 1, 'Count', {
            'FeatureType': feature_type,  # recording, tts, etc.
            'Status': 'Success' if success else 'Failed'
        })
        
        if duration > 0:
            self.send_metric('VoiceDuration', duration, 'Seconds', {
                'FeatureType': feature_type
            })
    
    def track_batch_processing(self, batch_size: int, total_processing_time: float, 
                             content_types: list, success_count: int) -> None:
        """Track batch/multi-file processing"""
        
        # Batch processing metrics
        self.send_metric('BatchProcessed', 1, 'Count', {
            'BatchSize': str(batch_size),
            'MixedTypes': 'Yes' if len(set(content_types)) > 1 else 'No'
        })
        
        # Batch processing time
        self.send_metric('BatchProcessingTime', total_processing_time, 'Seconds', {
            'BatchSize': str(batch_size)
        })
        
        # Success rate
        success_rate = (success_count / batch_size) * 100 if batch_size > 0 else 0
        self.send_metric('BatchSuccessRate', success_rate, 'Percent', {
            'BatchSize': str(batch_size)
        })
    
    def track_embedding_operations(self, operation_type: str, chunk_count: int, 
                                 processing_time: float) -> None:
        """Track vector embedding operations"""
        
        # Embedding operations
        self.send_metric('EmbeddingOperations', 1, 'Count', {
            'OperationType': operation_type  # create, search, batch
        })
        
        # Chunk count
        self.send_metric('EmbeddingChunks', chunk_count, 'Count', {
            'OperationType': operation_type
        })
        
        # Processing time
        self.send_metric('EmbeddingProcessingTime', processing_time, 'Seconds', {
            'OperationType': operation_type
        })
    
    def track_error(self, error_type: str, error_context: str, severity: str = 'Error') -> None:
        """Track application errors"""
        
        self.send_metric('ApplicationErrors', 1, 'Count', {
            'ErrorType': error_type,
            'Context': error_context,
            'Severity': severity
        })
    
    def track_session_activity(self, activity_type: str, session_duration: float = 0) -> None:
        """Track user session activities"""
        
        # Session activities
        self.send_metric('SessionActivity', 1, 'Count', {
            'ActivityType': activity_type  # start, content_upload, question, end
        })
        
        if session_duration > 0:
            self.send_metric('SessionDuration', session_duration, 'Seconds')
    
    def track_resource_usage(self, resource_type: str, usage_value: float, unit: str) -> None:
        """Track infrastructure resource usage"""
        
        self.send_metric(f'{resource_type}Usage', usage_value, unit, 
                        namespace=self.resource_namespace)

# Global instance
metrics_service = CloudWatchMetrics()

def track_metric(metric_name: str, value: float, unit: str = 'Count', 
                dimensions: Optional[Dict[str, str]] = None) -> bool:
    """Convenience function for tracking metrics"""
    return metrics_service.send_metric(metric_name, value, unit, dimensions)