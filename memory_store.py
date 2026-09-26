import chromadb
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# ChromaDB stores everything locally on disk, in a folder called "memory_db"
chroma_client = chromadb.PersistentClient(path="./memory_db")
collection = chroma_client.get_or_create_collection(name="agent_memory")


def get_embedding(text: str) -> list:
    """Converts text into a numeric 'meaning fingerprint' using Gemini's embedding model."""
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
    )
    return result.embeddings[0].values


def save_memory(task: str, result: str):
    """Saves one conversation turn permanently, with its embedding for future search."""
    combined_text = f"User asked: {task}\nAssistant answered: {result}"
    embedding = get_embedding(combined_text)

    # Each entry needs a unique ID — use the current count as a simple counter
    entry_id = str(collection.count())

    collection.add(
        ids=[entry_id],
        embeddings=[embedding],
        documents=[combined_text],
    )


def search_memory(query: str, n_results: int = 4) -> list:
    """Finds the most relevant past conversations for the current question, however old they are."""
    if collection.count() == 0:
        return []

    query_embedding = get_embedding(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count()),
    )
    return results["documents"][0] if results["documents"] else []



def get_recent_memories(n: int = 5) -> list:
    """Fetches the N most recent memories directly (not by search, just by recency)."""
    total = collection.count()
    if total == 0:
        return []
    start = max(0, total - n)
    ids = [str(i) for i in range(start, total)]
    result = collection.get(ids=ids)
    return result["documents"] if result["documents"] else []