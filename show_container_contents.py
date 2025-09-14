import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from urllib.parse import urlparse

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

try:
    # Erstelle BlobServiceClient
    blob_service_client = BlobServiceClient(account_url=blob_sas_url)
    print("✅ BlobServiceClient erfolgreich erstellt")
    
    # Erstelle Container Client
    container_client = blob_service_client.get_container_client(container_name)
    print("✅ Container Client erfolgreich erstellt")
    
    # Zeige Container-Eigenschaften
    print(f"\n📁 Container-Eigenschaften:")
    properties = container_client.get_container_properties()
    print(f"Name: {properties.name}")
    print(f"Erstellt: {properties.created}")
    print(f"Letzte Änderung: {properties.last_modified}")
    print(f"ETag: {properties.etag}")
    
    # Liste alle Blobs im Container
    print(f"\n📄 Blobs im Container '{container_name}':")
    blobs = container_client.list_blobs()
    
    blob_count = 0
    total_size = 0
    
    for blob in blobs:
        blob_count += 1
        size_mb = blob.size / (1024 * 1024) if blob.size else 0
        total_size += blob.size if blob.size else 0
        
        print(f"{blob_count:2d}. {blob.name}")
        print(f"     Größe: {size_mb:.2f} MB")
        print(f"     Letzte Änderung: {blob.last_modified}")
        print(f"     Content-Type: {blob.content_settings.content_type if blob.content_settings else 'Nicht verfügbar'}")
        print()
    
    total_size_mb = total_size / (1024 * 1024)
    print(f"📊 Zusammenfassung:")
    print(f"   Gesamt Blobs: {blob_count}")
    print(f"   Gesamtgröße: {total_size_mb:.2f} MB")
    
    if blob_count == 0:
        print("   ⚠️  Container ist leer!")
    
except Exception as e:
    print(f"❌ Fehler beim Zugriff auf Container: {e}")
    print(f"Fehler-Typ: {type(e).__name__}")
    
    # Zusätzliche Debug-Informationen
    if hasattr(e, 'response'):
        print(f"Response Status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
        print(f"Response Text: {e.response.text[:200] if hasattr(e.response, 'text') else 'N/A'}")

