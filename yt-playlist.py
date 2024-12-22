import os
import sys
from typing import List, Dict, Optional, Tuple
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs
from sanitize_filename import FilenameSanitizer
from api_key_rotator import YouTubeAPIKeyRotator
from process_with_tldr import process_with_tldr
import time

load_dotenv()

class YouTubePlaylistTranscriptDownloader:
    def __init__(self):
        """Initialize the downloader with required components"""
        self.api_rotator = YouTubeAPIKeyRotator()
        self.output_dir = "yt-playlists"
        self.stats = {
            "downloaded": 0,
            "skipped": 0,
            "failed": 0
        }
        self.filename_sanitizer = FilenameSanitizer()

    def _get_playlist_info(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract playlist ID and title from URL"""
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            if 'list' not in query_params:
                print("URL does not contain a valid playlist ID")
                return None, None
                
            playlist_id = query_params['list'][0]
            
            request = self.api_rotator.service.playlists().list(
                part="snippet",
                id=playlist_id
            )
            response = self.api_rotator.execute_with_rotation(request)
            
            if response.get("items"):
                return playlist_id, response["items"][0]["snippet"]["title"]
                
        except Exception as e:
            print(f"Error extracting playlist ID: {str(e)}")
            
        return None, None

    def _get_playlist_videos(self, playlist_id: str) -> List[Dict]:
        """Get all videos from the playlist"""
        videos = []
        next_page_token = None
        
        while True:
            try:
                request = self.api_rotator.service.playlistItems().list(
                    part="snippet",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = self.api_rotator.execute_with_rotation(request)
                
                for item in response["items"]:
                    videos.append({
                        "id": item["snippet"]["resourceId"]["videoId"],
                        "title": item["snippet"]["title"]
                    })
                
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break
                    
            except Exception as e:
                print(f"Error retrieving playlist videos: {str(e)}")
                break

        return videos

    def _download_transcript(self, video_id: str, video_title: str, folder_path: str):
        """Download and save video transcript"""
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = None
            
            for lang in ['it', 'en']:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    break
                except:
                    continue
            
            if not transcript:
                print(f"No transcript available for: {video_title}")
                self.stats["failed"] += 1
                return

            transcript_data = transcript.fetch()
            
            sanitized_title = self.filename_sanitizer.sanitize(video_title)
            filename = f"{sanitized_title}.txt"
            filepath = os.path.join(folder_path, filename)
            
            if os.path.exists(filepath):
                print(f"Transcript already exists: {filename}")
                self.stats["skipped"] += 1
                return
            
            with open(filepath, "w", encoding="utf-8") as f:
                text = " ".join([item["text"] for item in transcript_data])
                f.write(text)
            
            print(f"Transcript saved: {filename}")
            self.stats["downloaded"] += 1
            
        except (TranscriptsDisabled, NoTranscriptFound):
            print(f"No transcript available for: {video_title}")
            self.stats["failed"] += 1
        except Exception as e:
            print(f"Error downloading transcript for {video_title}: {str(e)}")
            self.stats["failed"] += 1

    def download_playlist_transcripts(self, playlist_url: str):
        """Main method to handle playlist transcript downloads"""
        os.makedirs(self.output_dir, exist_ok=True)
        
        playlist_id, playlist_title = self._get_playlist_info(playlist_url)
        
        if not playlist_id or not playlist_title:
            print("Invalid playlist URL or unable to retrieve playlist information")
            return
            
        folder_name = self.filename_sanitizer.sanitize(playlist_title)
        folder_path = os.path.join(self.output_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        
        videos = self._get_playlist_videos(playlist_id)
        
        if not videos:
            print("No videos found in playlist")
            return
            
        print(f"\nFound {len(videos)} videos. Starting download in: {folder_path}")
        
        for video in videos:
            self._download_transcript(video["id"], video["title"], folder_path)
            time.sleep(1)
        
        print("\nStatistics:")
        print(f"Transcripts downloaded: {self.stats['downloaded']}")
        print(f"Transcripts skipped: {self.stats['skipped']}")
        print(f"Transcripts failed: {self.stats['failed']}")

        # Process with TLDR if any transcripts were downloaded
        if self.stats['downloaded'] > 0:
            if process_with_tldr(folder_path):
                print("TLDR processing completed successfully")
            else:
                print("TLDR processing failed")

def main():
    if len(sys.argv) != 2:
        print("Usage: python yt-playlist.py [YouTube playlist URL]")
        return
    
    downloader = YouTubePlaylistTranscriptDownloader()
    downloader.download_playlist_transcripts(sys.argv[1])

if __name__ == "__main__":
    main()