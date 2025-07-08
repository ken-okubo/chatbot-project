import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def get_openai_response(messages):
    try:
        response = client.chat.completions.create(
            model='gpt-4o',
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Erro ao chamar OpenAI: {e}")
        return None
