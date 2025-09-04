import os;
from dotenv import load_dotenv;
from openai import OpenAI;

load_dotenv()

c=OpenAI(api_key=os.getenv('DEEPSEEK_API_KEY'),base_url='https://api.deepseek.com')

print(len(c.embeddings.create(model='deepseek-embedding',input='hello world').data[0].embedding))