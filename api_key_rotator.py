# api_key_rotator.py
import os
from typing import Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv  # Add this import

class YouTubeAPIKeyRotator:
    def __init__(self):
        """Initialize API key rotator with keys from .env file"""
        # Add this line at the start of __init__
        load_dotenv()  # Explicitly load .env file
        
        self.current_key_index = 1
        self.max_retries = 3
        self.retry_count = 0
        print("Starting API key count...")  # Debug line
        self.max_keys = self._count_api_keys()
        print(f"Found {self.max_keys} API keys")  # Debug line
        if self.max_keys == 0:
            raise ValueError("No API keys found in .env file")
        self.youtube = None
        self._initialize_service()

    def _count_api_keys(self) -> int:
        """Count how many API keys are defined in .env file"""
        print("Checking for API keys in .env file...")  # Debug line
        count = 0
        while True:
            key = f"API_KEY_{count + 1}"
            value = os.getenv(key)
            print(f"Checking {key}: {'Found' if value else 'Not found'}")  # Debug line
            if value:
                count += 1
            else:
                break
        return count

    def _initialize_service(self):
        """Initialize YouTube service with current API key"""
        api_key = self._get_current_key()
        if not api_key:
            raise ValueError(f"API_KEY_{self.current_key_index} not found in .env file")
        self.youtube = build("youtube", "v3", developerKey=api_key)

    def _get_current_key(self) -> Optional[str]:
        """Get current API key from environment variables"""
        return os.getenv(f"API_KEY_{self.current_key_index}")

    def rotate_key(self):
        """Rotate to next available API key"""
        if self.retry_count >= self.max_retries:
            self.retry_count = 0
            raise ValueError("All API keys are invalid or quota exceeded")
            
        self.current_key_index = (self.current_key_index % self.max_keys) + 1
        self.retry_count += 1
        
        try:
            self._initialize_service()
            self.retry_count = 0  # Reset counter on successful initialization
        except Exception as e:
            self.rotate_key()

    def execute_with_rotation(self, request):
        """Execute a YouTube API request with automatic key rotation on quota exceeded"""
        try:
            return request.execute()
        except HttpError as e:
            if "quota" in str(e).lower():
                print("Quota exceeded, trying next API key...")
                self.rotate_key()
                return self.execute_with_rotation(request)
            raise

    @property
    def service(self):
        """Get current YouTube service instance"""
        return self.youtube