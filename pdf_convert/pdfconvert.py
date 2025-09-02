import os
import sys
import pdfplumber
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import PyPDF2
import argparse
from pathlib import Path

def check_pdf_for_text(pdf_path):
    """Prüft, ob ein PDF Text enthält."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text and text.strip():
                    return True
        return False
    except Exception as e:
        print(f"Fehler beim Prüfen von {pdf_path}: {e}")
        return False

def ocr_pdf(input_pdf, output_pdf):
    """Wendet OCR auf ein PDF an und speichert es mit Textschicht."""
    try:
        print(f"Starte OCR für: {input_pdf}")
        
        # Verwende PyMuPDF für PDF-zu-Bild-Konvertierung
        try:
            # Öffne PDF mit PyMuPDF
            pdf_document = fitz.open(input_pdf)
            print(f"✅ PyMuPDF: PDF mit {len(pdf_document)} Seiten geöffnet")
            
            # Erstelle ein neues PDF für die Ausgabe
            pdf_writer = PyPDF2.PdfWriter()
            
            for page_num in range(len(pdf_document)):
                print(f"Verarbeite Seite {page_num + 1}/{len(pdf_document)}...")
                
                # Konvertiere Seite zu Bild
                page = pdf_document[page_num]
                mat = fitz.Matrix(2.0, 2.0)  # 2x Zoom für bessere Qualität
                pix = page.get_pixmap(matrix=mat)
                
                # Konvertiere zu PIL Image
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                
                # Führe OCR auf dem Bild durch
                text = pytesseract.image_to_pdf_or_hocr(image, extension='pdf', lang='deu')
                
                # Konvertiere das OCR-PDF (Bytes) in ein PyPDF2-kompatibles Format
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(text))
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
            
            # Schließe PyMuPDF Dokument
            pdf_document.close()
            
            # Speichere das neue PDF
            with open(output_pdf, 'wb') as f:
                pdf_writer.write(f)
            print(f"✅ OCR abgeschlossen: {output_pdf}")
            return True
            
        except Exception as e:
            print(f"❌ PyMuPDF Fehler: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Fehler bei OCR von {input_pdf}: {e}")
        return False

def process_pdfs_in_directory(directory):
    """Durchläuft alle PDFs im Verzeichnis und Unterverzeichnissen."""
    directory_path = Path(directory)
    
    if not directory_path.exists():
        print(f"❌ Verzeichnis existiert nicht: {directory}")
        return
    
    pdf_count = 0
    processed_count = 0
    skipped_text_count = 0
    skipped_converted_count = 0
    error_count = 0
    
    print(f"🔍 Durchsuche Verzeichnis: {directory}")
    
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith('.pdf'):
                pdf_path = os.path.join(root, filename)
                output_pdf = os.path.join(root, f"ocr_{filename}")
                
                # Überspringe bereits OCR-bearbeitete Dateien
                if filename.startswith('ocr_'):
                    print(f"⏭️ Überspringe bereits OCR-bearbeitete Datei: {filename}")
                    continue
                
                pdf_count += 1
                print(f"\n📄 Prüfe {pdf_path}...")
                
                # Prüfe ob bereits eine konvertierte Version existiert
                if os.path.exists(output_pdf):
                    print(f"⏭️ {filename}: Bereits konvertierte Version gefunden, überspringe.")
                    skipped_converted_count += 1
                    continue
                
                if check_pdf_for_text(pdf_path):
                    print(f"✅ {filename}: Enthält bereits Text, überspringe OCR.")
                    skipped_text_count += 1
                else:
                    print(f"🔍 {filename}: Kein Text gefunden, starte OCR...")
                    if ocr_pdf(pdf_path, output_pdf):
                        processed_count += 1
                    else:
                        error_count += 1
    
    print(f"\n📊 Zusammenfassung:")
    print(f"   Anzahl der Dokumente: {pdf_count}")
    print(f"   Übersprungene Dokumente weil schon Text: {skipped_text_count}")
    print(f"   Übersprungene Dokumente weil schon konvertiert: {skipped_converted_count}")
    print(f"   Konvertierte Dokumente: {processed_count}")
    print(f"   Fehler/Rest: {error_count}")

def main():
    parser = argparse.ArgumentParser(description='PDF OCR Tool für Session Net')
    parser.add_argument('directory', nargs='?', default=None, 
                       help='Verzeichnis mit PDFs (optional)')
    parser.add_argument('--recursive', '-r', action='store_true',
                       help='Rekursiv alle Unterverzeichnisse durchsuchen')
    
    args = parser.parse_args()
    
    # Standard-Verzeichnis wenn keines angegeben
    if args.directory is None:
        # Suche nach dem aktuellen Projektverzeichnis
        current_dir = Path.cwd()
        possible_dirs = [
            current_dir / "pohlheim_geschuetzt",
            current_dir / "downloads",
            current_dir / "Kalender_2025_August"
        ]
        
        for dir_path in possible_dirs:
            if dir_path.exists():
                args.directory = str(dir_path)
                print(f"🔍 Verwende gefundenes Verzeichnis: {args.directory}")
                break
        else:
            print("❌ Kein Standardverzeichnis gefunden. Bitte geben Sie ein Verzeichnis an.")
            print("Verfügbare Optionen:")
            print("  python pdfconvert.py <verzeichnis>")
            print("  python pdfconvert.py --help")
            return
    
    process_pdfs_in_directory(args.directory)

if __name__ == "__main__":
    main()