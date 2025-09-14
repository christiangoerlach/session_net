import os
import json
from dotenv import load_dotenv
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

# Lade Umgebungsvariablen aus config.env
load_dotenv('config.env')

# Azure Document Intelligence Konfiguration
endpoint = os.getenv('DOCUMENTINTELLIGENCE_ENDPOINT')
key = os.getenv('DOCUMENTINTELLIGENCE_API_KEY')

print(f"Endpoint: {endpoint}")
print(f"Key vorhanden: {'Ja' if key else 'Nein'}")

# Erstelle DocumentIntelligenceClient
client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

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
            poller = client.begin_analyze_document("prebuilt-layout", document=f)
            result = poller.result()
        
        # Speichere das Ergebnis als JSON
        with open(output_path, "w", encoding="utf-8") as out_file:
            json.dump(result.to_dict(), out_file, ensure_ascii=False, indent=2)
        
        print(f"OCR-Daten erfolgreich erstellt: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Fehler beim Erstellen der OCR-Daten: {e}")
        raise

# Test der OCR-Funktionalität
if __name__ == "__main__":
    print("OCR-Funktionalität wird getestet...")
    
    # Suche nach PDF-Dateien im aktuellen Verzeichnis
    pdf_files = []
    for file in os.listdir('.'):
        if file.lower().endswith('.pdf'):
            pdf_files.append(file)
    
    if pdf_files:
        print(f"Gefundene PDF-Dateien: {pdf_files}")
        # Teste mit der ersten PDF-Datei
        test_pdf = pdf_files[0]
        print(f"Teste OCR mit: {test_pdf}")
        
        try:
            result_path = create_ocr(test_pdf)
            print(f"✓ OCR-Test erfolgreich! Ergebnis: {result_path}")
        except Exception as e:
            print(f"✗ OCR-Test fehlgeschlagen: {e}")
    else:
        print("Keine PDF-Dateien im aktuellen Verzeichnis gefunden.")
        print("Erstelle eine Test-PDF oder fügen Sie eine PDF-Datei hinzu.")

