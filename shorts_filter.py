# shorts_filter.py
import re
from typing import Dict

class YouTubeShortsFilter:
    @staticmethod
    def is_short(video_data: Dict) -> bool:
        """
        Check if video is a Short based on YouTube API metadata.
        
        A video is considered a Short if it meets any of these criteria:
        1. Duration is 60 seconds or less
        2. Has vertical video format (aspect ratio > 1)
        3. Contains #shorts hashtag in title or description
        4. Is in Shorts URL format
        """
        try:
            content_details = video_data.get("contentDetails", {})
            snippet = video_data.get("snippet", {})
            
            # Get duration in seconds using ISO 8601 duration format
            duration = content_details.get("duration", "PT0S")
            matches = re.findall(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)[0]
            hours, minutes, seconds = [int(v) if v else 0 for v in matches]
            duration_sec = hours * 3600 + minutes * 60 + seconds
            
            # Check video dimensions for vertical format
            if "standard" in snippet.get("thumbnails", {}):
                thumb = snippet["thumbnails"]["standard"]
                aspect_ratio = thumb.get("height", 0) / thumb.get("width", 1) if thumb.get("width", 0) > 0 else 0
                is_vertical = aspect_ratio > 1
            else:
                is_vertical = False
                
            # Check for #shorts hashtag
            description = snippet.get("description", "").lower()
            title = snippet.get("title", "").lower()
            has_shorts_tag = any(
                tag in text for tag in ["#shorts", "#short", "#youtubeshorts"] 
                for text in [description, title]
            )
            
            # Check for Shorts URL format
            url = snippet.get("resourceId", {}).get("videoId", "")
            is_shorts_url = "/shorts/" in url
            
            return any([
                duration_sec <= 60,      # Max duration for Shorts
                is_vertical,             # Vertical video format
                has_shorts_tag,          # Contains Shorts hashtag
                is_shorts_url           # Uses Shorts URL format
            ])
                
        except Exception as e:
            print(f"Error checking if video is short: {str(e)}")
            return False

    @staticmethod
    def get_required_parts() -> str:
        """Return the required parts for the videos.list API call"""
        return "contentDetails,snippet,status"