import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from urllib.parse import urlparse
import requests

# Lade Umgebungsvariablen aus config.env
load_dotenv('config.env')

blob_sas_url = os.getenv('BLOBSASURL')
print(f"Blob SAS URL: {blob_sas_url}")
print(f"URL Länge: {len(blob_sas_url) if blob_sas_url else 'None'}")

if not blob_sas_url:
    print("❌ BLOBSASURL ist nicht gesetzt!")
    exit(1)

# Parse die URL
parsed_url = urlparse(blob_sas_url)
print(f"\nURL-Analyse:")
print(f"Schema: {parsed_url.scheme}")
print(f"Netzwerk: {parsed_url.netloc}")
print(f"Pfad: {parsed_url.path}")
print(f"Query: {parsed_url.query[:50]}..." if len(parsed_url.query) > 50 else f"Query: {parsed_url.query}")

# Extrahiere Container-Name
container_name = parsed_url.path.split('/')[-1]
print(f"Container Name: {container_name}")

# Teste HTTP-Zugriff
print(f"\nHTTP-Test:")
try:
    response = requests.get(blob_sas_url, timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✅ HTTP-Zugriff erfolgreich!")
    else:
        print(f"❌ HTTP-Zugriff fehlgeschlagen: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
except Exception as e:
    print(f"❌ HTTP-Zugriff Fehler: {e}")

# Teste Container Client direkt (KORREKT für Container-SAS URLs)
print(f"\nContainer Client Test (KORREKT):")
try:
    from azure.storage.blob import ContainerClient
    
    # Verwende ContainerClient direkt mit der Container-SAS URL
    container_client = ContainerClient.from_container_url(blob_sas_url)
    print("✅ ContainerClient erfolgreich erstellt")
    
    # Teste Container-Zugriff
    print("Teste Container-Zugriff...")
    blobs = container_client.list_blobs()
    
    blob_count = 0
    for blob in blobs:
        blob_count += 1
        print(f"  Blob {blob_count}: {blob.name}")
        if blob_count >= 5:  # Nur erste 5 Blobs anzeigen
            print("  ... (weitere Blobs vorhanden)")
            break
    
    print(f"✅ Container-Zugriff erfolgreich! {blob_count} Blobs gefunden")
    
except Exception as e:
    print(f"❌ Container Client Fehler: {e}")
    print(f"Fehler-Typ: {type(e).__name__}")

# Teste spezifische Blob-Operationen
print(f"\nSpezifische Blob-Operationen Test:")
try:
    # Verwende den bereits erstellten ContainerClient
    container_client = ContainerClient.from_container_url(blob_sas_url)
    
    # Teste ob Container existiert
    properties = container_client.get_container_properties()
    print(f"✅ Container existiert: {properties.name}")
    print(f"Container erstellt: {properties.created}")
    print(f"Container letzte Änderung: {properties.last_modified}")
    
except Exception as e:
    print(f"❌ Container-Operationen Fehler: {e}")
