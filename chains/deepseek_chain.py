# chains/deepseek_chain.py
# Step 3 

"""
A minimal conversation chain powered by DeepSeek via the OpenAI-compatible endpoint.
This module exposes:
- build_chat_model(): return a configured ChatOpenAI client for DeepSeek
- build_conversation_chain(): return a LangChain runnable (prompt -> model -> text)
- ask(message): convenience helper to run one-shot Q&A

All functions include docstrings for clarity.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser


load_dotenv()


def build_chat_model(temperature: float = 0) -> ChatOpenAI:
    """
    Create a LangChain ChatOpenAI client that talks to DeepSeek.

    Args:
        temperature (float): Sampling temperature. 0 for deterministic output.

    Returns:
        ChatOpenAI: A configured chat model that hits DeepSeek's OpenAI-compatible endpoint.
    """
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        temperature=temperature,
    )


def build_conversation_chain(
    system_prompt: Optional[str] = None, temperature: float = 0
):
    """
    Build a minimal LCEL (LangChain Expression Language) pipeline:
    user input -> prompt -> DeepSeek model -> string output.

    Args:
        system_prompt (str, optional): System role instruction to steer behavior.
            If None, a default helpful assistant instruction is used.
        temperature (float): Model temperature.

    Returns:
        Runnable: A runnable chain that accepts {'input': <text>} and returns a string.
    """
    prompt_text = system_prompt or "You are a helpful research copilot. Be concise and accurate."

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompt_text),
            ("human", "{input}"),
        ]
    )

    model = build_chat_model(temperature=temperature)
    parser = StrOutputParser()

    # LCEL: prompt | model | parser
    chain = prompt | model | parser
    return chain


def ask(message: str, system_prompt: Optional[str] = None, temperature: float = 0) -> str:
    """
    Convenience helper to perform a single question-and-answer turn.

    Args:
        message (str): The user question or instruction.
        system_prompt (str, optional): Optional system instruction to steer behavior.
        temperature (float): Sampling temperature for generation.

    Returns:
        str: The model's textual reply.
    """
    chain = build_conversation_chain(system_prompt=system_prompt, temperature=temperature)
    return chain.invoke({"input": message})
