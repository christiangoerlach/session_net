import re
import os
import json
import base64
import PyPDF2
from datetime import datetime
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

# Lade Umgebungsvariablen - angepasst für training Verzeichnis
load_dotenv('../config.env')

class DocumentAnalyzer:
    def __init__(self):
        """Initialisiert den Document Intelligence Client"""
        self.endpoint = os.getenv('DOCUMENTINTELLIGENCE_ENDPOINT')
        self.api_key = os.getenv('DOCUMENTINTELLIGENCE_API_KEY')
        
        if not self.endpoint or not self.api_key:
            raise ValueError("Document Intelligence Endpoint und API Key müssen in config.env gesetzt werden")
        
        self.client = DocumentIntelligenceClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.api_key)
        )
    
    def convert_date_to_iso(self, date_string):
        """
        Konvertiert deutsches Datumsformat zu ISO-Format
        
        Args:
            date_string (str): Datum im Format "20.07.2023"
            
        Returns:
            str: ISO-Format "2023-07-20T00:00:00Z" oder ursprünglicher String bei Fehler
        """
        if not date_string:
            return ""
        
        try:
            # Versuche deutsches Format zu parsen (dd.mm.yyyy)
            if re.match(r'\d{1,2}\.\d{1,2}\.\d{4}', date_string):
                date_obj = datetime.strptime(date_string, '%d.%m.%Y')
                return date_obj.strftime('%Y-%m-%dT00:00:00Z')
            else:
                # Falls bereits ISO-Format oder anderes Format, zurückgeben
                return date_string
        except ValueError:
            # Bei Parsing-Fehlern ursprünglichen String zurückgeben
            return date_string
    
    def analyze_document(self, document_path):
        """
        Analysiert ein Dokument mit Azure Document Intelligence
        
        Args:
            document_path (str): Pfad zur PDF-Datei
            
        Returns:
            dict: Analyseergebnis von Document Intelligence
        """
        try:
            with open(document_path, "rb") as f:
                # Korrekte API-Verwendung für Version 1.0.2
                document_bytes = f.read()
                base64_content = base64.b64encode(document_bytes).decode('utf-8')
                
                # Verwende die korrekte API-Signatur mit body-Parameter
                body = {
                    "base64Source": base64_content
                }
                
                poller = self.client.begin_analyze_document(
                    "prebuilt-layout",
                    body=body
                )
                result = poller.result()
                return result
        except Exception as e:
            print(f"Fehler bei der Dokumentanalyse: {e}")
            print(f"Fehlerdetails: {type(e).__name__}")
            return None
    
    def extract_attendance_from_text(self, text):
        """
        Extrahiert Anwesenheitsliste aus Text mit Regex
        
        Args:
            text (str): Der zu analysierende Text
            
        Returns:
            dict: Strukturierte Anwesenheitsdaten
        """
        # Finde den Anwesenheitsbereich (zwischen "Anwesend:" und "Tagesordnung:")
        attendance_section = re.search(r"Anwesend:(.*?)Tagesordnung:", text, re.DOTALL | re.IGNORECASE)
        
        if not attendance_section:
            return {"error": "Anwesenheitsbereich nicht gefunden"}
        
        attendance_text = attendance_section.group(1)
        
        # Extrahiere Anwesende und Entschuldigte
        result = {
            "anwesend": [],
            "entschuldigt": [],
            "funktionen": {}
        }
        
        # Teile in Anwesend und Entschuldigt
        entschuldigt_match = re.search(r"Entschuldigt:(.*?)$", attendance_text, re.DOTALL | re.IGNORECASE)
        
        if entschuldigt_match:
            anwesend_text = attendance_text[:entschuldigt_match.start()]
            entschuldigt_text = entschuldigt_match.group(1)
        else:
            anwesend_text = attendance_text
            entschuldigt_text = ""
        
        # Parse Anwesende
        result["anwesend"] = self._parse_attendance_section(anwesend_text)
        
        # Parse Entschuldigte
        if entschuldigt_text:
            result["entschuldigt"] = self._parse_attendance_section(entschuldigt_text)
        
        return result
    
    def _parse_attendance_section(self, text):
        """
        Parst einen Anwesenheitsbereich und extrahiert Funktionen und Personen
        
        Args:
            text (str): Text des Anwesenheitsbereichs
            
        Returns:
            list: Liste der Funktionen mit Personen
        """
        functions = []
        current_function = None
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Ignoriere Seitennummern und Dokumentennamen
            if re.match(r"^Seite \d+ von \d+$", line) or re.match(r"^STV/\d+/\d+-\d+$", line):
                continue
                
            # Prüfe ob es eine Funktionsüberschrift ist (erweitert um "Von der Verwaltung:")
            if re.match(r"^(Von der|Vom|Schriftführer)", line, re.IGNORECASE):
                current_function = line
                functions.append({
                    "funktion": current_function,
                    "personen": []
                })
            # Prüfe ob es eine Person ist (beginnt mit STV, Stadtrat, etc.)
            elif re.match(r"^(STV|Stadtrat|Bürgermeister|Erster Stadtrat)", line, re.IGNORECASE):
                if current_function and functions:
                    functions[-1]["personen"].append(line)
                else:
                    # Fallback für Personen ohne Funktionsüberschrift
                    functions.append({
                        "funktion": "Unbekannt",
                        "personen": [line]
                    })
            # Spezialfall: Schriftführer oder Verwaltung mit Namen (ohne Funktionspräfix)
            elif current_function and ("Schriftführer" in current_function or "Verwaltung" in current_function) and not re.match(r"^(STV|Stadtrat|Bürgermeister|Erster Stadtrat)", line, re.IGNORECASE):
                # Wenn wir bei Schriftführer oder Verwaltung sind und die Zeile nicht mit einer Funktion beginnt, ist es wahrscheinlich der Name
                if functions and functions[-1]["funktion"] == current_function:
                    functions[-1]["personen"].append(line)
        
        return functions
    
    def convert_to_custom_format(self, results):
        """
        Konvertiert die Analyseergebnisse in das struktur.json-konforme Format
        
        Args:
            results (dict): Analyseergebnisse
            
        Returns:
            dict: struktur.json-konformes JSON-Format
        """
        # Extrahiere Dateiname für ID
        document_path = results.get('document_path', '')
        filename = os.path.basename(document_path)
        file_id = os.path.splitext(filename)[0]  # Ohne .pdf Extension
        
        # Metadaten extrahieren
        metadata = results.get('metadata', {})
        attendance_data = results.get('attendance_data', {})
        
        # Anwesenheitsdaten konvertieren
        attendance_present = []
        attendance_excused = []
        
        if isinstance(attendance_data, dict) and 'error' not in attendance_data:
            # Anwesende Personen konvertieren
            for func in attendance_data.get('anwesend', []):
                for person in func.get('personen', []):
                    attendance_present.append({
                        "name": person,
                        "function": func.get('funktion', ''),
                        "status": "present"
                    })
            
            # Entschuldigte Personen konvertieren
            for func in attendance_data.get('entschuldigt', []):
                for person in func.get('personen', []):
                    attendance_excused.append({
                        "name": person,
                        "function": func.get('funktion', ''),
                        "status": "excused"
                    })
        
        # struktur.json-konformes Format erstellen
        custom_format = {
            "id": file_id,
            "document_type": metadata.get('dokumenttyp', ''),
            "session_type": metadata.get('sitzungsart', ''),
            "date": self.convert_date_to_iso(metadata.get('tag', '')),  # ISO-Format
            "duration": metadata.get('dauer', ''),
            "location": metadata.get('ort', ''),
            "attendance_present": attendance_present,
            "attendance_excused": attendance_excused if attendance_excused else [],  # Immer Array
            "total_present": len(attendance_present),
            "total_excused": len(attendance_excused),
            "total_participants": len(attendance_present) + len(attendance_excused),
            "analysis_method": results.get('analysis_method', 'unknown'),
            "total_pages": results.get('total_pages', 0),
            "extraction_timestamp": results.get('extraction_timestamp', ''),
            "document_path": document_path,
            "full_text": results.get('full_text', '')
        }
        
        return custom_format
    
    def extract_metadata(self, text):
        """
        Extrahiert Metadaten aus dem Dokument
        
        Args:
            text (str): Der zu analysierende Text
            
        Returns:
            dict: Strukturierte Metadaten
        """
        metadata = {
            "sitzungsart": None,
            "tag": None,
            "dauer": None,
            "ort": None,
            "dokumenttyp": None
        }
        
        # 1. Dokumenttyp erkennen (nach "NIEDERSCHRIFT")
        niederschrift_match = re.search(r"NIEDERSCHRIFT", text, re.IGNORECASE)
        if niederschrift_match:
            metadata["dokumenttyp"] = "Niederschrift"
        
        # 2. Sitzungsart extrahieren (nach "über die Sitzung der" und vor "der Stadt Pohlheim")
        sitzung_match = re.search(r"über die Sitzung der ([^\n]+) der Stadt Pohlheim", text, re.IGNORECASE)
        if sitzung_match:
            metadata["sitzungsart"] = sitzung_match.group(1).strip()
        
        # 3. Tag extrahieren (nach "Tag:")
        tag_match = re.search(r"Tag:\s*([^\n]+)", text, re.IGNORECASE)
        if tag_match:
            metadata["tag"] = tag_match.group(1).strip()
        
        # 4. Dauer extrahieren (nach "Dauer:")
        dauer_match = re.search(r"Dauer:\s*([^\n]+)", text, re.IGNORECASE)
        if dauer_match:
            metadata["dauer"] = dauer_match.group(1).strip()
        
        # 5. Ort extrahieren (nach "Ort:")
        ort_match = re.search(r"Ort:\s*([^\n]+)", text, re.IGNORECASE)
        if ort_match:
            metadata["ort"] = ort_match.group(1).strip()
        
        return metadata
    
    def extract_text_locally(self, document_path):
        """
        Extrahiert Text aus PDF mit lokaler PyPDF2-Analyse (alle Seiten)
        
        Args:
            document_path (str): Pfad zur PDF-Datei
            
        Returns:
            str: Vollständiger Text aller Seiten
        """
        try:
            with open(document_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                full_text = ""
                
                print(f"📄 Lokale PDF-Analyse: {len(pdf_reader.pages)} Seiten gefunden")
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    full_text += f"\n--- SEITE {page_num} ---\n"
                    full_text += page_text
                    print(f"  ✅ Seite {page_num} extrahiert")
                
                return full_text
        except Exception as e:
            print(f"Fehler bei lokaler PDF-Analyse: {e}")
            return None
    
    def find_all_attendance_in_text(self, text):
        """
        Findet alle Anwesenheits-Vorkommen im Text
        
        Args:
            text (str): Der zu analysierende Text
            
        Returns:
            list: Liste aller Anwesenheits-Vorkommen
        """
        # Finde alle Anwesenheits-Vorkommen
        attendance_matches = re.findall(r"(STV|Stadtrat|Bürgermeister|Erster Stadtrat)\s+[^\\n]+", text, re.IGNORECASE)
        return attendance_matches
    
    def find_all_tops_in_text(self, text):
        """
        Findet alle TOP-Vorkommen im Text (auch unvollständige)
        
        Args:
            text (str): Der zu analysierende Text
            
        Returns:
            list: Liste aller TOP-Vorkommen
        """
        # Finde alle TOP-Vorkommen
        top_matches = re.findall(r"TOP\s\d+[^\n]*", text, re.IGNORECASE)
        return top_matches
    
    def extract_tops_from_layout(self, response):
        """
        Extrahiert TOPs aus Document Intelligence Layout-Response
        
        Args:
            response: Document Intelligence Response-Objekt
            
        Returns:
            list: Liste der gefundenen TOPs mit Metadaten
        """
        tops_found = []
        
        for page in response.pages:
            for line in page.lines:
                if re.match(r"TOP\s\d+:", line.content):
                    top_info = {
                        "content": line.content,
                        "page_number": page.page_number,
                        "position": line.polygon if hasattr(line, 'polygon') else None,
                        "confidence": line.confidence if hasattr(line, 'confidence') else None
                    }
                    tops_found.append(top_info)
        
        return tops_found
    
    def analyze_and_extract_tops(self, document_path):
        """
        Hauptfunktion: Analysiert Dokument und extrahiert TOPs
        
        Args:
            document_path (str): Pfad zur PDF-Datei
            
        Returns:
            dict: Ergebnisse der TOP-Extraktion
        """
        print(f"Analysiere Dokument: {document_path}")
        
        # Dokument analysieren
        response = self.analyze_document(document_path)
        if not response:
            return {"error": "Dokumentanalyse fehlgeschlagen"}
        
        # TOPs aus Layout extrahieren
        layout_tops = self.extract_tops_from_layout(response)
        
        # Vollständigen Text extrahieren für Regex-Analyse
        full_text = ""
        for page in response.pages:
            for line in page.lines:
                full_text += line.content + "\n"
        
        # Anwesenheitsdaten mit Regex extrahieren
        attendance_data = self.extract_attendance_from_text(full_text)
        
        # Alle Anwesenheits-Vorkommen finden
        all_attendance_matches = self.find_all_attendance_in_text(full_text)
        
        # Metadaten extrahieren
        metadata = self.extract_metadata(full_text)
        
        # Zusätzlich: Lokale PDF-Analyse für alle Seiten
        print("\n🔄 Führe lokale PDF-Analyse durch (alle Seiten)...")
        local_text = self.extract_text_locally(document_path)
        
        if local_text:
            # Anwesenheitsdaten aus lokalem Text extrahieren
            local_attendance_data = self.extract_attendance_from_text(local_text)
            local_metadata = self.extract_metadata(local_text)
            
            return {
                "document_path": document_path,
                "layout_tops": layout_tops,
                "attendance_data": local_attendance_data,  # Verwende lokale Daten
                "all_attendance_matches": all_attendance_matches,
                "metadata": local_metadata,  # Verwende lokale Metadaten
                "total_pages": len(response.pages),
                "full_text": full_text,
                "local_full_text": local_text,  # Zusätzlich: Lokaler Text
                "analysis_method": "Azure + Local",
                "extraction_timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "document_path": document_path,
                "layout_tops": layout_tops,
                "attendance_data": attendance_data,
                "all_attendance_matches": all_attendance_matches,
                "metadata": metadata,
                "total_pages": len(response.pages),
                "full_text": full_text,
                "analysis_method": "Azure only"
            }
    
    def print_results(self, results):
        """Druckt die Ergebnisse formatiert aus"""
        if "error" in results:
            print(f"Fehler: {results['error']}")
            return
        
        print(f"\n=== ANALYSEERGEBNISSE für {results['document_path']} ===")
        print(f"Gesamtseiten: {results['total_pages']}")
        
        # Metadaten anzeigen
        print(f"\n--- DOKUMENT-METADATEN ---")
        metadata = results.get('metadata', {})
        print(f"📄 Dokumenttyp: {metadata.get('dokumenttyp', 'Nicht erkannt')}")
        print(f"🏛️ Sitzungsart: {metadata.get('sitzungsart', 'Nicht erkannt')}")
        print(f"📅 Tag: {metadata.get('tag', 'Nicht erkannt')}")
        print(f"⏰ Dauer: {metadata.get('dauer', 'Nicht erkannt')}")
        print(f"📍 Ort: {metadata.get('ort', 'Nicht erkannt')}")
        
        print(f"\n--- Anwesenheitsdaten aus Layout-Analyse ({len(results['layout_tops'])} gefunden) ---")
        for i, top in enumerate(results['layout_tops'], 1):
            print(f"Eintrag {i}: {top['content']}")
            print(f"  Seite: {top['page_number']}")
            if top['position']:
                print(f"  Position: {top['position']}")
            if top['confidence']:
                print(f"  Vertrauen: {top['confidence']:.2f}")
            print()
        
        print(f"\n--- Strukturierte Anwesenheitsdaten ---")
        if isinstance(results['attendance_data'], dict) and 'error' not in results['attendance_data']:
            # Anwesende
            print(f"\n📋 ANWESEND:")
            for func in results['attendance_data']['anwesend']:
                print(f"  {func['funktion']}:")
                for person in func['personen']:
                    print(f"    - {person}")
            
            # Entschuldigte
            if results['attendance_data']['entschuldigt']:
                print(f"\n❌ ENTSCHULDIGT:")
                for func in results['attendance_data']['entschuldigt']:
                    print(f"  {func['funktion']}:")
                    for person in func['personen']:
                        print(f"    - {person}")
        else:
            print(f"Fehler: {results['attendance_data'].get('error', 'Unbekannter Fehler')}")


def process_all_pdfs_in_folder(folder_path):
    """
    Verarbeitet alle PDF-Dateien in einem Ordner und erstellt Trainings-Labels
    
    Args:
        folder_path (str): Pfad zum Ordner mit PDF-Dateien
    """
    if not os.path.exists(folder_path):
        print(f"❌ Ordner nicht gefunden: {folder_path}")
        return
    
    # Finde alle PDF-Dateien im Ordner
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"❌ Keine PDF-Dateien im Ordner gefunden: {folder_path}")
        return
    
    print(f"🔍 Gefunden: {len(pdf_files)} PDF-Dateien im Ordner {folder_path}")
    print("=" * 60)
    
    analyzer = DocumentAnalyzer()
    successful_count = 0
    
    for i, pdf_file in enumerate(pdf_files, 1):
        pdf_path = os.path.join(folder_path, pdf_file)
        print(f"\n📄 [{i}/{len(pdf_files)}] Verarbeite: {pdf_file}")
        print("⏳ Bitte warten, dies kann einige Sekunden dauern...")
        
        try:
            # Analysiere PDF
            results = analyzer.analyze_and_extract_tops(pdf_path)
            
            if "error" in results:
                print(f"❌ Fehler bei der Analyse: {results['error']}")
                continue
            
            # Erstelle benutzerdefiniertes Format für Training
            custom_format = analyzer.convert_to_custom_format(results)
            
            # Speichere .json Datei im output Ordner - angepasst für training Verzeichnis
            base_name = os.path.splitext(pdf_file)[0]
            output_folder = os.path.join(os.path.dirname(folder_path), "output")
            os.makedirs(output_folder, exist_ok=True)
            custom_file = os.path.join(output_folder, f"{base_name}.json")
            
            with open(custom_file, 'w', encoding='utf-8') as f:
                json.dump(custom_format, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Custom Format erstellt: {os.path.basename(custom_file)}")
            
            # Zeige kurze Zusammenfassung
            metadata = results.get('metadata', {})
            print(f"   🏛️ Sitzungsart: {metadata.get('sitzungsart', 'Nicht erkannt')}")
            print(f"   📅 Tag: {metadata.get('tag', 'Nicht erkannt')}")
            
            # Zähle Anwesenheitsdaten
            if isinstance(results['attendance_data'], dict) and 'error' not in results['attendance_data']:
                anwesend_count = sum(len(func['personen']) for func in results['attendance_data']['anwesend'])
                entschuldigt_count = sum(len(func['personen']) for func in results['attendance_data']['entschuldigt'])
                print(f"   👥 Anwesend: {anwesend_count}, ❌ Entschuldigt: {entschuldigt_count}")
            
            successful_count += 1
            
        except Exception as e:
            print(f"❌ Fehler bei der Verarbeitung von {pdf_file}: {e}")
            continue
    
    print("\n" + "=" * 60)
    print(f"🎉 VERARBEITUNG ABGESCHLOSSEN!")
    print(f"   ✅ Erfolgreich verarbeitet: {successful_count}/{len(pdf_files)} Dateien")
    output_folder = os.path.join(os.path.dirname(folder_path), "output")
    print(f"   📁 Alle .json Dateien wurden im Ordner gespeichert:")
    print(f"      {output_folder}")
    
    if successful_count > 0:
        print(f"\n📋 Erstellte JSON Dateien:")
        for pdf_file in pdf_files:
            base_name = os.path.splitext(pdf_file)[0]
            custom_file = os.path.join(output_folder, f"{base_name}.json")
            if os.path.exists(custom_file):
                print(f"   ✅ {base_name}.json")


def main():
    """Hauptfunktion für PDF-Analyse"""
    import sys
    
    # Prüfe ob Ordner-Pfad als Argument übergeben wurde
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        # Standard-Ordner für Training-Input - angepasst für training Verzeichnis
        folder_path = "input"  # Relativer Pfad vom training Verzeichnis aus
        print(f"🔍 Verwende Standard-Ordner: {folder_path}")
    
    if not os.path.exists(folder_path):
        print(f"❌ Ordner nicht gefunden: {folder_path}")
        print("💡 Verwenden Sie: python extract2.py <pfad_zum_ordner>")
        return
    
    try:
        # Verarbeite alle PDFs im Ordner
        process_all_pdfs_in_folder(folder_path)
        
    except Exception as e:
        print(f"❌ Fehler bei der Verarbeitung: {e}")
        print("\n🔧 Mögliche Lösungen:")
        print("   - Überprüfen Sie den Ordner-Pfad")
        print("   - Stellen Sie sicher, dass die PDF-Dateien nicht beschädigt sind")
        print("   - Überprüfen Sie Ihre Internetverbindung")
        print("   - Überprüfen Sie den API Key in config.env")


if __name__ == "__main__":
    main()
