"""
llm.py

one shared llm object that every agent imports.
"""

from langchain_google_genai import ChatGoogleGenerativeAI

import config

llm = ChatGoogleGenerativeAI(
    model=config.MODEL,
    api_key=config.GOOGLE_API_KEY,
    temperature=0.5,
    max_retries=5,
)
