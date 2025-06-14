# groq_agent.py

import os
from langchain_core.language_models import LLM
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

def get_groq_llm() -> LLM:
    """
    Returns a configured instance of Groq's LLaMA2 LLM using LangChain.
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables!")

    llm = ChatGroq(
        temperature=0.7,
        model_name="llama-3.3-70b-versatile",  # Using the latest versatile model
        groq_api_key=groq_api_key
    )

    return llm


def get_prompt_template() -> PromptTemplate:
    """
    Returns a standard prompt template for KalpAI use.
    """
    template = """
    You are KalpAI, an empathetic multilingual psychologist trained on psychology books and human behavior.

    User Emotion: {emotion}
    Language: {language}
    Query: {query}

    Based on the emotional tone, psychology literature, and motivational practices, craft a deeply empathetic, helpful, and relevant response in the user's selected language.
    """

    return PromptTemplate(
        input_variables=["emotion", "language", "query"],
        template=template
    )