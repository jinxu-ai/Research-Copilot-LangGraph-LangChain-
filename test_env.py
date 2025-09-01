# # Please install OpenAI SDK first: `pip3 install openai`

# from openai import OpenAI

# client = OpenAI(api_key="<DeepSeek API Key>", base_url="https://api.deepseek.com")

# response = client.chat.completions.create(
#     model="deepseek-chat",
#     messages=[
#         {"role": "system", "content": "You are a helpful assistant"},
#         {"role": "user", "content": "Hello"},
#     ],
#     stream=False
# )

# print(response.choices[0].message.content)



import os 
from dotenv import load_dotenv


load_dotenv()

print("OPENAI-API-Key: ", os.getenv("OPENAI_API_KEY"))
print("DEEPSEEK-API-Key: ", os.getenv("DEEPSEEK_API_KEY"))