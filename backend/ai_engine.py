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

MODEL_NAME = "gemini-robotics-er-1.5-preview"

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


def analyze_case_for_officer(citizen_description, documentation_text=""):
    similar_cases_context = find_similar_cases(citizen_description)

    system_prompt = get_officer_system_prompt(similar_cases_context)

    user_message = f"""
    Opis zgłoszenia od obywatela: {citizen_description}

    Załączona dokumentacja (PDF):
    {documentation_text if documentation_text else "Brak załączonej dokumentacji."}

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


def extract_accident_data_for_pdf(messages_history):
    """
    Analizuje historię rozmowy i wyciąga dane do wypełnienia formularza Zawiadomienie o wypadku.
    Zwraca słownik, gdzie klucze to nazwy pól w PDF.
    """
    conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages_history])
    
    prompt = f"""
    Przeanalizuj poniższą rozmowę z obywatelem zgłaszającym wypadek i wyciągnij dane potrzebne do wypełnienia formularza "Zawiadomienie o wypadku".
    
    Rozmowa:
    {conversation_text}
    
    Twoim zadaniem jest przygotowanie obiektu JSON, w którym klucze odpowiadają polom formularza PDF.
    Oto lista pól, które powinieneś spróbować wypełnić na podstawie rozmowy (jeśli brak danych, zostaw puste lub wpisz "Nie podano").
    
    DANE OSOBY POSZKODOWANEJ:
    - PESEL[0] (PESEL)
    - Rodzajseriainumerdokumentu[0] (Rodzaj, seria i numer dokumentu tożsamości)
    - Imię[0] (Imię)
    - Nazwisko[0] (Nazwisko)
    - Dataurodzenia[0] (Data urodzenia DD/MM/RRRR)
    - Miejsceurodzenia[0] (Miejsce urodzenia)
    - Numertelefonu[0] (Numer telefonu)
    
    ADRES ZAMIESZKANIA POSZKODOWANEGO:
    - Ulica[0] (Ulica)
    - Numerdomu[0] (Numer domu)
    - Numerlokalu[0] (Numer lokalu)
    - Kodpocztowy[0] (Kod pocztowy)
    - Poczta[0] (Miejscowość)
    - Nazwapaństwa[0] (Nazwa państwa, jeśli inne niż Polska)
    
    ADRES DO KORESPONDENCJI (jeśli inny):
    - Ulica2[0] (Ulica)
    - Numerdomu2[0] (Numer domu)
    - Numerlokalu2[0] (Numer lokalu)
    - Kodpocztowy2[0] (Kod pocztowy)
    - Poczta2[0] (Miejscowość)
    - Numertelefonu2[0] (Numer telefonu)
    
    DANE OSOBY ZAWIADAMIAJĄCEJ (jeśli inna niż poszkodowany):
    - Imię[1] (Imię)
    - Nazwisko[1] (Nazwisko)
    - Ulica[1] (Ulica)
    - Numerdomu[1] (Numer domu)
    - Numerlokalu[1] (Numer lokalu)
    - Kodpocztowy[1] (Kod pocztowy)
    - Poczta[1] (Miejscowość)
    
    INFORMACJA O WYPADKU:
    - Datawyp[0] (Data wypadku DD/MM/RRRR)
    - Godzina[0] (Godzina wypadku)
    - Miejscewyp[0] (Miejsce wypadku)
    - Godzina3A[0] (Planowana godzina rozpoczęcia pracy)
    - Godzina3B[0] (Planowana godzina zakończenia pracy)
    - Tekst4[0] (Rodzaj doznanych urazów)
    - Tekst5[0] (Szczegółowy opis okoliczności, miejsca i przyczyn wypadku)
    - TAK6[0] / NIE6[0] (Czy udzielono pierwszej pomocy? Wpisz "Yes" w odpowiednie pole, drugie zostaw puste)
    - Tekst6[0] (Jeśli TAK, nazwa i adres placówki medycznej)
    - Tekst7[0] (Organ prowadzący postępowanie np. Policja)
    - TAK8[0] / NIE8[0] (Czy wypadek przy obsłudze maszyn? Wpisz "Yes" w odpowiednie pole)
    - Tekst8[0] (Jeśli TAK, czy maszyna była sprawna)
    - TAK9[0] / NIE9[0] (Czy maszyna ma atest? Wpisz "Yes" w odpowiednie pole)
    - TAK10[0] / NIE10[0] (Czy maszyna w ewidencji? Wpisz "Yes" w odpowiednie pole)
    
    Zwróć TYLKO poprawny obiekt JSON. Nie dodawaj żadnych komentarzy ani formatowania markdown (```json).
    """
    
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        # Clean up markdown if present
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
            
        return json.loads(content)
    except Exception as e:
        print(f"Błąd ekstrakcji danych do PDF: {e}")
        return {}
