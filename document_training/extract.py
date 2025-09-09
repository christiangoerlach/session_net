import re
import os
import json
import base64
import PyPDF2
from datetime import datetime
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

# Lade Umgebungsvariablen
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
    
    def convert_to_azure_format(self, results):
        """
        Konvertiert die Analyseergebnisse in Azure Document Intelligence Trainingsformat
        
        Args:
            results (dict): Analyseergebnisse
            
        Returns:
            dict: Azure-konformes JSON-Format
        """
        azure_format = {
            "document": {
                "docType": "session_protocol",
                "fields": {}
            },
            "labels": []
        }
        
        # Metadaten als Felder hinzufügen
        metadata = results.get('metadata', {})
        if metadata:
            azure_format["document"]["fields"]["document_type"] = {
                "type": "string",
                "value": metadata.get('dokumenttyp', ''),
                "boundingRegions": [
                    {
                        "pageNumber": 1,
                        "polygon": [
                            {"x": 0.1, "y": 0.1},
                            {"x": 0.4, "y": 0.1},
                            {"x": 0.4, "y": 0.15},
                            {"x": 0.1, "y": 0.15}
                        ]
                    }
                ]
            }
            azure_format["document"]["fields"]["session_type"] = {
                "type": "string", 
                "value": metadata.get('sitzungsart', ''),
                "boundingRegions": [
                    {
                        "pageNumber": 1,
                        "polygon": [
                            {"x": 0.1, "y": 0.2},
                            {"x": 0.6, "y": 0.2},
                            {"x": 0.6, "y": 0.25},
                            {"x": 0.1, "y": 0.25}
                        ]
                    }
                ]
            }
            azure_format["document"]["fields"]["date"] = {
                "type": "date",
                "value": metadata.get('tag', ''),
                "boundingRegions": [
                    {
                        "pageNumber": 1,
                        "polygon": [
                            {"x": 0.1, "y": 0.3},
                            {"x": 0.3, "y": 0.3},
                            {"x": 0.3, "y": 0.35},
                            {"x": 0.1, "y": 0.35}
                        ]
                    }
                ]
            }
            azure_format["document"]["fields"]["duration"] = {
                "type": "string",
                "value": metadata.get('dauer', ''),
                "boundingRegions": [
                    {
                        "pageNumber": 1,
                        "polygon": [
                            {"x": 0.1, "y": 0.4},
                            {"x": 0.4, "y": 0.4},
                            {"x": 0.4, "y": 0.45},
                            {"x": 0.1, "y": 0.45}
                        ]
                    }
                ]
            }
            azure_format["document"]["fields"]["location"] = {
                "type": "string",
                "value": metadata.get('ort', ''),
                "boundingRegions": [
                    {
                        "pageNumber": 1,
                        "polygon": [
                            {"x": 0.1, "y": 0.5},
                            {"x": 0.7, "y": 0.5},
                            {"x": 0.7, "y": 0.55},
                            {"x": 0.1, "y": 0.55}
                        ]
                    }
                ]
            }
        
        # Anwesenheitsdaten strukturieren
        attendance_data = results.get('attendance_data', {})
        if isinstance(attendance_data, dict) and 'error' not in attendance_data:
            
            # Anwesende Personen
            anwesend_list = []
            for func in attendance_data.get('anwesend', []):
                for person in func.get('personen', []):
                    anwesend_list.append({
                        "name": person,
                        "function": func.get('funktion', ''),
                        "status": "present"
                    })
            
            # Entschuldigte Personen
            entschuldigt_list = []
            for func in attendance_data.get('entschuldigt', []):
                for person in func.get('personen', []):
                    entschuldigt_list.append({
                        "name": person,
                        "function": func.get('funktion', ''),
                        "status": "excused"
                    })
            
            azure_format["document"]["fields"]["attendance_present"] = {
                "type": "array",
                "value": anwesend_list,
                "boundingRegions": [
                    {
                        "pageNumber": 1,
                        "polygon": [
                            {"x": 0.1, "y": 0.6},
                            {"x": 0.8, "y": 0.6},
                            {"x": 0.8, "y": 0.8},
                            {"x": 0.1, "y": 0.8}
                        ]
                    }
                ]
            }
            
            azure_format["document"]["fields"]["attendance_excused"] = {
                "type": "array", 
                "value": entschuldigt_list,
                "boundingRegions": [
                    {
                        "pageNumber": 1,
                        "polygon": [
                            {"x": 0.1, "y": 0.85},
                            {"x": 0.8, "y": 0.85},
                            {"x": 0.8, "y": 0.95},
                            {"x": 0.1, "y": 0.95}
                        ]
                    }
                ]
            }
            
            # Zusammenfassung
            azure_format["document"]["fields"]["attendance_summary"] = {
                "type": "object",
                "value": {
                    "total_present": len(anwesend_list),
                    "total_excused": len(entschuldigt_list),
                    "total_participants": len(anwesend_list) + len(entschuldigt_list)
                }
            }
        
        # Labels für Azure Document Intelligence Training
        azure_format["labels"] = [
            {
                "label": "document_type",
                "confidence": 0.95,
                "source": "extracted"
            },
            {
                "label": "session_type", 
                "confidence": 0.90,
                "source": "extracted"
            },
            {
                "label": "attendance_data",
                "confidence": 0.85,
                "source": "extracted"
            }
        ]
        
        # Zusätzliche Metadaten für Azure
        azure_format["azure_metadata"] = {
            "analysis_method": results.get('analysis_method', 'unknown'),
            "total_pages": results.get('total_pages', 0),
            "extraction_timestamp": results.get('extraction_timestamp', ''),
            "document_path": results.get('document_path', '')
        }
        
        return azure_format
    
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
        

def main():
    """Hauptfunktion für PDF-Analyse"""
    import sys
    
    # Prüfe ob PDF-Pfad als Argument übergeben wurde
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Fordere Benutzer zur Eingabe auf
        pdf_path = input("Bitte geben Sie den Pfad zur PDF-Datei ein: ").strip()
    
    if not pdf_path:
        print("❌ Kein PDF-Pfad angegeben!")
        return
    
    if not pdf_path.lower().endswith('.pdf'):
        print("❌ Die Datei muss eine PDF-Datei sein!")
        return
    
    if not os.path.exists(pdf_path):
        print(f"❌ Datei nicht gefunden: {pdf_path}")
        return
    
    try:
        print(f"🔍 Analysiere PDF-Datei: {pdf_path}")
        print("⏳ Bitte warten, dies kann einige Sekunden dauern...\n")
        
        # Erstelle DocumentAnalyzer und analysiere PDF
        analyzer = DocumentAnalyzer()
        results = analyzer.analyze_and_extract_tops(pdf_path)
        
        if "error" in results:
            print(f"❌ Fehler bei der Analyse: {results['error']}")
            return
        
        # Zeige Ergebnisse
        analyzer.print_results(results)
        
        # Zusätzliche Statistiken
        print(f"\n📊 ZUSAMMENFASSUNG:")
        print(f"   📄 Dokument: {os.path.basename(pdf_path)}")
        print(f"   📑 Seiten: {results['total_pages']}")
        
        # Metadaten in Zusammenfassung
        metadata = results.get('metadata', {})
        print(f"   🏛️ Sitzungsart: {metadata.get('sitzungsart', 'Nicht erkannt')}")
        print(f"   📅 Tag: {metadata.get('tag', 'Nicht erkannt')}")
        print(f"   ⏰ Dauer: {metadata.get('dauer', 'Nicht erkannt')}")
        print(f"   📍 Ort: {metadata.get('ort', 'Nicht erkannt')}")
        
        print(f"   🎯 Anwesenheitsdaten (Layout): {len(results['layout_tops'])}")
        
        # Zähle strukturierte Anwesenheitsdaten
        if isinstance(results['attendance_data'], dict) and 'error' not in results['attendance_data']:
            anwesend_count = sum(len(func['personen']) for func in results['attendance_data']['anwesend'])
            entschuldigt_count = sum(len(func['personen']) for func in results['attendance_data']['entschuldigt'])
            print(f"   👥 Anwesend: {anwesend_count} Personen")
            print(f"   ❌ Entschuldigt: {entschuldigt_count} Personen")
        else:
            print(f"   ❌ Anwesenheitsdaten: Fehler")
        
        
        # Speichere Ergebnisse in Azure-konformem JSON-Format
        output_file = f"{os.path.splitext(os.path.basename(pdf_path))[0]}.document.json"
        azure_format = analyzer.convert_to_azure_format(results)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(azure_format, f, ensure_ascii=False, indent=2)
        print(f"   💾 Azure-konforme Labels gespeichert in: {output_file}")
        
    except Exception as e:
        print(f"❌ Fehler bei der PDF-Analyse: {e}")
        print("\n🔧 Mögliche Lösungen:")
        print("   - Überprüfen Sie den PDF-Pfad")
        print("   - Stellen Sie sicher, dass die PDF-Datei nicht beschädigt ist")
        print("   - Überprüfen Sie Ihre Internetverbindung")
        print("   - Überprüfen Sie den API Key in config.env")

if __name__ == "__main__":
    main()
