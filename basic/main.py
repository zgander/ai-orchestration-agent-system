from google import genai

#ChatBOT

import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)

chats = client.chats.create(
    model="gemini-2.5-flash"
)

while True:
    message = input("You: ")
    if message == "exit":
        break

    response = chats.send_message(message)
    print("Ans:", response.text)