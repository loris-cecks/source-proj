import os
import sys
import time
import random
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional
import google.generativeai as genai

def load_config():
    load_dotenv()
    return {
        'api_key': os.getenv('GEMINI_API_KEY'),
        'input_dir': Path(os.getenv('INPUT_DIR', 'transcripts')),
        'output_dir': None,  # Will be set based on input directory
        'model_name': os.getenv('GEMINI_MODEL', 'gemini-exp-1206'),
        'prompt_path': Path('prompt.txt')
    }

class SimpleTranscriptProcessor:
    def __init__(self, api_key: str, model_name: str, prompt: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name=model_name)
        self.prompt = prompt

    def process(self, text: str) -> Optional[str]:
        try:
            formatted_prompt = self.prompt.replace("{text}", text)
            response = self.model.generate_content(formatted_prompt)
            return response.text if response else None
        except Exception as e:
            print(f"[ERROR] API Error: {e}")
            return None

def process_transcripts(config):
    input_dir = config['input_dir']
    output_dir = config['output_dir']
    prompt_path = config['prompt_path']

    if not prompt_path.exists():
        print(f"[ERROR] Prompt file '{prompt_path}' does not exist.")
        return

    prompt_template = prompt_path.read_text(encoding='utf-8')
    processor = SimpleTranscriptProcessor(api_key=config['api_key'], 
                                        model_name=config['model_name'], 
                                        prompt=prompt_template)
    
    if not input_dir.exists():
        print(f"[ERROR] Input directory '{input_dir}' does not exist.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    for file in input_dir.glob('*.txt'):
        print(f"Processing file: {file.name}")
        output_file = output_dir / f"{file.stem}.md"

        if output_file.exists():
            print(f"[OVERWRITE] Overwriting existing file: {file.name}")
        
        transcript_text = file.read_text(encoding='utf-8')
        ai_output = processor.process(transcript_text)
        
        if ai_output:
            output_file.write_text(ai_output, encoding='utf-8')
            print(f"[SUCCESS] Output saved to: {output_file}")
        else:
            print(f"[FAILED] Unable to process {file.name}.")
        
        time.sleep(random.uniform(1, 3))

def main():
    config = load_config()
    if not config['api_key']:
        print("[ERROR] GEMINI_API_KEY is missing. Please check your .env file.")
        return
        
    if len(sys.argv) > 1:
        config['input_dir'] = Path(sys.argv[1])
    
    config['output_dir'] = config['input_dir'] / 'TLDR'
    
    print(f"Starting transcript processing from {config['input_dir']}...")
    process_transcripts(config)
    print("Processing completed.")

if __name__ == "__main__":
    main()