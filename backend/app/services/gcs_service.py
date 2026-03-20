"""
GCS service for handling file uploads and downloads
"""
from google.cloud import storage
from app.config import settings
import logging
from typing import Optional
from datetime import datetime
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class GCSService:
    """Service for Google Cloud Storage operations"""
    
    def __init__(self):
        """Initialize GCS client"""
        # GCS client uses Application Default Credentials automatically
        self.project_id = settings.gcp_project_id
        self.bucket_name = settings.gcs_bucket_name
        self._client = None
        self.local_storage_root = Path(getattr(settings, "local_storage_path", "/tmp/openclaims_uploads"))
    
    @property
    def client(self):
        if self._client is None:
            try:
                if self.project_id:
                    self._client = storage.Client(project=self.project_id)
                else:
                    self._client = storage.Client()
            except Exception as e:
                logger.error(f"Failed to initialize GCS client (Check GCP Credentials!): {e}")
        return self._client

    @property
    def bucket(self):
        if not self.bucket_name:
            logger.warning("GCS_BUCKET_NAME is not configured. Using local document storage fallback.")
            return None
        if not self.client:
            return None
        return self.client.bucket(self.bucket_name)

    @staticmethod
    def _sanitize_filename(file_name: str) -> str:
        base_name = Path(file_name).name or "document.pdf"
        return re.sub(r"[^A-Za-z0-9._-]", "_", base_name)

    def _build_object_key(self, patient_id: str, file_name: str) -> str:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = self._sanitize_filename(file_name)
        return f"patients/{patient_id}/documents/{timestamp}_{safe_name}"

    def _upload_file_local(self, file_content: bytes, object_key: str) -> Optional[str]:
        try:
            local_path = self.local_storage_root / object_key
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(file_content)
            local_key = f"local://{object_key}"
            logger.warning(f"Stored file locally because GCS is unavailable: {local_key}")
            return local_key
        except Exception as e:
            logger.error(f"Failed to store file locally: {str(e)}")
            return None

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
            # Generate object key with organized structure
            object_key = self._build_object_key(patient_id=patient_id, file_name=file_name)

            # Fall back to local storage when bucket/client is unavailable.
            bucket = self.bucket
            if bucket is None:
                return self._upload_file_local(file_content=file_content, object_key=object_key)

            # Upload to GCS
            blob = bucket.blob(object_key)
            blob.metadata = {
                'patient_id': str(patient_id),
                'original_filename': file_name
            }
            blob.upload_from_string(file_content, content_type=content_type)
            
            logger.info(f"Successfully uploaded file to GCS: {object_key}")
            return object_key
            
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
            if gcs_key.startswith("local://"):
                object_key = gcs_key[len("local://"):]
                local_path = self.local_storage_root / object_key
                if not local_path.exists():
                    logger.error(f"Local fallback file not found: {local_path}")
                    return None
                file_content = local_path.read_bytes()
                logger.info(f"Successfully downloaded local fallback file: {len(file_content)} bytes")
                return file_content

            logger.info(f"Downloading file from GCS: {gcs_key}")
            bucket = self.bucket
            if bucket is None:
                logger.error("GCS bucket unavailable and key is not local fallback key")
                return None

            blob = bucket.blob(gcs_key)
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
            if gcs_key.startswith("local://"):
                logger.warning("Signed URLs are not supported for local fallback storage")
                return None

            bucket = self.bucket
            if bucket is None:
                logger.error("Cannot generate signed URL because GCS bucket is unavailable")
                return None

            blob = bucket.blob(gcs_key)
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
