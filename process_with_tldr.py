# process_with_tldr.py
import subprocess
import sys
from pathlib import Path
from typing import Optional

class TLDRProcessor:
    """Class to handle TLDR processing of transcripts"""
    
    def __init__(self, tldr_script_path: Optional[str] = 'TLDR.py'):
        """
        Initialize the TLDR processor
        
        Args:
            tldr_script_path: Path to the TLDR.py script (default: 'TLDR.py')
        """
        self.tldr_script = Path(tldr_script_path)
        if not self.tldr_script.exists():
            raise FileNotFoundError(f"TLDR script not found at: {self.tldr_script}")

    def process_folder(self, folder_path: str) -> bool:
        """
        Process all transcripts in the specified folder using TLDR
        
        Args:
            folder_path: Path to the folder containing transcripts
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        try:
            print("\nProcessing transcripts with TLDR...")
            subprocess.run(
                [sys.executable, str(self.tldr_script), folder_path], 
                check=True
            )
            print("TLDR processing completed successfully.")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error during TLDR processing: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during TLDR processing: {e}")
            return False

def process_with_tldr(folder_path: str, tldr_script: Optional[str] = 'TLDR.py') -> bool:
    """
    Convenience function to process transcripts with TLDR
    
    Args:
        folder_path: Path to the folder containing transcripts
        tldr_script: Path to the TLDR.py script (default: 'TLDR.py')
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    try:
        processor = TLDRProcessor(tldr_script)
        return processor.process_folder(folder_path)
    except Exception as e:
        print(f"Failed to initialize TLDR processor: {e}")
        return False

if __name__ == "__main__":
    # Allow direct execution with folder path argument
    if len(sys.argv) != 2:
        print("Usage: python process_with_tldr.py <folder_path>")
        sys.exit(1)
        
    success = process_with_tldr(sys.argv[1])
    sys.exit(0 if success else 1)