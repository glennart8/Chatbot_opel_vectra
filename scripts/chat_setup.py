from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from pypdf import PdfReader
from dotenv import load_dotenv
import os

load_dotenv()

# --- Läs PDF och rensa text ---
pdf_file = "data/husqvarna435.pdf"  # Husqvarna 435 manual
reader = PdfReader(pdf_file)

text = ""
print(f"Läser in text från PDF: {pdf_file}")
print(f"Totalt antal sidor i PDF: {len(reader.pages)}")

# DEFINIERA SIDINTERVALL - Svenska manualen börjar på sida 112
START_INDEX = 111   # Index för Sida 112 (0-baserat index)
END_INDEX = len(reader.pages)    # Läs till slutet av PDF:en

print(f"Läser svenska sektionen: Sida {START_INDEX + 1} till {END_INDEX}")

# Ändra loopen för att iterera över sidor i intervallet [START_INDEX, END_INDEX)
for i in range(START_INDEX, END_INDEX):
    if i < len(reader.pages):
        page = reader.pages[i]
        page_text = page.extract_text()

        if page_text:
            # Ta bort onödiga radbrytningar
            page_text = page_text.replace("\n", " ").strip()
            text += page_text + "\n"
        else:
            # Kan vara bra att se om någon sida är tom p.g.a. OCR-problem
            print(f"Varning: Sida {i+1} gav ingen text vid extraktion.")
    else:
        # Detta bör inte hända
        print(f"Varning: Försökte läsa sida {i+1}, men PDF:en slutade.")
        break

print(f"Totalt antal tecken extraherade: {len(text)}")

# --- Skapa Document-objekt ---
docs = [Document(page_content=text)]

# --- Dela upp i chunks ---
# Större chunks för att behålla mer kontext (t.ex. hela felsökningstabeller)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
docs_split = text_splitter.split_documents(docs)
print(f"Antal chunks: {len(docs_split)}")

# --- Skapa embeddings (lokalt HuggingFace, gratis) ---
print("Skapar embeddings med HuggingFace...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2")

# --- Skapa FAISS-index ---
vectorstore = FAISS.from_documents(docs_split, embeddings)

# --- Spara index lokalt ---
vectorstore.save_local("faiss_index")
print("FAISS-index sparat som 'faiss_index'")
