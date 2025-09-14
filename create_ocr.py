import os
import json
from dotenv import load_dotenv
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient
from urllib.parse import urlparse

# Lade Umgebungsvariablen aus config.env
load_dotenv('config.env')

# Azure Document Intelligence Konfiguration
endpoint = os.getenv('DOCUMENTINTELLIGENCE_ENDPOINT')
key = os.getenv('DOCUMENTINTELLIGENCE_API_KEY')
blob_sas_url = os.getenv('BLOBSASURL')

# Erstelle DocumentIntelligenceClient
client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

# Erstelle BlobServiceClient mit SAS URL
blob_service_client = BlobServiceClient(account_url=blob_sas_url)

def create_ocr(pdf_path, output_path=None):
    """
    Erstellt OCR-Daten aus einer PDF-Datei und speichert sie als JSON.
    
    Args:
        pdf_path (str): Pfad zur PDF-Datei
        output_path (str, optional): Pfad für die Ausgabedatei. 
                                   Wenn nicht angegeben, wird der PDF-Pfad mit .ocr.json erweitert
    
    Returns:
        str: Pfad zur erstellten OCR-JSON-Datei
    """
    # Bestimme Ausgabepfad
    if output_path is None:
        output_path = pdf_path + ".ocr.json"
    
    try:
        # Öffne PDF-Datei und führe OCR-Analyse durch
        with open(pdf_path, "rb") as f:
            poller = client.begin_analyze_document(
                model_id="prebuilt-layout",
                body=f
            )
            result = poller.result()
        
        # Speichere das Ergebnis als JSON
        with open(output_path, "w", encoding="utf-8") as out_file:
            json.dump(result.as_dict(), out_file, ensure_ascii=False, indent=2)
        
        print(f"OCR-Daten erfolgreich erstellt: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Fehler beim Erstellen der OCR-Daten: {e}")
        raise


def get_pdf_blobs_without_ocr():
    """
    Findet alle PDF-Dateien im Blob Storage, die noch keine entsprechende OCR-Datei haben.
    
    Returns:
        list: Liste von Blob-Namen (PDF-Dateien ohne OCR)
    """
    try:
        # Parse die SAS URL um Container-Name zu extrahieren
        parsed_url = urlparse(blob_sas_url)
        container_name = parsed_url.path.split('/')[-1]
        if not container_name:
            container_name = "container2"  # Fallback falls Container-Name nicht extrahiert werden kann
        
        # Erstelle Container Client
        container_client = blob_service_client.get_container_client(container_name)
        
        # Liste alle Blobs im Container
        blobs = container_client.list_blobs()
        
        pdf_blobs = []
        ocr_blobs = set()
        
        # Trenne PDF-Dateien und OCR-Dateien
        for blob in blobs:
            blob_name = blob.name.lower()
            if blob_name.endswith('.pdf'):
                pdf_blobs.append(blob.name)
            elif blob_name.endswith('.ocr.json'):
                # Entferne .ocr.json Extension um den ursprünglichen PDF-Namen zu bekommen
                original_pdf = blob.name[:-9]  # Entfernt ".ocr.json"
                ocr_blobs.add(original_pdf)
        
        # Finde PDF-Dateien ohne entsprechende OCR-Datei
        pdfs_without_ocr = [pdf for pdf in pdf_blobs if pdf not in ocr_blobs]
        
        print(f"Gefunden: {len(pdf_blobs)} PDF-Dateien, {len(ocr_blobs)} OCR-Dateien")
        print(f"PDF-Dateien ohne OCR: {len(pdfs_without_ocr)}")
        
        return pdfs_without_ocr
        
    except Exception as e:
        print(f"Fehler beim Durchsuchen des Blob Storage: {e}")
        raise


def download_blob_to_temp(blob_name, temp_path):
    """
    Lädt eine Blob-Datei in einen temporären lokalen Pfad herunter.
    
    Args:
        blob_name (str): Name der Blob-Datei
        temp_path (str): Lokaler Pfad für die temporäre Datei
    
    Returns:
        str: Pfad zur heruntergeladenen Datei
    """
    try:
        # Parse die SAS URL um Container-Name zu extrahieren
        parsed_url = urlparse(blob_sas_url)
        container_name = parsed_url.path.split('/')[-1]
        if not container_name:
            container_name = "container2"  # Fallback falls Container-Name nicht extrahiert werden kann
        
        # Erstelle Container Client
        container_client = blob_service_client.get_container_client(container_name)
        
        # Lade Blob herunter
        with open(temp_path, "wb") as download_file:
            download_file.write(container_client.download_blob(blob_name).readall())
        
        print(f"Blob heruntergeladen: {blob_name} -> {temp_path}")
        return temp_path
        
    except Exception as e:
        print(f"Fehler beim Herunterladen von {blob_name}: {e}")
        raise


def upload_ocr_to_blob(local_ocr_path, blob_name):
    """
    Lädt eine OCR-JSON-Datei in den Blob Storage hoch.
    
    Args:
        local_ocr_path (str): Lokaler Pfad zur OCR-JSON-Datei
        blob_name (str): Name für die Blob-Datei (mit .ocr.json Extension)
    """
    try:
        # Parse die SAS URL um Container-Name zu extrahieren
        parsed_url = urlparse(blob_sas_url)
        container_name = parsed_url.path.split('/')[-1]
        if not container_name:
            container_name = "container2"  # Fallback falls Container-Name nicht extrahiert werden kann
        
        # Erstelle Container Client
        container_client = blob_service_client.get_container_client(container_name)
        
        # Lade OCR-Datei hoch
        with open(local_ocr_path, "rb") as data:
            container_client.upload_blob(name=blob_name, data=data, overwrite=True)
        
        print(f"OCR-Datei hochgeladen: {local_ocr_path} -> {blob_name}")
        
    except Exception as e:
        print(f"Fehler beim Hochladen von {local_ocr_path}: {e}")
        raise


def process_missing_ocr_files():
    """
    Verarbeitet alle PDF-Dateien im Blob Storage, die noch keine OCR-Datei haben.
    """
    import tempfile
    import shutil
    
    try:
        # Finde PDF-Dateien ohne OCR
        pdfs_without_ocr = get_pdf_blobs_without_ocr()
        
        if not pdfs_without_ocr:
            print("Alle PDF-Dateien haben bereits OCR-Dateien!")
            return
        
        print(f"Verarbeite {len(pdfs_without_ocr)} PDF-Dateien...")
        
        # Erstelle temporäres Verzeichnis
        temp_dir = tempfile.mkdtemp()
        
        try:
            for i, pdf_blob_name in enumerate(pdfs_without_ocr, 1):
                print(f"\n[{i}/{len(pdfs_without_ocr)}] Verarbeite: {pdf_blob_name}")
                
                # Erstelle temporäre Pfade
                temp_pdf_path = os.path.join(temp_dir, os.path.basename(pdf_blob_name))
                temp_ocr_path = temp_pdf_path + ".ocr.json"
                
                # OCR-Datei Name für Blob
                ocr_blob_name = pdf_blob_name + ".ocr.json"
                
                try:
                    # Lade PDF herunter
                    download_blob_to_temp(pdf_blob_name, temp_pdf_path)
                    
                    # Erstelle OCR
                    create_ocr(temp_pdf_path, temp_ocr_path)
                    
                    # Lade OCR-Datei hoch
                    upload_ocr_to_blob(temp_ocr_path, ocr_blob_name)
                    
                    print(f"✓ Erfolgreich verarbeitet: {pdf_blob_name}")
                    
                except Exception as e:
                    print(f"✗ Fehler bei {pdf_blob_name}: {e}")
                    continue
                
                finally:
                    # Lösche temporäre Dateien
                    if os.path.exists(temp_pdf_path):
                        os.remove(temp_pdf_path)
                    if os.path.exists(temp_ocr_path):
                        os.remove(temp_ocr_path)
        
        finally:
            # Lösche temporäres Verzeichnis
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        print(f"\nVerarbeitung abgeschlossen!")
        
    except Exception as e:
        print(f"Fehler bei der Verarbeitung: {e}")
        raise


def process_local_pdfs():
    """
    Verarbeitet alle PDF-Dateien im lokalen Verzeichnis pohlheim_protokolle\Stavo,
    die noch keine OCR-Datei haben.
    """
    import glob
    
    # Verzeichnis mit PDF-Dateien
    pdf_directory = "pohlheim_protokolle\\Stavo"
    
    if not os.path.exists(pdf_directory):
        print(f"Verzeichnis {pdf_directory} existiert nicht!")
        return
    
    # Finde alle PDF-Dateien
    pdf_pattern = os.path.join(pdf_directory, "*.pdf")
    pdf_files = glob.glob(pdf_pattern)
    
    if not pdf_files:
        print(f"Keine PDF-Dateien in {pdf_directory} gefunden!")
        return
    
    print(f"Gefunden: {len(pdf_files)} PDF-Dateien in {pdf_directory}")
    
    # Finde PDF-Dateien ohne OCR
    pdfs_without_ocr = []
    for pdf_file in pdf_files:
        ocr_file = pdf_file + ".ocr.json"
        if not os.path.exists(ocr_file):
            pdfs_without_ocr.append(pdf_file)
    
    if not pdfs_without_ocr:
        print("Alle PDF-Dateien haben bereits OCR-Dateien!")
        return
    
    print(f"PDF-Dateien ohne OCR: {len(pdfs_without_ocr)}")
    
    # Verarbeite PDF-Dateien ohne OCR
    for i, pdf_file in enumerate(pdfs_without_ocr, 1):
        print(f"\n[{i}/{len(pdfs_without_ocr)}] Verarbeite: {os.path.basename(pdf_file)}")
        
        try:
            # Erstelle OCR
            ocr_file = pdf_file + ".ocr.json"
            create_ocr(pdf_file, ocr_file)
            print(f"✓ Erfolgreich verarbeitet: {os.path.basename(pdf_file)}")
            
        except Exception as e:
            print(f"✗ Fehler bei {os.path.basename(pdf_file)}: {e}")
            continue
    
    print(f"\nVerarbeitung abgeschlossen!")


# Beispiel-Verwendung:
if __name__ == "__main__":
    # Verarbeite lokale PDF-Dateien im pohlheim_protokolle\Stavo Verzeichnis
    process_local_pdfs()
    
    # Oder alle PDF-Dateien ohne OCR im Blob Storage verarbeiten:
    # process_missing_ocr_files()
    
    # Oder einzelne PDF-Datei verarbeiten:
    # create_ocr("protokoll1.pdf")
