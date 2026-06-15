import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("XAI_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.x.ai/v1"
)
while True:
    user= input("Tú:").strip()
    response = client.responses.create(
        model="grok-4.3",
        input=user
    )
    print(response.output_text)
    
    
    
    if user == "":
        break