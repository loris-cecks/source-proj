#!/usr/bin/env python3
import os
import sys
import subprocess

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_header():
    print("=" * 50)
    print("YouTube Transcripts Downloader".center(50))
    print("=" * 50)
    print()

def print_menu():
    print("Available options:")
    print()
    print("1. Download transcripts from last week's videos")
    print("2. Download transcripts from a YouTube channel")
    print("3. Download transcripts from a YouTube playlist")
    print("4. Exit")
    print()

def get_user_choice():
    while True:
        try:
            choice = input("Enter your choice (1-4): ")
            if choice in ['1', '2', '3', '4']:
                return choice
            print("Invalid choice. Please enter a number between 1 and 4.")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            sys.exit(0)

def run_script(script_name, requires_argument=True):
    try:
        if requires_argument:
            url = input("\nEnter the YouTube URL: ").strip()
            if not url:
                print("URL cannot be empty")
                return
            subprocess.run([sys.executable, script_name, url])
        else:
            subprocess.run([sys.executable, script_name])
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error running script: {str(e)}")

def main():
    while True:
        clear_screen()
        print_header()
        print_menu()
        
        choice = get_user_choice()
        
        if choice == '1':
            run_script('yt-lastweek.py', requires_argument=False)
        elif choice == '2':
            run_script('yt-channel.py')
        elif choice == '3':
            run_script('yt-playlist.py')
        elif choice == '4':
            print("\nGoodbye!")
            sys.exit(0)
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()