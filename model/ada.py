from openai import OpenAI
import os
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus config.env
load_dotenv('../config.env')

# Erstelle OpenAI Client
api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    print("❌ OPENAI_API_KEY ist nicht in der config.env gesetzt!")
    print("Bitte fügen Sie einen gültigen OpenAI API Key hinzu.")
    exit(1)

print(f"API Key gefunden: {api_key[:10]}...")

try:
    client = OpenAI(api_key=api_key)
    
    # Erstelle Embedding mit der neuen API
    response = client.embeddings.create(
        input="Dein Dokumententext",
        model="text-embedding-ada-002"
    )
    
    embedding = response.data[0].embedding
    print(f"✅ Embedding erfolgreich erstellt! Dimension: {len(embedding)}")
    print(f"Erste 5 Werte: {embedding[:5]}")
    
except Exception as e:
    print(f"❌ Fehler beim Erstellen des Embeddings: {e}")
    print("Mögliche Ursachen:")
    print("- Ungültiger API Key")
    print("- Keine Internetverbindung")
    print("- OpenAI Service nicht verfügbar")
