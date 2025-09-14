import PyPDF2
import pdfplumber
import fitz
import re
import os
import json
from datetime import datetime

# PDF-Datei für Vergleich
pdf_file = '2023_Juli_Stadtverordnetenversammlung_Niederschrift_STV.pdf'
pdf_path = os.path.join('input', pdf_file)

print('=== PDF-EXTRAKTIONSVERGLEICH ===')
print(f'Datei: {pdf_file}')
print()

# Extrahiere mit allen drei Methoden
print('Extrahiere Text mit allen drei Methoden...')

# PyPDF2
with open(pdf_path, 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    pypdf2_text = ''
    for page in pdf_reader.pages:
        pypdf2_text += page.extract_text()

# pdfplumber
with pdfplumber.open(pdf_path) as pdf:
    pdfplumber_text = ''
    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            pdfplumber_text += page_text

# pymupdf
doc = fitz.open(pdf_path)
pymupdf_text = ''
for page in doc:
    pymupdf_text += page.get_text()
doc.close()

print(f'PyPDF2: {len(pypdf2_text)} Zeichen')
print(f'pdfplumber: {len(pdfplumber_text)} Zeichen')
print(f'pymupdf: {len(pymupdf_text)} Zeichen')
print()

# Finde Unterschiede zwischen PyPDF2 und pdfplumber
print('=== PyPDF2 vs pdfplumber UNTERSCHIEDE ===')
pypdf2_vs_pdfplumber = {
    'timestamp': datetime.now().isoformat(),
    'pdf_file': pdf_file,
    'statistics': {
        'pypdf2_length': len(pypdf2_text),
        'pdfplumber_length': len(pdfplumber_text),
        'length_difference': len(pypdf2_text) - len(pdfplumber_text)
    },
    'character_differences': []
}

# Zeichen-für-Zeichen Vergleich (erste 1000 Zeichen)
min_length = min(len(pypdf2_text), len(pdfplumber_text), 1000)
for i in range(min_length):
    if pypdf2_text[i] != pdfplumber_text[i]:
        pypdf2_vs_pdfplumber['character_differences'].append({
            'position': i,
            'pypdf2_char': pypdf2_text[i],
            'pdfplumber_char': pdfplumber_text[i],
            'context': pypdf2_text[max(0, i-10):i+10]
        })
        if len(pypdf2_vs_pdfplumber['character_differences']) >= 20:
            break

# Speichere PyPDF2 vs pdfplumber Unterschiede
with open('pypdf2_vs_pdfplumber_differences.json', 'w', encoding='utf-8') as f:
    json.dump(pypdf2_vs_pdfplumber, f, ensure_ascii=False, indent=2)

print(f'Textlängen-Unterschied: {pypdf2_vs_pdfplumber["statistics"]["length_difference"]} Zeichen')
print(f'Gefundene Zeichen-Unterschiede: {len(pypdf2_vs_pdfplumber["character_differences"])}')
print()

# Finde Unterschiede zwischen pymupdf und PyPDF2
print('=== pymupdf vs PyPDF2 UNTERSCHIEDE ===')
pymupdf_vs_pypdf2 = {
    'timestamp': datetime.now().isoformat(),
    'pdf_file': pdf_file,
    'statistics': {
        'pymupdf_length': len(pymupdf_text),
        'pypdf2_length': len(pypdf2_text),
        'length_difference': len(pymupdf_text) - len(pypdf2_text)
    },
    'character_differences': []
}

# Zeichen-für-Zeichen Vergleich (erste 1000 Zeichen)
min_length = min(len(pymupdf_text), len(pypdf2_text), 1000)
for i in range(min_length):
    if pymupdf_text[i] != pypdf2_text[i]:
        pymupdf_vs_pypdf2['character_differences'].append({
            'position': i,
            'pymupdf_char': pymupdf_text[i],
            'pypdf2_char': pypdf2_text[i],
            'context': pymupdf_text[max(0, i-10):i+10]
        })
        if len(pymupdf_vs_pypdf2['character_differences']) >= 20:
            break

# Speichere pymupdf vs PyPDF2 Unterschiede
with open('pymupdf_vs_pypdf2_differences.json', 'w', encoding='utf-8') as f:
    json.dump(pymupdf_vs_pypdf2, f, ensure_ascii=False, indent=2)

print(f'Textlängen-Unterschied: {pymupdf_vs_pypdf2["statistics"]["length_difference"]} Zeichen')
print(f'Gefundene Zeichen-Unterschiede: {len(pymupdf_vs_pypdf2["character_differences"])}')
print()

print('Ergebnisse gespeichert in:')
print('  - pypdf2_vs_pdfplumber_differences.json')
print('  - pymupdf_vs_pypdf2_differences.json')
