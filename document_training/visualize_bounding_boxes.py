#!/usr/bin/env python3
"""
Script zur Visualisierung der Bounding Boxes auf PDF-Dokumenten
Zeigt die extrahierten Felder mit ihren Positionen an
"""

import fitz  # PyMuPDF
import json
import os
import sys
from pathlib import Path

class BoundingBoxVisualizer:
    def __init__(self):
        self.colors = {
            'document_type': (1, 0, 0),      # Rot
            'session_type': (0, 1, 0),        # Grün
            'date': (0, 0, 1),                # Blau
            'duration': (1, 1, 0),            # Gelb
            'location': (1, 0, 1),            # Magenta
            'attendance_present': (0, 1, 1),  # Cyan
            'attendance_excused': (1, 0.5, 0) # Orange
        }
    
    def visualize_pdf(self, pdf_path, json_path=None, output_path=None):
        """
        Visualisiert Bounding Boxes auf einem PDF
        
        Args:
            pdf_path (str): Pfad zur PDF-Datei
            json_path (str): Pfad zur JSON-Datei (optional, wird automatisch erkannt)
            output_path (str): Ausgabepfad für annotiertes PDF (optional)
        """
        try:
            # PDF laden
            print(f"📄 Lade PDF: {pdf_path}")
            doc = fitz.open(pdf_path)
            
            # JSON-Pfad bestimmen
            if json_path is None:
                pdf_name = Path(pdf_path).stem
                # Suche JSON-Datei im aktuellen Verzeichnis
                json_path = f"{pdf_name}.document.json"
                if not os.path.exists(json_path):
                    # Fallback: Suche im document_training Verzeichnis
                    json_path = f"document_training/{pdf_name}.document.json"
            
            if not os.path.exists(json_path):
                print(f"❌ JSON-Datei nicht gefunden: {json_path}")
                return False
            
            # JSON laden
            print(f"📋 Lade Labels: {json_path}")
            with open(json_path, 'r', encoding='utf-8') as f:
                labels = json.load(f)
            
            # Ausgabepfad bestimmen
            if output_path is None:
                pdf_name = Path(pdf_path).stem
                output_path = f"{pdf_name}_annotated.pdf"
            
            print(f"🎨 Zeichne Bounding Boxes...")
            
            # Bounding Boxes zeichnen
            fields_drawn = 0
            for field_name, field_data in labels.get("document", {}).get("fields", {}).items():
                if "boundingRegions" not in field_data:
                    continue
                
                # Farbe für dieses Feld bestimmen
                color = self.colors.get(field_name, (0.5, 0.5, 0.5))  # Grau als Standard
                
                for region in field_data["boundingRegions"]:
                    page_num = region["pageNumber"] - 1  # 0-basiert
                    
                    if page_num >= len(doc):
                        print(f"⚠️  Seite {region['pageNumber']} existiert nicht im PDF")
                        continue
                    
                    page = doc[page_num]
                    
                    # Polygon zu Rechteck konvertieren
                    polygon_points = region["polygon"]
                    if len(polygon_points) >= 4:
                        # Erste 4 Punkte verwenden (normalerweise ein Rechteck)
                        x_coords = [p["x"] * page.rect.width for p in polygon_points[:4]]
                        y_coords = [p["y"] * page.rect.height for p in polygon_points[:4]]
                        
                        # Rechteck erstellen
                        rect = fitz.Rect(
                            min(x_coords), min(y_coords),
                            max(x_coords), max(y_coords)
                        )
                        
                        # Rechteck zeichnen
                        page.draw_rect(rect, color=color, width=2)
                        
                        # Feldname als Text hinzufügen
                        text_point = fitz.Point(rect.x0, rect.y0 - 5)
                        page.insert_text(
                            text_point, 
                            f"{field_name}: {field_data.get('value', '')}", 
                            fontsize=8, 
                            color=color
                        )
                        
                        fields_drawn += 1
            
            # PDF speichern
            print(f"💾 Speichere annotiertes PDF: {output_path}")
            doc.save(output_path)
            doc.close()
            
            print(f"✅ Erfolgreich! {fields_drawn} Felder visualisiert")
            print(f"📁 Ausgabedatei: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Fehler bei der Visualisierung: {e}")
            return False
    
    def list_available_files(self, directory="."):
        """Listet verfügbare PDF und JSON Dateien auf"""
        print("📋 Verfügbare Dateien:")
        
        pdf_files = list(Path(directory).glob("*.pdf"))
        json_files = list(Path(directory).glob("*.document.json"))
        
        print(f"\n📄 PDF-Dateien ({len(pdf_files)}):")
        for pdf in pdf_files:
            print(f"  - {pdf.name}")
        
        print(f"\n📋 JSON-Dateien ({len(json_files)}):")
        for json_file in json_files:
            print(f"  - {json_file.name}")
        
        return pdf_files, json_files

def main():
    """Hauptfunktion"""
    print("🎨 Bounding Box Visualizer")
    print("=" * 50)
    
    visualizer = BoundingBoxVisualizer()
    
    # PDF-Datei auswählen
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"📄 Verwende PDF: {pdf_path}")
    else:
        # Verfügbare Dateien anzeigen
        pdf_files, json_files = visualizer.list_available_files()
        
        if not pdf_files:
            print("❌ Keine PDF-Dateien gefunden!")
            return
        
        print(f"\n🎯 Wählen Sie eine PDF-Datei:")
        for i, pdf in enumerate(pdf_files, 1):
            print(f"  {i}. {pdf.name}")
        
        try:
            choice = int(input("\nEingabe (Nummer): ")) - 1
            if 0 <= choice < len(pdf_files):
                pdf_path = str(pdf_files[choice])
            else:
                print("❌ Ungültige Auswahl!")
                return
        except ValueError:
            print("❌ Ungültige Eingabe!")
            return
    
    # Visualisierung starten
    print(f"\n🚀 Starte Visualisierung für: {pdf_path}")
    success = visualizer.visualize_pdf(pdf_path)
    
    if success:
        print("\n✅ Visualisierung abgeschlossen!")
        print("💡 Öffnen Sie die *_annotated.pdf Datei, um die Bounding Boxes zu sehen")
    else:
        print("\n❌ Visualisierung fehlgeschlagen!")

if __name__ == "__main__":
    main()
