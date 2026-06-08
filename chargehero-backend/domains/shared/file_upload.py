"""File upload service for managing S3 uploads with presigned URLs."""

import logging
import mimetypes
from typing import Optional, Dict, Any
from uuid import uuid4
from datetime import timedelta

logger = logging.getLogger(__name__)

# Allowed file types for uploads
ALLOWED_PHOTO_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
ALLOWED_VIDEO_TYPES = {'video/mp4', 'video/quicktime'}
ALLOWED_SIGNATURE_TYPES = {'image/png', 'image/jpeg'}

# Size limits (in bytes)
MAX_PHOTO_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_SIGNATURE_SIZE = 5 * 1024 * 1024  # 5 MB


class FileUploadService:
    """Service for managing file uploads to Supabase Storage (S3-compatible)."""

    def __init__(self, db, bucket_name: str = 'chargehero-uploads'):
        """
        Initialize with Supabase client.

        Args:
            db: Supabase client
            bucket_name: Storage bucket name
        """
        self.db = db
        self.bucket_name = bucket_name

    def get_presigned_url_for_photo(self, ticket_id: str, photo_type: str) -> Optional[Dict[str, Any]]:
        """
        Get presigned URL for photo upload (before or after photo).

        Args:
            ticket_id: Ticket ID
            photo_type: 'before' or 'after'

        Returns:
            Dict with presigned URL and upload path, or None on error
        """
        try:
            if photo_type not in ['before', 'after']:
                raise ValueError("photo_type must be 'before' or 'after'")

            # Generate unique filename
            file_id = str(uuid4())[:8]
            file_path = f"tickets/{ticket_id}/photos/{photo_type}_{file_id}.jpg"

            # Get presigned upload URL (24 hour expiry)
            presigned_url = self.db.storage.from_(self.bucket_name).create_signed_url(
                file_path,
                expires_in=86400  # 24 hours
            )

            return {
                'presigned_url': presigned_url,
                'file_path': file_path,
                'bucket': self.bucket_name,
                'expires_in_hours': 24,
                'expected_content_type': 'image/jpeg'
            }

        except Exception as e:
            logger.error(f"Error creating presigned URL for photo: {e}")
            return None

    def get_presigned_url_for_signature(self, ticket_id: str, engineer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get presigned URL for signature upload (customer signature on completion).

        Args:
            ticket_id: Ticket ID
            engineer_id: Engineer ID

        Returns:
            Dict with presigned URL, or None on error
        """
        try:
            file_id = str(uuid4())[:8]
            file_path = f"tickets/{ticket_id}/signatures/{engineer_id}_{file_id}.png"

            presigned_url = self.db.storage.from_(self.bucket_name).create_signed_url(
                file_path,
                expires_in=86400  # 24 hours
            )

            return {
                'presigned_url': presigned_url,
                'file_path': file_path,
                'bucket': self.bucket_name,
                'expires_in_hours': 24,
                'expected_content_type': 'image/png'
            }

        except Exception as e:
            logger.error(f"Error creating presigned URL for signature: {e}")
            return None

    def get_presigned_url_for_video(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """
        Get presigned URL for video upload (KYC liveness or service video).

        Args:
            ticket_id: Ticket ID or registration ID

        Returns:
            Dict with presigned URL, or None on error
        """
        try:
            file_id = str(uuid4())[:8]
            file_path = f"videos/{ticket_id}/video_{file_id}.mp4"

            presigned_url = self.db.storage.from_(self.bucket_name).create_signed_url(
                file_path,
                expires_in=86400  # 24 hours
            )

            return {
                'presigned_url': presigned_url,
                'file_path': file_path,
                'bucket': self.bucket_name,
                'expires_in_hours': 24,
                'expected_content_type': 'video/mp4'
            }

        except Exception as e:
            logger.error(f"Error creating presigned URL for video: {e}")
            return None

    def get_presigned_url_for_document(self, user_id: str, document_type: str) -> Optional[Dict[str, Any]]:
        """
        Get presigned URL for document upload (certificates).

        Args:
            user_id: User ID
            document_type: '10th_certificate', '12th_certificate', 'iti_certificate'

        Returns:
            Dict with presigned URL, or None on error
        """
        try:
            allowed_types = ['10th_certificate', '12th_certificate', 'iti_certificate']
            if document_type not in allowed_types:
                raise ValueError(f"document_type must be one of {allowed_types}")

            file_id = str(uuid4())[:8]
            file_path = f"documents/{user_id}/{document_type}_{file_id}.pdf"

            presigned_url = self.db.storage.from_(self.bucket_name).create_signed_url(
                file_path,
                expires_in=86400  # 24 hours
            )

            return {
                'presigned_url': presigned_url,
                'file_path': file_path,
                'bucket': self.bucket_name,
                'expires_in_hours': 24,
                'expected_content_type': 'application/pdf'
            }

        except Exception as e:
            logger.error(f"Error creating presigned URL for document: {e}")
            return None

    def validate_file_size(self, file_size_bytes: int, file_type: str) -> bool:
        """
        Validate file size against limits.

        Args:
            file_size_bytes: File size in bytes
            file_type: Type of file ('photo', 'video', 'signature', 'document')

        Returns:
            True if valid, False otherwise
        """
        limits = {
            'photo': MAX_PHOTO_SIZE,
            'video': MAX_VIDEO_SIZE,
            'signature': MAX_SIGNATURE_SIZE,
            'document': MAX_PHOTO_SIZE  # Same as photo
        }

        limit = limits.get(file_type, MAX_PHOTO_SIZE)
        return file_size_bytes <= limit

    def validate_content_type(self, content_type: str, file_type: str) -> bool:
        """
        Validate content type against allowed types.

        Args:
            content_type: MIME type from request
            file_type: Type of file ('photo', 'video', 'signature', 'document')

        Returns:
            True if valid, False otherwise
        """
        allowed = {
            'photo': ALLOWED_PHOTO_TYPES,
            'video': ALLOWED_VIDEO_TYPES,
            'signature': ALLOWED_SIGNATURE_TYPES,
            'document': {'application/pdf'}
        }

        valid_types = allowed.get(file_type, ALLOWED_PHOTO_TYPES)
        return content_type in valid_types

    def get_download_url(self, file_path: str, expires_in_hours: int = 168) -> Optional[str]:
        """
        Get download URL for a file (for viewing/downloading uploaded files).

        Args:
            file_path: Path in storage bucket
            expires_in_hours: Expiration time in hours

        Returns:
            Download URL or None on error
        """
        try:
            download_url = self.db.storage.from_(self.bucket_name).create_signed_url(
                file_path,
                expires_in=expires_in_hours * 3600
            )
            return download_url
        except Exception as e:
            logger.error(f"Error creating download URL: {e}")
            return None

    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            file_path: Path to file in bucket

        Returns:
            True if deleted, False on error
        """
        try:
            self.db.storage.from_(self.bucket_name).remove([file_path])
            logger.info(f"Deleted file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False

    def get_file_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata about a file.

        Args:
            file_path: Path to file in bucket

        Returns:
            Dict with file metadata or None
        """
        try:
            # List objects matching the path
            response = self.db.storage.from_(self.bucket_name).list(file_path.rsplit('/', 1)[0])

            for item in response:
                if item.get('name') == file_path.split('/')[-1]:
                    return {
                        'name': item.get('name'),
                        'size': item.get('metadata', {}).get('size'),
                        'created_at': item.get('created_at'),
                        'updated_at': item.get('updated_at')
                    }

            return None
        except Exception as e:
            logger.error(f"Error getting file metadata: {e}")
            return None
