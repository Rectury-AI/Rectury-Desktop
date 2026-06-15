import os

from openai import OpenAI
from dotenv import load_dotenv

def create_client():
    load_dotenv()
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise ValueError("XAI_API_KEY environment variable is not set.")
    
    return OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1"
    )