import os
from openai import AzureOpenAI

endpoint = "Your_Endpoint"  # https://xyz.azure.com/
key = "Your_Key"  # Your API key
model_name = "gpt-4o"  # Your model name

client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_version="2024-02-01",
    api_key=key
)

completion = client.chat.completions.create(
    model=model_name,
    messages=[
        {
            "role": "user",
            "content": "What is AI?",  # Your question can go here
        },
    ],
)

print(completion.choices[0].message.content)
