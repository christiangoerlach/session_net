import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from urllib.parse import urlparse

# Lade Umgebungsvariablen aus config.env
load_dotenv('config.env')

blob_sas_url = os.getenv('BLOBSASURL')
print(f"Blob URL: {blob_sas_url}")

# Erstelle BlobServiceClient mit SAS URL - alternative Methode
try:
    blob_service_client = BlobServiceClient(account_url=blob_sas_url)
    print("BlobServiceClient erfolgreich erstellt")
except Exception as e:
    print(f"Fehler beim Erstellen des BlobServiceClient: {e}")
    exit(1)

# Parse die SAS URL um Container-Name zu extrahieren
parsed_url = urlparse(blob_sas_url)
container_name = parsed_url.path.split('/')[-1]
if not container_name:
    container_name = "container2"  # Fallback falls Container-Name nicht extrahiert werden kann

print(f"Container Name: {container_name}")

try:
    # Erstelle Container Client
    container_client = blob_service_client.get_container_client(container_name)
    
    # Liste alle Blobs im Container
    blobs = container_client.list_blobs()
    
    blob_count = 0
    for blob in blobs:
        blob_count += 1
        print(f"Blob {blob_count}: {blob.name}")
        if blob_count >= 5:  # Nur erste 5 Blobs anzeigen
            break
    
    print(f"Gefunden: {blob_count} Blobs (erste 5 angezeigt)")
    
except Exception as e:
    print(f"Fehler: {e}")
