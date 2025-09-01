



import os 
from dotenv import load_dotenv


load_dotenv()

print("OPENAI-API-Key: ", os.getenv("OPENAI_API_KEY"))
print("DEEPSEEK-API-Key: ", os.getenv("DEEPSEEK_API_KEY"))

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph

print("LangChain & LangGraph imported successfully!")



# Please install OpenAI SDK first: `pip3 install openai`

from openai import OpenAI

client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello, Who are you?"},
    ],
    stream=False
)

print(response.choices[0].message.content)