import json

# Lade die neuen Unterschiede-Dateien
with open('pypdf2_vs_pdfplumber_differences.json', 'r', encoding='utf-8') as f:
    pypdf2_vs_pdfplumber = json.load(f)

with open('pymupdf_vs_pypdf2_differences.json', 'r', encoding='utf-8') as f:
    pymupdf_vs_pypdf2 = json.load(f)

print('=== ZUSAMMENFASSUNG DER UNTERSCHIEDE ===')
print()
print('PyPDF2 vs pdfplumber:')
print(f'  Textlängen-Unterschied: {pypdf2_vs_pdfplumber["statistics"]["length_difference"]} Zeichen')
print(f'  PyPDF2: {pypdf2_vs_pdfplumber["statistics"]["pypdf2_length"]} Zeichen')
print(f'  pdfplumber: {pypdf2_vs_pdfplumber["statistics"]["pdfplumber_length"]} Zeichen')
print(f'  Gefundene Zeichen-Unterschiede: {len(pypdf2_vs_pdfplumber["character_differences"])}')
print()

print('pymupdf vs PyPDF2:')
print(f'  Textlängen-Unterschied: {pymupdf_vs_pypdf2["statistics"]["length_difference"]} Zeichen')
print(f'  pymupdf: {pymupdf_vs_pypdf2["statistics"]["pymupdf_length"]} Zeichen')
print(f'  PyPDF2: {pymupdf_vs_pypdf2["statistics"]["pypdf2_length"]} Zeichen')
print(f'  Gefundene Zeichen-Unterschiede: {len(pymupdf_vs_pypdf2["character_differences"])}')
print()

print('Erste 5 Zeichen-Unterschiede (PyPDF2 vs pdfplumber):')
for i, diff in enumerate(pypdf2_vs_pdfplumber['character_differences'][:5]):
    print(f'  Position {diff["position"]}: PyPDF2="{diff["pypdf2_char"]}" vs pdfplumber="{diff["pdfplumber_char"]}"')
    print(f'    Kontext: {diff["context"]}')
print()

print('Erste 5 Zeichen-Unterschiede (pymupdf vs PyPDF2):')
for i, diff in enumerate(pymupdf_vs_pypdf2['character_differences'][:5]):
    print(f'  Position {diff["position"]}: pymupdf="{diff["pymupdf_char"]}" vs PyPDF2="{diff["pypdf2_char"]}"')
    print(f'    Kontext: {diff["context"]}')
