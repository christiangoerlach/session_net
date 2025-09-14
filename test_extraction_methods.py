import PyPDF2
import pdfplumber
import fitz  # pymupdf
import os

# Teste alle drei Methoden auf derselben PDF
pdf_file = '2023_Juli_Stadtverordnetenversammlung_Niederschrift_STV.pdf'
pdf_path = os.path.join('input', pdf_file)

print('=== VERGLEICH DER PDF-EXTRAKTIONSMETHODEN ===')
print('Datei:', pdf_file)
print()

# 1. PyPDF2 (aktuell verwendet)
print('1. PyPDF2 (aktuell verwendet):')
try:
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        pypdf2_text = ''
        for page in pdf_reader.pages:
            pypdf2_text += page.extract_text()
    
    print('   Textlänge:', len(pypdf2_text), 'Zeichen')
    print('   Erste 200 Zeichen:')
    print('   ', pypdf2_text[:200].replace('\n', ' '))
    print()
    
except Exception as e:
    print('   Fehler:', e)
    print()

# 2. pdfplumber
print('2. pdfplumber:')
try:
    with pdfplumber.open(pdf_path) as pdf:
        pdfplumber_text = ''
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                pdfplumber_text += page_text
    
    print('   Textlänge:', len(pdfplumber_text), 'Zeichen')
    print('   Erste 200 Zeichen:')
    print('   ', pdfplumber_text[:200].replace('\n', ' '))
    print()
    
except Exception as e:
    print('   Fehler:', e)
    print()

# 3. pymupdf
print('3. pymupdf:')
try:
    doc = fitz.open(pdf_path)
    pymupdf_text = ''
    for page in doc:
        pymupdf_text += page.get_text()
    doc.close()
    
    print('   Textlänge:', len(pymupdf_text), 'Zeichen')
    print('   Erste 200 Zeichen:')
    print('   ', pymupdf_text[:200].replace('\n', ' '))
    print()
    
except Exception as e:
    print('   Fehler:', e)
    print()

# Vergleich der Ergebnisse
print('=== VERGLEICH DER ERGEBNISSE ===')
print('Textlängen:')
print('  PyPDF2:', len(pypdf2_text) if 'pypdf2_text' in locals() else 'Fehler')
print('  pdfplumber:', len(pdfplumber_text) if 'pdfplumber_text' in locals() else 'Fehler')
print('  pymupdf:', len(pymupdf_text) if 'pymupdf_text' in locals() else 'Fehler')
print()

# Prüfe auf Unterschiede
if 'pypdf2_text' in locals() and 'pdfplumber_text' in locals():
    if pypdf2_text == pdfplumber_text:
        print('PyPDF2 vs pdfplumber: IDENTISCH')
    else:
        print('PyPDF2 vs pdfplumber: UNTERSCHIEDLICH')
        print('   Unterschiede in den ersten 500 Zeichen:')
        for i, (c1, c2) in enumerate(zip(pypdf2_text[:500], pdfplumber_text[:500])):
            if c1 != c2:
                print(f'   Position {i}: PyPDF2="{c1}" vs pdfplumber="{c2}"')
                break

if 'pypdf2_text' in locals() and 'pymupdf_text' in locals():
    if pypdf2_text == pymupdf_text:
        print('PyPDF2 vs pymupdf: IDENTISCH')
    else:
        print('PyPDF2 vs pymupdf: UNTERSCHIEDLICH')
        print('   Unterschiede in den ersten 500 Zeichen:')
        for i, (c1, c2) in enumerate(zip(pypdf2_text[:500], pymupdf_text[:500])):
            if c1 != c2:
                print(f'   Position {i}: PyPDF2="{c1}" vs pymupdf="{c2}"')
                break

# Teste spezifische Extraktionsmuster
print('\n=== TESTE SPEZIFISCHE MUSTER ===')

# Teste Anwesenheitsliste
if 'pypdf2_text' in locals():
    print('Anwesenheitsliste (PyPDF2):')
    anwesen_match = re.search(r'Anwesend[:\s]*(.*?)(?=Abwesend|TOP|Tagesordnung)', pypdf2_text, re.DOTALL | re.IGNORECASE)
    if anwesen_match:
        anwesen_text = anwesen_match.group(1).strip()
        print('   Gefunden:', len(anwesen_text), 'Zeichen')
        print('   Erste 100 Zeichen:', anwesen_text[:100])
    else:
        print('   Nicht gefunden')
    print()

if 'pdfplumber_text' in locals():
    print('Anwesenheitsliste (pdfplumber):')
    anwesen_match = re.search(r'Anwesend[:\s]*(.*?)(?=Abwesend|TOP|Tagesordnung)', pdfplumber_text, re.DOTALL | re.IGNORECASE)
    if anwesen_match:
        anwesen_text = anwesen_match.group(1).strip()
        print('   Gefunden:', len(anwesen_text), 'Zeichen')
        print('   Erste 100 Zeichen:', anwesen_text[:100])
    else:
        print('   Nicht gefunden')
    print()

if 'pymupdf_text' in locals():
    print('Anwesenheitsliste (pymupdf):')
    anwesen_match = re.search(r'Anwesend[:\s]*(.*?)(?=Abwesend|TOP|Tagesordnung)', pymupdf_text, re.DOTALL | re.IGNORECASE)
    if anwesen_match:
        anwesen_text = anwesen_match.group(1).strip()
        print('   Gefunden:', len(anwesen_text), 'Zeichen')
        print('   Erste 100 Zeichen:', anwesen_text[:100])
    else:
        print('   Nicht gefunden')
    print()
