import PyPDF2
import pdfplumber
import fitz
import re
import os

# Teste alle drei Methoden auf derselben PDF
pdf_file = '2023_Juli_Stadtverordnetenversammlung_Niederschrift_STV.pdf'
pdf_path = os.path.join('input', pdf_file)

print('=== VERGLEICH DER ERGEBNISSE ===')

# Extrahiere Text mit allen Methoden
with open(pdf_path, 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    pypdf2_text = ''
    for page in pdf_reader.pages:
        pypdf2_text += page.extract_text()

with pdfplumber.open(pdf_path) as pdf:
    pdfplumber_text = ''
    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            pdfplumber_text += page_text

doc = fitz.open(pdf_path)
pymupdf_text = ''
for page in doc:
    pymupdf_text += page.get_text()
doc.close()

print('Textlängen:')
print('  PyPDF2:', len(pypdf2_text), 'Zeichen')
print('  pdfplumber:', len(pdfplumber_text), 'Zeichen')
print('  pymupdf:', len(pymupdf_text), 'Zeichen')
print()

# Prüfe auf Unterschiede
print('PyPDF2 vs pdfplumber:')
if pypdf2_text == pdfplumber_text:
    print('  IDENTISCH')
else:
    print('  UNTERSCHIEDLICH')
    print('  Unterschiede in den ersten 500 Zeichen:')
    for i, (c1, c2) in enumerate(zip(pypdf2_text[:500], pdfplumber_text[:500])):
        if c1 != c2:
            print(f'  Position {i}: PyPDF2="{c1}" vs pdfplumber="{c2}"')
            break

print()
print('PyPDF2 vs pymupdf:')
if pypdf2_text == pymupdf_text:
    print('  IDENTISCH')
else:
    print('  UNTERSCHIEDLICH')
    print('  Unterschiede in den ersten 500 Zeichen:')
    for i, (c1, c2) in enumerate(zip(pypdf2_text[:500], pymupdf_text[:500])):
        if c1 != c2:
            print(f'  Position {i}: PyPDF2="{c1}" vs pymupdf="{c2}"')
            break

print()
print('pdfplumber vs pymupdf:')
if pdfplumber_text == pymupdf_text:
    print('  IDENTISCH')
else:
    print('  UNTERSCHIEDLICH')
    print('  Unterschiede in den ersten 500 Zeichen:')
    for i, (c1, c2) in enumerate(zip(pdfplumber_text[:500], pymupdf_text[:500])):
        if c1 != c2:
            print(f'  Position {i}: pdfplumber="{c1}" vs pymupdf="{c2}"')
            break

# Teste spezifische Extraktionsmuster
print('\n=== TESTE SPEZIFISCHE MUSTER ===')

# Teste Anwesenheitsliste
print('Anwesenheitsliste (PyPDF2):')
anwesen_match = re.search(r'Anwesend[:\s]*(.*?)(?=Abwesend|TOP|Tagesordnung)', pypdf2_text, re.DOTALL | re.IGNORECASE)
if anwesen_match:
    anwesen_text = anwesen_match.group(1).strip()
    print('   Gefunden:', len(anwesen_text), 'Zeichen')
    print('   Erste 100 Zeichen:', anwesen_text[:100])
else:
    print('   Nicht gefunden')
print()

print('Anwesenheitsliste (pdfplumber):')
anwesen_match = re.search(r'Anwesend[:\s]*(.*?)(?=Abwesend|TOP|Tagesordnung)', pdfplumber_text, re.DOTALL | re.IGNORECASE)
if anwesen_match:
    anwesen_text = anwesen_match.group(1).strip()
    print('   Gefunden:', len(anwesen_text), 'Zeichen')
    print('   Erste 100 Zeichen:', anwesen_text[:100])
else:
    print('   Nicht gefunden')
print()

print('Anwesenheitsliste (pymupdf):')
anwesen_match = re.search(r'Anwesend[:\s]*(.*?)(?=Abwesend|TOP|Tagesordnung)', pymupdf_text, re.DOTALL | re.IGNORECASE)
if anwesen_match:
    anwesen_text = anwesen_match.group(1).strip()
    print('   Gefunden:', len(anwesen_text), 'Zeichen')
    print('   Erste 100 Zeichen:', anwesen_text[:100])
else:
    print('   Nicht gefunden')
print()

# Teste TOP-Erkennung
print('TOP-Erkennung (PyPDF2):')
top_matches = re.findall(r'TOP\s+(\d+(?:\.\d+)?)', pypdf2_text, re.IGNORECASE)
print('   Gefundene TOPs:', len(top_matches))
print('   Erste 5 TOPs:', top_matches[:5])
print()

print('TOP-Erkennung (pdfplumber):')
top_matches = re.findall(r'TOP\s+(\d+(?:\.\d+)?)', pdfplumber_text, re.IGNORECASE)
print('   Gefundene TOPs:', len(top_matches))
print('   Erste 5 TOPs:', top_matches[:5])
print()

print('TOP-Erkennung (pymupdf):')
top_matches = re.findall(r'TOP\s+(\d+(?:\.\d+)?)', pymupdf_text, re.IGNORECASE)
print('   Gefundene TOPs:', len(top_matches))
print('   Erste 5 TOPs:', top_matches[:5])
print()
