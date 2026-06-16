import os
from dotenv import load_dotenv

load_dotenv()


def get_llm():
    """
    Initializes and returns the appropriate LLM client (OpenAI or Google Gemini)
    depending on the API keys configured in the environment.
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")

    if openai_key:
        try:
            from langchain_openai import ChatOpenAI
            print("Using OpenAI ChatOpenAI (gpt-4o-mini)")
            return ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
        except ImportError:
            print("Warning: langchain_openai is not installed, attempting to fallback to google LLM.")

    if google_key:
        from langchain_google_genai import ChatGoogleGenerativeAI

        print("Using Google ChatGoogleGenerativeAI (gemini-2.5-flash)")
        return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)

    raise ValueError("Eroare: Nu a fost gasita nicio cheie API (OPENAI_API_KEY sau GOOGLE_API_KEY) in fisierul .env!")

def get_embeddings():
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )