import os
from dotenv import load_dotenv

load_dotenv()

def get_llm(temperature: float = 0.3):
    """
    Returns an LLM instance.
    Prefers Groq (openai/gpt-oss-120b) when GROQ_API_KEY is available,
    as it avoids Mistral's strict 1 request/sec rate limits and 429 quota exhaustion errors.
    Falls back to ChatMistralAI if requested or if Groq is not configured.
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    provider = os.getenv("LLM_PROVIDER", "auto").lower()

    if (provider in ("groq", "auto")) and groq_api_key:
        from langchain_groq import ChatGroq
        model = os.getenv("GROQ_LLM_MODEL", "openai/gpt-oss-120b")
        return ChatGroq(
            model=model,
            groq_api_key=groq_api_key,
            temperature=temperature,
        )

    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    if mistral_api_key:
        from langchain_mistralai import ChatMistralAI
        return ChatMistralAI(
            model=os.getenv("MISTRAL_MODEL", "mistral-small-latest"),
            mistral_api_key=mistral_api_key,
            temperature=temperature,
        )

    raise RuntimeError(
        "No LLM API key found! Please configure GROQ_API_KEY or MISTRAL_API_KEY in your environment."
    )

