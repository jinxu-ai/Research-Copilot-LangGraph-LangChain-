import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
load_dotenv()

'''
load LLMs
'''

def create_llm_client(provider="deepseek"):
    """
    Create and return a Large Language Model (LLM) client based on the given provider.

    This function supports two providers:
    - "openai": Uses LangChain's ChatOpenAI client (with GPT-4o-mini).
    - "deepseek": Uses the official OpenAI SDK with DeepSeek's API base URL.

    Args:
        provider (str, optional): The LLM provider to use. 
            Options are:
            - "openai" (default: "deepseek")
            - "deepseek"

    Returns:
        object: An initialized LLM client instance (ChatOpenAI or OpenAI).

    Raises:
        ValueError: If the given provider is not supported.
    """
    
    # create openai client
    if provider == "openai":
        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY")
        )
    
    # create deepseek client
    elif provider == "deepseek":
        from openai import OpenAI
        return OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
    
    # error
    else:
        raise ValueError(f"Unsupported provider: {provider}")




from typing_extensions import Literal
API_type = Literal["OPENAI_API_KEY", "DEEPSEEK_API_KEY"]








# def get_llm()

# Please install OpenAI SDK first: `pip3 install openai`

# from openai import OpenAI


# def get_chat(api_type: API_type):
#     client = OpenAI(api_key=os.getenv(api_type), base_url="https://api.deepseek.com")

#     response = client.chat.completions.create(
#         model="deepseek-chat",
#         messages=[
#             {"role": "system", "content": "You are a helpful assistant"},
#             {"role": "user", "content": "Hello, Who are you?"},
#         ],
#         stream=False
#     )

#     print(response.choices[0].message.content)



