from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from pypdf import PdfReader
from dotenv import load_dotenv
import os

load_dotenv()

# --- Konfigurera vilka PDF:er som ska läsas in ---
PDF_CONFIGS = [
    {
        "file": "data/husqvarna435.pdf",
        "model": "Husqvarna 435",
        "start_page": 112,  # Svenska sektionen börjar här (1-baserat)
        "end_page": None,   # None = läs till slutet
    },
    {
        "file": "data/husqvarna542i.pdf",
        "model": "Husqvarna 542i XP",
        "start_page": 1,    # Svenska sektionen börjar på sida 1
        "end_page": 44,     # Läs till sida 44
    },
]

def read_pdf(config):
    """Läs in en PDF och returnera text med modelltagg"""
    pdf_file = config["file"]
    model_name = config["model"]

    if not os.path.exists(pdf_file):
        print(f"VARNING: {pdf_file} finns inte, hoppar över...")
        return ""

    reader = PdfReader(pdf_file)

    # Konvertera till 0-baserat index
    start_idx = config["start_page"] - 1
    end_idx = config["end_page"] if config["end_page"] else len(reader.pages)

    print(f"\n--- Läser {model_name} ---")
    print(f"Fil: {pdf_file}")
    print(f"Totalt antal sidor i PDF: {len(reader.pages)}")
    print(f"Läser sidor: {start_idx + 1} till {end_idx}")

    text = ""
    for i in range(start_idx, min(end_idx, len(reader.pages))):
        page = reader.pages[i]
        page_text = page.extract_text()
        page_text = page_text.replace("\n", " ").strip()
        text += page_text + "\n"

    # Lägg till modelltagg i början av texten så AI:n vet vilken såg det gäller
    tagged_text = f"[MODELL: {model_name}]\n{text}"

    print(f"Antal tecken extraherade: {len(text)}")
    return tagged_text

# --- Läs in alla PDF:er ---
all_text = ""
for config in PDF_CONFIGS:
    all_text += read_pdf(config) + "\n\n"

print(f"\n--- Totalt ---")
print(f"Totalt antal tecken från alla PDF:er: {len(all_text)}")

# --- Skapa Document-objekt ---
docs = [Document(page_content=all_text)]

# --- Dela upp i chunks ---
# Större chunks för att behålla mer kontext (t.ex. hela felsökningstabeller)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
docs_split = text_splitter.split_documents(docs)
print(f"Antal chunks: {len(docs_split)}")

# --- Skapa embeddings (lokalt HuggingFace, gratis) ---
print("\nSkapar embeddings med HuggingFace...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2")

# --- Skapa FAISS-index ---
vectorstore = FAISS.from_documents(docs_split, embeddings)

# --- Spara index lokalt ---
vectorstore.save_local("faiss_index")
print("FAISS-index sparat som 'faiss_index'")
print("\nKlart! Du kan nu ställa frågor om båda sågarna.")
