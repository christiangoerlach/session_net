import os
from dotenv import load_dotenv
from urllib.parse import urlparse

# Lade Umgebungsvariablen aus config.env
load_dotenv('config.env')

blob_url = os.getenv('BLOBSASURL')
print(f"Vollständige Blob SAS URL:")
print(f"{blob_url}")
print()

# Parse die URL
parsed = urlparse(blob_url)

print(f"URL-Analyse:")
print(f"Schema: {parsed.scheme}")
print(f"Netzwerk: {parsed.netloc}")
print(f"Pfad: {parsed.path}")
print(f"Query Parameter: {parsed.query}")
print()

# Extrahiere Container-Name
container_name = parsed.path.split('/')[-1]
print(f"Container Name: {container_name}")
print()

# Zeige die Verzeichnisstruktur
print(f"Verzeichnisstruktur:")
print(f"Azure Storage Account: {parsed.netloc}")
print(f"Container: {container_name}")
print(f"Vollständiger Pfad: {parsed.path}")
print()

# Zeige SAS Token Details
if parsed.query:
    print(f"SAS Token Details:")
    query_params = parsed.query.split('&')
    for param in query_params:
        if '=' in param:
            key, value = param.split('=', 1)
            if key == 'sp':
                print(f"  Berechtigungen: {value}")
            elif key == 'st':
                print(f"  Start-Zeit: {value}")
            elif key == 'se':
                print(f"  End-Zeit: {value}")
            elif key == 'sv':
                print(f"  Service Version: {value}")
            elif key == 'sr':
                print(f"  Ressource: {value}")
            elif key == 'sig':
                print(f"  Signatur: {value[:20]}...")

