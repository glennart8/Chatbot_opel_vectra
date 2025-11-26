# -*- coding: utf-8 -*-
"""
Test backend API direkt utan frontend
Kör detta script för att chatta med backend via API
"""
import requests
import json
import sys
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
SESSION_ID = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

def check_health():
    """Kontrollera att backend är igång"""
    try:
        response = requests.get(f"{API_BASE_URL}/health/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend är igång!")
            print(f"   Version: {data['version']}")
            if data['model_loaded']:
                print(f"   Modell laddad: Ja")
            else:
                print(f"   Modell laddad: Nej")
                print(f"   ⚠️  Modellen laddar vid första frågan (kan ta 1-2 min)")
            return True  # Returnera True även om modellen inte är laddad än
        else:
            print(f"❌ Backend svarar med fel: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Kan inte ansluta till backend!")
        print("   Starta backend med: python -m uvicorn backend.app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Fel: {e}")
        return False

def ask_question(question: str):
    """Ställ en fråga till chatboten"""
    try:
        print(f"\n🤔 Skickar fråga till backend...")

        # Skapa request
        payload = {
            "question": question,
            "session_id": SESSION_ID
        }

        # Skicka POST request
        response = requests.post(
            f"{API_BASE_URL}/chat/",
            json=payload,
            timeout=60  # AI-modellen kan ta tid
        )

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Svar från backend:")
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"{data['answer']}")
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"⏱️  Tidsstämpel: {data['timestamp']}")
            return True
        else:
            print(f"\n❌ Fel {response.status_code}: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("\n❌ Request timeout! AI-modellen tar för lång tid (>60 sek)")
        return False
    except Exception as e:
        print(f"\n❌ Fel vid anrop: {e}")
        return False

def main():
    """Huvudfunktion"""
    print("=" * 50)
    print("  Backend API Test - Husqvarna Chatbot")
    print("=" * 50)
    print()

    # Kontrollera att backend är igång
    if not check_health():
        print("\n💡 Tips:")
        print("   1. Starta backend: python -m uvicorn backend.app.main:app --reload")
        print("   2. Eller kör Docker: docker-compose up backend")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("  Redo att chatta! Skriv 'exit' för att avsluta")
    print("=" * 50)

    # Interaktiv loop
    while True:
        try:
            # Läs input från användaren
            print("\n")
            question = input("❓ Din fråga: ").strip()

            # Kolla om användaren vill avsluta
            if question.lower() in ['exit', 'quit', 'q', 'avsluta']:
                print("\n👋 Hej då!")
                break

            # Hoppa över tomma frågor
            if not question:
                continue

            # Ställ frågan till backend
            ask_question(question)

        except KeyboardInterrupt:
            print("\n\n👋 Avbruten av användaren. Hej då!")
            break
        except Exception as e:
            print(f"\n❌ Oväntat fel: {e}")
            continue

if __name__ == "__main__":
    main()
