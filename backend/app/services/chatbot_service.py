# -*- coding: utf-8 -*-
"""
Chatbot service - migrerad logik från chatbot.py
"""
import sys
import io
import logging
import os
from typing import Optional
from dotenv import load_dotenv

# Ladda .env filen
load_dotenv()

# Fixa encoding för svenska tecken
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import google.generativeai as genai

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class ChatbotService:
    """
    Chatbot service som hanterar FAISS vektordatabas och AI-modell
    """

    def __init__(self):
        self.embeddings: Optional[HuggingFaceEmbeddings] = None
        self.vectorstore: Optional[FAISS] = None
        self.gemini_model = None
        self._model_loaded = False

    def initialize(self):
        """Initialisera modeller och vektordatabas"""
        try:
            logger.info("Initialiserar chatbot service...")

            # Ladda embeddings
            logger.info(f"Laddar embeddings: {settings.EMBEDDING_MODEL}")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL
            )

            # Ladda FAISS index
            logger.info(f"Laddar FAISS index från: {settings.FAISS_INDEX_PATH}")
            self.vectorstore = FAISS.load_local(
                settings.FAISS_INDEX_PATH,
                self.embeddings,
                allow_dangerous_deserialization=True
            )

            # Konfigurera Google Gemini API
            logger.info("Konfigurerar Google Gemini API...")
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY saknas i .env filen")

            genai.configure(api_key=api_key)

            # Prova olika modeller i fallback-ordning
            models_to_try = [
                'gemini-2.5-flash',
                'gemini-1.5-flash-latest',
                'gemini-1.5-pro-latest',
                'models/gemini-1.5-flash',
                'models/gemini-2.5-flash',
                'models/gemini-pro'
            ]

            model_loaded = False
            for model_name in models_to_try:
                try:
                    logger.info(f"Försöker ladda modell: {model_name}")
                    self.gemini_model = genai.GenerativeModel(model_name)
                    # Testa att modellen fungerar med en enkel fråga
                    test_response = self.gemini_model.generate_content("Test")
                    logger.info(f"Modell {model_name} laddad!")
                    model_loaded = True
                    break
                except Exception as e:
                    logger.warning(f"Kunde inte ladda {model_name}: {e}")
                    continue

            if not model_loaded:
                raise ValueError("Ingen Gemini-modell kunde laddas. Kontrollera din API-nyckel.")

            self._model_loaded = True
            logger.info("Chatbot service initialiserad med Gemini API!")

        except Exception as e:
            logger.error(f"Fel vid initialisering av chatbot: {e}")
            raise

    def is_ready(self) -> bool:
        """Kontrollera om modellen är redo"""
        return self._model_loaded

    def _extract_keywords(self, query: str) -> list:
        """
        Extrahera nyckelord från frågan för hybrid sökning.
        Mappar vanliga frågor till tekniska termer.
        """
        query_lower = query.lower()
        keywords = []

        # Mappning av vanliga frågeord till tekniska termer
        keyword_map = {
            'väger': ['vikt', 'kg'],
            'vikt': ['vikt', 'kg'],
            'tung': ['vikt', 'kg'],
            'effekt': ['motoreffekt', 'kw', 'watt'],
            'stark': ['motoreffekt', 'kw', 'watt'],
            'tank': ['tankvolym', 'liter', 'cm3'],
            'bränsle': ['bränsle', 'tank', 'bensin'],
            'olja': ['olja', 'tank', 'kedjeolja'],
            'ljud': ['ljudnivå', 'db', 'decibel'],
            'buller': ['buller', 'ljudeffekt', 'db'],
            'vibration': ['vibration', 'm/s'],
            'kedja': ['kedja', 'svärd', 'sågkedja', 'delning', 'tum', 'skärlängd', 'svärdslängd'],
            'svärd': ['svärd', 'tum', 'cm', 'svärdslängd', 'skärlängd', 'delning'],
            'typ': ['typ', 'modell', 'specifikation', 'rekommenderad'],
            'delning': ['delning', 'tum', 'mm', 'kedja'],
            'specifikation': ['motoreffekt', 'vikt', 'tank', 'specifikation'],
            'teknisk': ['motoreffekt', 'vikt', 'tank', 'teknisk'],
            'förvar': ['förvaring', 'transport', 'långtidsförvaring'],
            'transport': ['transport', 'förvaring'],
            'starta': ['starta', 'start', 'motor'],
            'stopp': ['stanna', 'stoppa', 'motor'],
            'filter': ['luftfilter', 'bränslefilter', 'filter'],
            'rengör': ['rengör', 'rensa', 'underhåll'],
            'underhåll': ['underhåll', 'service', 'rengör'],
            'problem': ['felsökning', 'problem', 'startar inte'],
            'funkar inte': ['felsökning', 'problem', 'startar inte'],
            'kassera': ['kassering', 'avfall', 'miljö'],
            # Nya för batteridriven såg och jämförelser
            'batteri': ['batteri', 'laddning', 'laddare', 'ah', 'volt'],
            'ladda': ['ladda', 'laddning', 'laddare', 'batteri'],
            'jämför': ['435', '542i', 'modell', 'specifikation'],
            'skillnad': ['435', '542i', 'modell', 'specifikation'],
            '435': ['435', 'bensin', 'modell'],
            '542': ['542i', 'batteri', 'modell'],
            'bensin': ['bensin', 'bränsle', '435', 'tank'],
            'el': ['batteri', 'laddning', '542i', 'elektrisk'],
        }

        for word, terms in keyword_map.items():
            if word in query_lower:
                keywords.extend(terms)

        return list(set(keywords))  # Ta bort dubbletter

    def ask_question(self, query: str) -> str:
        """
        Ställ en fråga till chatboten

        Args:
            query: Användarens fråga

        Returns:
            Chatbotens svar
        """
        if not self.is_ready():
            raise RuntimeError("Chatbot är inte initialiserad. Kör initialize() först.")

        try:
            # Hämta relevanta dokument från FAISS (semantisk sökning)
            docs = self.vectorstore.similarity_search(query, k=settings.NUM_DOCUMENTS)

            # Hybrid sökning: Lägg till nyckelordssökning för tekniska termer
            keywords = self._extract_keywords(query)
            keyword_docs = []
            if keywords:
                all_docs = list(self.vectorstore.docstore._dict.values())
                for doc in all_docs:
                    content_lower = doc.page_content.lower()
                    # Räkna hur många nyckelord som matchar
                    match_count = sum(1 for kw in keywords if kw in content_lower)
                    # Kräv minst 1 nyckelordsmatchning för att prioritera
                    if match_count >= 1:
                        if doc not in docs:
                            keyword_docs.append((match_count, doc))
                            logger.info(f"Lade till dokument via nyckelordssökning ({match_count} matchningar): {doc.page_content[:50]}...")

            # Sortera efter antal matchningar (flest först) och prioritera
            keyword_docs.sort(key=lambda x: x[0], reverse=True)
            keyword_docs = [doc for _, doc in keyword_docs]
            docs = keyword_docs + docs

            # Logga vilka dokument som hittades (för debugging)
            logger.info(f"Hittade {len(docs)} dokument för frågan: {query[:50]}...")
            for i, doc in enumerate(docs[:8]):  # Logga max 8
                logger.info(f"Dokument {i+1}: {doc.page_content[:100]}...")

            # Bygg context från dokument
            context = ""
            for doc in docs:
                if len(context) + len(doc.page_content) < settings.MAX_CONTEXT_LENGTH:
                    context += doc.page_content + "\n"
                else:
                    # Ta med en del av det sista dokumentet för att fylla ut
                    remaining_length = settings.MAX_CONTEXT_LENGTH - len(context)
                    if remaining_length > 0:
                        context += doc.page_content[:remaining_length]
                    break

            # Rensa context
            cleaned_context = context.replace('\n', ' ').strip()

            # Skapa prompt för Gemini
            prompt = f"""Du är en vänlig och kunnig expert på Husqvarna motorsågar. Du hjälper användare med deras frågor på ett avslappnat och naturligt sätt, som om du pratar med en kompis som behöver hjälp.

Du har tillgång till information om FLERA Husqvarna-modeller:
- Husqvarna 435 (bensindriven)
- Husqvarna 542i XP (batteridriven)

REGLER FÖR DIN TON:
- Var personlig och vänlig, men inte överdriven
- Använd vardagligt språk, undvik stelt "kundtjänst-språk"
- Ge konkreta och praktiska svar
- Om du ger instruktioner, gör dem enkla att följa
- Det är okej att vara lite entusiastisk om motorsågar!

REGLER FÖR JÄMFÖRELSER:
- Om användaren frågar om en specifik modell, fokusera på den
- Om användaren vill jämföra, lyft fram skillnader tydligt
- Ange alltid vilken modell informationen gäller
- Kontexten är taggad med [MODELL: ...] för att visa vilken såg texten gäller

KONTEXT FRÅN BRUKSANVISNINGAR:
{cleaned_context}

ANVÄNDARENS FRÅGA:
{query}

Svara på svenska. Om informationen inte finns i kontexten, var ärlig med det men försök ändå vara hjälpsam."""

            # Generera svar med Gemini
            response = self.gemini_model.generate_content(prompt)
            answer = response.text

            return answer

        except Exception as e:
            logger.error(f"Fel vid frågehantering: {e}")
            raise

# Singleton instance
chatbot_service = ChatbotService()
