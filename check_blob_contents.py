import os
import json
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from urllib.parse import urlparse

# Lade Umgebungsvariablen aus config.env
load_dotenv('config.env')

blob_sas_url = os.getenv('BLOBSASURL')
print(f"Blob URL: {blob_sas_url}")

# Erstelle BlobServiceClient mit SAS URL
blob_service_client = BlobServiceClient(account_url=blob_sas_url)

# Parse die SAS URL um Container-Name zu extrahieren
parsed_url = urlparse(blob_sas_url)
container_name = parsed_url.path.split('/')[-1]
if not container_name:
    container_name = "container2"  # Fallback falls Container-Name nicht extrahiert werden kann

print(f"Container Name: {container_name}")

# Erstelle Container Client
container_client = blob_service_client.get_container_client(container_name)

# Liste alle Blobs im Container
print("\nAktuelle Blobs im Container:")
blobs = container_client.list_blobs()
blob_count = 0
for blob in blobs:
    blob_count += 1
    print(f"{blob_count}: {blob.name}")
    if blob_count >= 20:  # Nur erste 20 Blobs anzeigen
        print("... (weitere Blobs vorhanden)")
        break

print(f"\nGesamt: {blob_count} Blobs gefunden")
