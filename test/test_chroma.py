import chromadb
try:
    client = chromadb.Client()
    collection = client.create_collection("test")
    collection.upsert(ids=["1"], documents=["test"])
    print("Upsert supported")
except AttributeError:
    print("Upsert NOT supported")
except Exception as e:
    print(f"Error: {e}")
