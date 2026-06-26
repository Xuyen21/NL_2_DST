import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

GPT_4o = "gpt-4o"  # "gpt-4o", "gpt-5-mini"
openai_key = os.getenv("OPENAI_API_KEY")

openai_client = OpenAI(
    # This is the default and can be omitted
    api_key=openai_key
)

