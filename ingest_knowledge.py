import os
import chromadb
from chromadb.utils import embedding_functions
from PyPDF2 import PdfReader

def extract_text_from_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

client = chromadb.PersistentClient(path="./chroma_db")
embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = client.get_or_create_collection(name="gleb_papers", embedding_function=embed_fn)

papers_dir = "papers"
if not os.path.exists(papers_dir):
    os.makedirs(papers_dir)
    print(f"Создана папка {papers_dir}. Положите туда PDF-файлы статей.")
    exit(0)

for filename in os.listdir(papers_dir):
    if filename.lower().endswith(".pdf"):
        print(f"Обработка {filename}...")
        text = extract_text_from_pdf(os.path.join(papers_dir, filename))
        chunk_size = 1000
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        for i, chunk in enumerate(chunks):
            collection.add(
                documents=[chunk],
                metadatas=[{"source": filename, "chunk": i}],
                ids=[f"{filename}_{i}"]
            )
        print(f"Добавлено {len(chunks)} фрагментов.")