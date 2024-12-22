import os
import sys
from datetime import datetime, timedelta
import googleapiclient.discovery
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv
import time
import isodate
import yaml
from api_key_rotator import YouTubeAPIKeyRotator
from sanitize_filename import FilenameSanitizer
from process_with_tldr import process_with_tldr

def parse_duration(duration):
    """Convert ISO 8601 duration to seconds"""
    return int(isodate.parse_duration(duration).total_seconds())

def get_channel_id(youtube_rotator, channel_handle):
    """Get channel ID from channel handle"""
    try:
        request = youtube_rotator.service.search().list(
            part="snippet",
            q=channel_handle,
            type="channel",
            maxResults=1
        )
        response = youtube_rotator.execute_with_rotation(request)
        
        if response['items']:
            return response['items'][0]['snippet']['channelId']
    except Exception as e:
        print(f"Error getting channel ID for {channel_handle}: {str(e)}")
    return None

def is_short_video(youtube_rotator, video_id):
    """Check if a video is a Short based on duration and format"""
    try:
        video_request = youtube_rotator.service.videos().list(
            part="snippet,contentDetails",
            id=video_id
        )
        video_response = youtube_rotator.execute_with_rotation(video_request)
        
        if not video_response.get('items'):
            return True
            
        video = video_response['items'][0]
        
        # Check duration (Shorts are under 60 seconds)
        duration = video['contentDetails']['duration']
        duration_seconds = parse_duration(duration)
        if duration_seconds < 60:
            return True
            
        # Check video format (Shorts are vertical)
        if 'maxres' in video['snippet'].get('thumbnails', {}):
            thumbnail = video['snippet']['thumbnails']['maxres']
            if thumbnail['height'] > thumbnail['width']:
                return True
                
        return False
        
    except Exception as e:
        print(f"Error checking if video is short: {str(e)}")
        return True

def get_recent_videos(youtube_rotator, channel_id):
    """Get non-Shorts videos from the last 7 days"""
    videos = []
    try:
        published_after = (datetime.utcnow() - timedelta(days=7)).isoformat() + 'Z'
        
        search_request = youtube_rotator.service.search().list(
            part="snippet",
            channelId=channel_id,
            maxResults=50,
            order="date",
            publishedAfter=published_after,
            type="video"
        )
        search_response = youtube_rotator.execute_with_rotation(search_request)
        
        for item in search_response.get('items', []):
            video_id = item['id']['videoId']
            
            if not is_short_video(youtube_rotator, video_id):
                videos.append({
                    'id': video_id,
                    'title': item['snippet']['title'],
                    'channel': item['snippet']['channelTitle']
                })

    except Exception as e:
        print(f"Error getting videos: {str(e)}")
    
    return videos

def download_transcript(video_id):
    """Download and format transcript"""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcripts(
            [video_id], 
            languages=['en', 'it']
        )[0]
        
        full_text = ' '.join([entry['text'] for entry in transcript_list[video_id]])
        return full_text
        
    except Exception as e:
        print(f"Error downloading transcript: {str(e)}")
        return None

def load_playlists():
    """Load playlists from YAML file with comments"""
    try:
        with open('playlists.yaml', 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if not data or 'playlists' not in data:
                print("No playlists found in playlists.yaml")
                return []
            return data['playlists']
    except FileNotFoundError:
        print("playlists.yaml not found")
        return []
    except Exception as e:
        print(f"Error loading playlists.yaml: {str(e)}")
        return []

def process_playlist(youtube_rotator, playlist_info, output_dir, stats):
    """Process a single playlist with its comment, getting only last week's videos"""
    try:
        playlist_url = playlist_info['url']
        comment = playlist_info.get('comment', 'No comment provided')
        
        print(f"\nProcessing playlist: {playlist_url}")
        print(f"Comment: {comment}")
        
        playlist_id = playlist_url.split('list=')[1].split('&')[0] if 'list=' in playlist_url else None
        if not playlist_id:
            print("Invalid playlist URL")
            return

        # Calculate the date 7 days ago
        seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat() + 'Z'

        request = youtube_rotator.service.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=50
        )
        response = youtube_rotator.execute_with_rotation(request)
        
        for item in response.get('items', []):
            # Check if video was published in the last 7 days
            published_at = item['snippet']['publishedAt']
            if published_at < seven_days_ago:
                continue

            video_id = item['snippet']['resourceId']['videoId']
            
            # Skip if video is a Short
            if is_short_video(youtube_rotator, video_id):
                continue

            video_title = item['snippet']['title']
            channel_title = item['snippet'].get('videoOwnerChannelTitle', 'Unknown Channel')
            
            filename = f"{channel_title} - {video_title}.txt"
            safe_filename = FilenameSanitizer.sanitize(filename)
            output_file = os.path.join(output_dir, safe_filename)
            
            if os.path.exists(output_file):
                print(f"Skipping existing transcript: {safe_filename}")
                stats['skipped'] += 1
                continue

            transcript = download_transcript(video_id)
            if transcript:
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(transcript)
                    print(f"Downloaded transcript: {safe_filename}")
                    stats['downloaded'] += 1
                except Exception as e:
                    print(f"Error writing transcript: {str(e)}")
                    stats['failed'] += 1
            else:
                print(f"Failed to download transcript for: {video_title}")
                stats['failed'] += 1

            time.sleep(1)

    except Exception as e:
        print(f"Error processing playlist: {str(e)}")

def main():
    # Create output directory
    output_dir = 'yt-lastweek'
    os.makedirs(output_dir, exist_ok=True)

    try:
        youtube_rotator = YouTubeAPIKeyRotator()
    except ValueError as e:
        print(f"Error initializing API key rotator: {str(e)}")
        return

    load_dotenv()
    OVERWRITE = os.getenv('OVERWRITE', 'False').lower() == 'true'

    stats = {
        'downloaded': 0,
        'skipped': 0,
        'failed': 0
    }

    # First process playlists
    print("\nLoading playlists from YAML...")
    playlists = load_playlists()
    
    if playlists:
        print(f"Found {len(playlists)} playlists")
        for playlist_info in playlists:
            process_playlist(youtube_rotator, playlist_info, output_dir, stats)
    else:
        print("No playlists to process")

    # Then process channels
    channel_file = 'channels.txt'
    if os.path.exists(channel_file):
        print("\nProcessing channels...")
        with open(channel_file, 'r') as f:
            channels = [line.strip() for line in f if line.strip()]

        for channel_url in channels:
            channel_handle = channel_url.split('@')[1] if '@' in channel_url else channel_url.split('/')[-1]
            print(f"\nProcessing channel: {channel_handle}")

            channel_id = get_channel_id(youtube_rotator, channel_handle)
            if not channel_id:
                print(f"Could not find channel ID for {channel_url}")
                continue

            videos = get_recent_videos(youtube_rotator, channel_id)
            
            if not videos:
                print(f"No recent videos found for {channel_url}")
                continue

            print(f"\nFound {len(videos)} recent videos for {channel_url}")

            for video in videos:
                filename = f"{video['channel']} - {video['title']}.txt"
                safe_filename = FilenameSanitizer.sanitize(filename)
                output_file = os.path.join(output_dir, safe_filename)
                
                if os.path.exists(output_file) and not OVERWRITE:
                    print(f"Skipping existing transcript: {safe_filename}")
                    stats['skipped'] += 1
                    continue

                transcript = download_transcript(video['id'])
                
                if transcript:
                    try:
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(transcript)
                        print(f"Downloaded transcript: {safe_filename}")
                        stats['downloaded'] += 1
                    except Exception as e:
                        print(f"Error writing transcript to file: {str(e)}")
                        stats['failed'] += 1
                else:
                    print(f"Failed to download transcript for: {video['title']}")
                    stats['failed'] += 1

                time.sleep(1)

    print("\nDownload Statistics:")
    print(f"Downloaded: {stats['downloaded']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Failed: {stats['failed']}")

    if stats['downloaded'] > 0:
        if process_with_tldr(output_dir):
            print("TLDR processing completed successfully")
        else:
            print("TLDR processing failed")

if __name__ == "__main__":
    load_dotenv()
    main()