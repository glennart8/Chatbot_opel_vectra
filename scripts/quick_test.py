# -*- coding: utf-8 -*-
"""
Snabbtest - Skicka EN fråga till backend
Användning: python scripts/quick_test.py "Hur startar jag motorsågen?"
"""
import requests
import sys
import json

API_URL = "http://localhost:8000/api/v1/chat/"

if len(sys.argv) < 2:
    print("❌ Ingen fråga angiven!")
    print(f"\nAnvändning:")
    print(f'  python scripts/quick_test.py "Hur startar jag motorsågen?"')
    sys.exit(1)

question = " ".join(sys.argv[1:])

print(f"❓ Fråga: {question}")
print(f"🔄 Skickar till {API_URL}...\n")

try:
    response = requests.post(
        API_URL,
        json={"question": question},
        timeout=60
    )

    if response.status_code == 200:
        data = response.json()
        print("✅ Svar:")
        print("━" * 60)
        print(data['answer'])
        print("━" * 60)
    else:
        print(f"❌ Fel {response.status_code}:")
        print(response.text)

except requests.exceptions.ConnectionError:
    print("❌ Kan inte ansluta till backend!")
    print("   Starta: python -m uvicorn backend.app.main:app --reload")
except Exception as e:
    print(f"❌ Fel: {e}")
