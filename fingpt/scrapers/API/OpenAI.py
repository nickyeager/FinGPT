import openai
import os
from dotenv import load_dotenv
load_dotenv()

OPEN_AI_KEY = os.getenv('OPEN_AI_KEY')

def get_result_from_openai_gpt4( prompt_str: str):
    max_tokens = 64
    openai.api_key = OPEN_AI_KEY
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=prompt_str,
        temperature=0,
        max_tokens=max_tokens,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response