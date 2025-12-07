import json
import os
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv
from chromadb.utils import embedding_functions
from backend.prompts import CITIZEN_SYSTEM_PROMPT, BUSINESS_SYSTEM_PROMPT, get_officer_system_prompt

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("Brak klucza API dla Gemini! Dodaj GEMINI_API_KEY do pliku .env")

genai.configure(api_key=gemini_api_key)

MODEL_NAME = "gemini-2.5-flash"

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
            for i, doc in enumerate(
                    results['documents'][0]):
                case_id = results['ids'][0][i]
                context_text += f"\n--- PODOBNA SPRAWA HISTORYCZNA NR {i + 1} (ID: {case_id}) ---\n"
                context_text += f"DECYZJA I UZASADNIENIE EKSPERTA ZUS:\n{doc}\n"
        return context_text
    except Exception as e:
        print(f"Błąd podczas szukania w ChromaDB: {e}")
        return "Błąd podczas przeszukiwania archiwum spraw."


def get_citizen_chat_response(messages_history, system_prompt=CITIZEN_SYSTEM_PROMPT):
    gemini_messages = []
    system_prompt_added = False

    for msg in messages_history:
        role = "user" if msg["role"] == "user" else "model"
        content = msg["content"]

        if role == "user" and not system_prompt_added:
            content = system_prompt + "\n\n" + content
            system_prompt_added = True

        gemini_messages.append({"role": role, "parts": [content]})

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(gemini_messages)
        return response.text
    except Exception as e:
        print(f"Błąd Gemini API w get_citizen_chat_response: {str(e)}")
        return f"Błąd Gemini API: {str(e)}"


def analyze_case_for_officer(citizen_description, medical_pdf_text="", workplace_pdf_text=""):
    similar_cases_context = find_similar_cases(citizen_description)

    system_prompt = get_officer_system_prompt(similar_cases_context)

    user_message = f"""
    Opis zgłoszenia od obywatela: {citizen_description}

    Dokumentacja medyczna (PDF):
    {medical_pdf_text if medical_pdf_text else "Brak dokumentacji medycznej."}

    Dokumentacja miejsca pracy (PDF):
    {workplace_pdf_text if workplace_pdf_text else "Brak dokumentacji miejsca pracy."}

    Na podstawie powyższych danych, dokonaj analizy i zwróć decyzję w formacie JSON.
    """
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(
            [{"role": "user", "parts": [system_prompt + "\n" + user_message]}],
            generation_config=genai.types.GenerationConfig(temperature=0.0)
        )

        content = response.text
        if content.startswith("```json") and content.endswith("```"):
            content = content[7:-3].strip()

        return json.loads(content)
    except json.JSONDecodeError:
        print(f"Błąd parsowania JSON: {content}")
        return {
            "decyzja": "BŁĄD PARSOWANIA",
            "uzasadnienie": "Model zwrócił odpowiedź, która nie jest poprawnym JSONem. Sprawdź logi.",
            "niezgodnosci_lub_braki": "Brak",
            "karta_wypadku": {}
        }
    except Exception as e:
        print(f"Błąd Gemini API w analyze_case_for_officer: {str(e)}")
        return {
            "decyzja": "BŁĄD API",
            "uzasadnienie": f"Wystąpił błąd połączenia z Gemini: {str(e)}",
            "niezgodnosci_lub_braki": "Brak",
            "karta_wypadku": {}
        }