import os
import chromadb
from chromadb.utils import embedding_functions
from PyPDF2 import PdfReader

chroma_client = chromadb.PersistentClient(path="./chroma_db")
ef = embedding_functions.DefaultEmbeddingFunction()
collection = chroma_client.get_or_create_collection(name="zus_cases", embedding_function=ef)


def extract_text(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        return "".join([page.extract_text() or "" for page in reader.pages])
    except:
        return ""


def index_cases():
    root_dir = "./data"
    print("Indeksuję dane lokalnie (bez OpenAI)...")

    for folder_name in os.listdir(root_dir):
        folder_path = os.path.join(root_dir, folder_name)
        if not os.path.isdir(folder_path): continue

        full_text = ""
        for f in os.listdir(folder_path):
            full_text += extract_text(os.path.join(folder_path, f))

        if full_text:
            collection.upsert(
                ids=[folder_name],
                documents=[full_text],
                metadatas=[{"case_id": folder_name}]
            )
            print(f"Zaktualizowano/Dodano: {folder_name}")


if __name__ == "__main__":
    index_cases()