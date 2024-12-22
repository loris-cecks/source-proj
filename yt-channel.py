# yt-channel.py
import os
import sys
from typing import List, Dict, Optional, Tuple
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from dotenv import load_dotenv
import time
import re
from shorts_filter import YouTubeShortsFilter
from sanitize_filename import FilenameSanitizer
from api_key_rotator import YouTubeAPIKeyRotator
from process_with_tldr import process_with_tldr

load_dotenv()

class YouTubeChannelTranscriptDownloader:
    def __init__(self):
        """Initialize the downloader with required components"""
        self.api_rotator = YouTubeAPIKeyRotator()
        self.output_dir = "yt-channels"
        self.stats = {
            "downloaded": 0,
            "skipped": 0,
            "failed": 0
        }
        self.shorts_filter = YouTubeShortsFilter()
        self.filename_sanitizer = FilenameSanitizer()

    def _get_channel_info(self, channel_url: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract channel ID and title from URL"""
        try:
            if '@' in channel_url:
                channel_handle = channel_url.split("@")[-1]
            else:
                channel_handle = channel_url.split("/")[-1]

            try:
                request = self.api_rotator.service.search().list(
                    q=channel_handle,
                    type="channel",
                    part="id,snippet",
                    maxResults=1
                )
                response = self.api_rotator.execute_with_rotation(request)
                
                if response.get("items"):
                    channel_id = response["items"][0]["id"]["channelId"]
                    channel_title = response["items"][0]["snippet"]["title"]
                    return channel_id, channel_title
                    
            except HttpError as e:
                print(f"API Error: {str(e)}")
                return None, None
                
        except Exception as e:
            print(f"Error retrieving channel ID: {str(e)}")
            
        return None, None

    def _get_video_details_batch(self, video_ids: List[str]) -> Dict:
        """Get video details in batches to optimize quota usage"""
        try:
            request = self.api_rotator.service.videos().list(
                part=self.shorts_filter.get_required_parts(),
                id=','.join(video_ids)
            )
            response = self.api_rotator.execute_with_rotation(request)
            return {item["id"]: item for item in response.get("items", [])}
            
        except Exception as e:
            print(f"Error getting video details: {str(e)}")
            return {}

    def _get_channel_videos(self, channel_id: str) -> List[Dict]:
        """Get all videos from channel excluding shorts"""
        videos = []
        temp_videos = []
        next_page_token = None

        while True:
            try:
                request = self.api_rotator.service.search().list(
                    channelId=channel_id,
                    part="id,snippet",
                    order="date",
                    maxResults=50,
                    pageToken=next_page_token,
                    type="video"
                )
                response = self.api_rotator.execute_with_rotation(request)
                
                for item in response["items"]:
                    if item["snippet"].get("liveBroadcastContent") != "live":
                        temp_videos.append({
                            "id": item["id"]["videoId"],
                            "title": item["snippet"]["title"]
                        })
                
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break
                    
            except Exception as e:
                print(f"Error retrieving channel videos: {str(e)}")
                break

        batch_size = 50
        for i in range(0, len(temp_videos), batch_size):
            batch = temp_videos[i:i + batch_size]
            batch_ids = [v["id"] for v in batch]
            video_details = self._get_video_details_batch(batch_ids)
            
            for video in batch:
                if video["id"] in video_details and not self.shorts_filter.is_short(video_details[video["id"]]):
                    videos.append(video)

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
            
            filename = self.filename_sanitizer.sanitize(video_title) + ".txt"
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

    def download_channel_transcripts(self, channel_url: str):
        """Main method to handle channel transcript downloads"""
        os.makedirs(self.output_dir, exist_ok=True)
        
        channel_id, channel_title = self._get_channel_info(channel_url)
        
        if not channel_id or not channel_title:
            print("Invalid channel URL or unable to retrieve channel information")
            return
            
        folder_name = self.filename_sanitizer.sanitize(channel_title)
        folder_path = os.path.join(self.output_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        
        videos = self._get_channel_videos(channel_id)
        
        if not videos:
            print("No videos found in channel")
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
        print("Usage: python yt-channel.py [YouTube channel URL]")
        return
    
    downloader = YouTubeChannelTranscriptDownloader()
    downloader.download_channel_transcripts(sys.argv[1])

if __name__ == "__main__":
    main()