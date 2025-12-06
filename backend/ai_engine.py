import json
import os

import chromadb
from openai import OpenAI
from dotenv import load_dotenv
from chromadb.utils import embedding_functions

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("Brak klucza API! Dodaj GROQ_API_KEY do pliku .env")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)

MODEL_NAME = "llama-3.3-70b-versatile"
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "zus_cases"

ef = embedding_functions.DefaultEmbeddingFunction()

try:
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        collection = chroma_client.get_collection(name=COLLECTION_NAME, embedding_function=ef)
        HAS_DB_CONNECTION = True
    except Exception:
        print(f"UWAGA: Nie znaleziono kolekcji '{COLLECTION_NAME}'. Uruchom skrypt indeksujący (build_knowledge.py)!")
        HAS_DB_CONNECTION = False
except Exception as e:
    print(f"UWAGA: Błąd inicjalizacji ChromaDB: {e}")
    HAS_DB_CONNECTION = False


def find_similar_cases(user_description, n_results=3):
    if not HAS_DB_CONNECTION:
        return "Brak dostępu do bazy historycznej (nie zaindeksowano spraw)."

    try:
        results = collection.query(
            query_texts=[user_description],
            n_results=n_results
        )

        context_text = ""
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                case_id = results['ids'][0][i]
                context_text += f"\n--- PODOBNA SPRAWA HISTORYCZNA NR {i + 1} (ID: {case_id}) ---\n"
                context_text += f"DECYZJA I UZASADNIENIE EKSPERTA ZUS:\n{doc}\n"

        return context_text

    except Exception as e:
        print(f"Błąd podczas szukania w ChromaDB: {e}")
        return "Błąd podczas przeszukiwania archiwum spraw."


def get_citizen_chat_response(messages_history):
    system_prompt = """
    Jesteś wirtualnym urzędnikiem ZUS. Pomagasz zgłosić wypadek.
    Mów krótko, prosto i po polsku.
    Zbierz informacje: Data, Miejsce, Przebieg zdarzenia, Uraz.
    """

    full_messages = [{"role": "system", "content": system_prompt}] + messages_history

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,  # Używamy Llamy 3
            messages=full_messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Błąd Groq API: {str(e)}"


def analyze_case_for_officer(citizen_description, pdf_text=""):
    similar_cases_context = find_similar_cases(citizen_description)

    system_prompt = f"""
    Jesteś Starszym Orzecznikiem ZUS.

    ZASADY PRAWNE:
    Wypadek przy pracy = Nagłość + Przyczyna Zewnętrzna + Związek z Pracą + Uraz.

    PODOBNE SPRAWY Z ARCHIWUM (Wzoruj się na nich!):
    {similar_cases_context}

    ZADANIE:
    Przeanalizuj opis i dokumentację. Wydaj decyzję w formacie JSON.
    Zwróć TYLKO czysty JSON.
    """

    user_message = f"""
    Opis zgłoszenia: {citizen_description}
    Dokumentacja (PDF): {pdf_text}
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        return json.loads(content)

    except json.JSONDecodeError:
        return {
            "decyzja": "BŁĄD PARSOWANIA",
            "uzasadnienie": "Model zwrócił odpowiedź, która nie jest poprawnym JSONem.",
            "karta_wypadku": {}
        }
    except Exception as e:
        return {
            "decyzja": "BŁĄD API",
            "uzasadnienie": f"Wystąpił błąd połączenia z Groq: {str(e)}",
            "karta_wypadku": {}
        }