import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from urllib.parse import urlparse
import requests

# Lade Umgebungsvariablen aus config.env
load_dotenv('config.env')

blob_sas_url = os.getenv('BLOBSASURL')
print(f"Blob SAS URL: {blob_sas_url}")

if not blob_sas_url:
    print("❌ BLOBSASURL ist nicht gesetzt!")
    exit(1)

# Parse die URL
parsed_url = urlparse(blob_sas_url)
container_name = parsed_url.path.split('/')[-1]
print(f"Container Name: {container_name}")

# Teste verschiedene Zugriffsmethoden
print(f"\n🔍 Teste verschiedene Zugriffsmethoden:")

# Methode 1: Direkter HTTP-Zugriff
print(f"\n1️⃣ Direkter HTTP-Zugriff:")
try:
    response = requests.get(blob_sas_url, timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✅ HTTP-Zugriff erfolgreich!")
    else:
        print(f"❌ HTTP-Zugriff fehlgeschlagen: {response.status_code}")
        print(f"Response: {response.text[:300]}...")
except Exception as e:
    print(f"❌ HTTP-Zugriff Fehler: {e}")

# Methode 2: Azure Blob Service Client mit verschiedenen Initialisierungen
print(f"\n2️⃣ Azure Blob Service Client Test:")

# Versuche 1: Mit vollständiger SAS URL
try:
    blob_service_client = BlobServiceClient(account_url=blob_sas_url)
    container_client = blob_service_client.get_container_client(container_name)
    
    # Teste einfache Operation
    blobs = list(container_client.list_blobs())
    print(f"✅ Erfolgreich! {len(blobs)} Blobs gefunden")
    
    for i, blob in enumerate(blobs[:5], 1):
        print(f"  {i}. {blob.name}")
    
    if len(blobs) > 5:
        print(f"  ... und {len(blobs) - 5} weitere")
        
except Exception as e:
    print(f"❌ Fehler mit vollständiger SAS URL: {e}")

# Versuche 2: Mit geteilter URL (Account URL + SAS Token)
print(f"\n3️⃣ Geteilte URL Methode:")
try:
    # Teile die URL in Account URL und SAS Token
    account_url = blob_sas_url.split('?')[0]
    sas_token = blob_sas_url.split('?')[1]
    
    print(f"Account URL: {account_url}")
    print(f"SAS Token: {sas_token[:50]}...")
    
    blob_service_client = BlobServiceClient(account_url=account_url, credential=sas_token)
    container_client = blob_service_client.get_container_client(container_name)
    
    # Teste einfache Operation
    blobs = list(container_client.list_blobs())
    print(f"✅ Erfolgreich! {len(blobs)} Blobs gefunden")
    
    for i, blob in enumerate(blobs[:5], 1):
        print(f"  {i}. {blob.name}")
    
    if len(blobs) > 5:
        print(f"  ... und {len(blobs) - 5} weitere")
        
except Exception as e:
    print(f"❌ Fehler mit geteilter URL: {e}")

# Versuche 3: Prüfe ob Container existiert
print(f"\n4️⃣ Container-Existenz Test:")
try:
    blob_service_client = BlobServiceClient(account_url=blob_sas_url)
    container_client = blob_service_client.get_container_client(container_name)
    
    # Teste Container-Existenz
    exists = container_client.exists()
    print(f"Container existiert: {exists}")
    
    if exists:
        properties = container_client.get_container_properties()
        print(f"Container erstellt: {properties.created}")
        print(f"Container letzte Änderung: {properties.last_modified}")
    
except Exception as e:
    print(f"❌ Container-Existenz Test Fehler: {e}")

