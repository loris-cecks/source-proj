# YouTube Transcript Downloader & Summarizer

A Python-based tool suite for downloading and summarizing YouTube video transcripts. The system supports downloading transcripts from individual channels, playlists, and recent videos, with automatic summarization using Google's Gemini AI.

## Features

- Download transcripts from:
  - Individual YouTube channels
  - YouTube playlists
  - Recent videos (last 7 days) from specified channels
- Automatic transcript summarization using Gemini AI
- Support for multiple YouTube API keys with automatic rotation
- Handles both English and Italian transcripts
- Automatic filtering of YouTube Shorts
- Sanitized filename handling
- Interactive command-line interface

## Prerequisites

- Python 3.x
- Google YouTube Data API v3 credentials
- Google Gemini API key
- Required Python packages (see requirements section)

## Setup

1. Clone the repository
2. Create a `.env` file with required API keys:

```
API_KEY_1=your_youtube_api_key_1
API_KEY_2=your_youtube_api_key_2
...
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-exp-1206
```

3. Install required packages:

```bash
pip install google-api-python-client youtube-transcript-api python-dotenv google.generativeai isodate pyyaml
```

## Usage

Run the launcher script for an interactive menu:

```bash
python yt-launcher.py
```

Or run individual scripts directly:

```bash
# Download from a channel
python yt-channel.py [channel_url]

# Download from a playlist
python yt-playlist.py [playlist_url]

# Download recent videos
python yt-lastweek.py
```

## Configuration Files

- `channels.txt`: List of YouTube channel URLs to monitor
- `playlists.yaml`: List of playlists with optional comments
- `prompt.txt`: Custom prompt template for Gemini AI summarization

## Output Structure

```
project/
├── yt-channels/          # Channel transcripts
├── yt-playlists/        # Playlist transcripts
└── yt-lastweek/         # Recent video transcripts
    └── TLDR/            # AI-generated summaries
```

## Error Handling

- Automatic API key rotation on quota exceeded
- Retry mechanism for failed requests
- Comprehensive error reporting
- Skip existing transcripts to avoid duplicates

## Notes

- Respects YouTube API quotas through key rotation
- Filters out YouTube Shorts automatically
- Supports both English and Italian transcripts
- Generates summaries using Gemini AI for downloaded transcripts
