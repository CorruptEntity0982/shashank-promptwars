"""
GCS service for handling file uploads and downloads
"""
from google.cloud import storage
from app.config import settings
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GCSService:
    """Service for Google Cloud Storage operations"""
    
    def __init__(self):
        """Initialize GCS client"""
        # GCS client uses Application Default Credentials automatically
        self.project_id = settings.gcp_project_id
        if self.project_id:
            self.client = storage.Client(project=self.project_id)
        else:
            self.client = storage.Client()
            
        self.bucket_name = settings.gcs_bucket_name
    
    @property
    def bucket(self):
        return self.client.bucket(self.bucket_name)

    def upload_file(
        self, 
        file_content: bytes, 
        file_name: str, 
        patient_id: str,
        content_type: str = "application/pdf"
    ) -> Optional[str]:
        """
        Upload file to GCS
        
        Args:
            file_content: File content as bytes
            file_name: Original file name
            patient_id: Patient ID for organizing files
            content_type: MIME type of file
            
        Returns:
            GCS blob name (key) if successful, None otherwise
        """
        try:
            # Generate GCS object name/key with organized structure
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            gcs_key = f"patients/{patient_id}/documents/{timestamp}_{file_name}"
            
            # Upload to GCS
            blob = self.bucket.blob(gcs_key)
            blob.metadata = {
                'patient_id': str(patient_id),
                'original_filename': file_name
            }
            blob.upload_from_string(file_content, content_type=content_type)
            
            logger.info(f"Successfully uploaded file to GCS: {gcs_key}")
            return gcs_key
            
        except Exception as e:
            logger.error(f"Failed to upload file to GCS: {str(e)}")
            return None
    
    def download_file(self, gcs_key: str) -> Optional[bytes]:
        """
        Download file from GCS
        
        Args:
            gcs_key: GCS blob name of the file
            
        Returns:
            File content as bytes if successful, None otherwise
        """
        try:
            logger.info(f"Downloading file from GCS: {gcs_key}")
            blob = self.bucket.blob(gcs_key)
            file_content = blob.download_as_bytes()
            logger.info(f"Successfully downloaded file: {len(file_content)} bytes")
            return file_content
            
        except Exception as e:
            logger.error(f"Failed to download file from GCS: {str(e)}")
            return None
    
    def get_file_url(self, gcs_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate presigned URL for file access
        
        Args:
            gcs_key: GCS blob name of the file
            expiration: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Presigned URL if successful, None otherwise
        """
        try:
            blob = self.bucket.blob(gcs_key)
            url = blob.generate_signed_url(
                version="v4",
                expiration=expiration,
                method="GET"
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}")
            return None


# Global GCS service instance
gcs_service = GCSService()
