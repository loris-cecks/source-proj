# sanitize_filename.py
import re
import html

class FilenameSanitizer:
    @staticmethod
    def sanitize(filename: str) -> str:
        """
        Sanitize filename by:
        1. Decoding HTML entities
        2. Removing/replacing invalid characters
        3. Trimming excess whitespace
        """
        # Decode HTML entities
        filename = html.unescape(filename)
        
        # Replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '-', filename)
        
        # Trim whitespace and dots
        filename = filename.strip('. ')
        
        # Ensure filename doesn't exceed max length (255 chars is common limit)
        if len(filename) > 255:
            filename = filename[:255]
        
        return filename