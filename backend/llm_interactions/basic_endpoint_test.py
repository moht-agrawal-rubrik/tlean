import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), base_url="https://basecamp.stark.rubrik.com")

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful monk."},
        {"role": "user", "content": "Hey! Please summarize life in one sentence."}
    ]
)

print(response)