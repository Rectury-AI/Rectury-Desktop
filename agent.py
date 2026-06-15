import openai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("XAI_API_KEY")

client = openai(
    api_key=api_key,
    base_url="https://api.x.ai/v1"
)