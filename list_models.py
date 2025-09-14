import os
from dotenv import load_dotenv
from azure.ai.documentintelligence import DocumentIntelligenceAdministrationClient
from azure.core.credentials import AzureKeyCredential

# Lade Umgebungsvariablen aus config.env
load_dotenv('config.env')

endpoint = os.getenv('DOCUMENTINTELLIGENCE_ENDPOINT')
key = os.getenv('DOCUMENTINTELLIGENCE_API_KEY')

print(f"Endpoint: {endpoint}")
print(f"Key vorhanden: {'Ja' if key else 'Nein'}")

# Erstelle DocumentIntelligenceAdministrationClient
client = DocumentIntelligenceAdministrationClient(endpoint=endpoint, credential=AzureKeyCredential(key))

try:
    # Liste alle verfügbaren Modelle
    print("\nVerfügbare Modelle:")
    models = client.list_models()
    
    model_count = 0
    for model in models:
        model_count += 1
        print(f"{model_count}: {model.model_id}")
        if model_count >= 10:  # Nur erste 10 Modelle anzeigen
            print("... (weitere Modelle vorhanden)")
            break
    
    if model_count == 0:
        print("Keine Modelle gefunden.")
    
except Exception as e:
    print(f"Fehler beim Abrufen der Modelle: {e}")
