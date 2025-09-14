import PyPDF2
import pdfplumber
import fitz  # pymupdf
import re
import os
import json
from datetime import datetime

def extract_with_pypdf2(pdf_path):
    """Extrahiere Text mit PyPDF2"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ''
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        return f"Fehler bei PyPDF2: {e}"

def extract_with_pdfplumber(pdf_path):
    """Extrahiere Text mit pdfplumber"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ''
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        return text
    except Exception as e:
        return f"Fehler bei pdfplumber: {e}"

def extract_with_pymupdf(pdf_path):
    """Extrahiere Text mit pymupdf"""
    try:
        doc = fitz.open(pdf_path)
        text = ''
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        return f"Fehler bei pymupdf: {e}"

def find_differences(text1, text2, method1_name, method2_name):
    """Finde und dokumentiere Unterschiede zwischen zwei Texten"""
    differences = []
    
    # Grundlegende Statistiken
    stats = {
        'method1': method1_name,
        'method2': method2_name,
        'length1': len(text1),
        'length2': len(text2),
        'length_diff': len(text1) - len(text2),
        'timestamp': datetime.now().isoformat()
    }
    
    # Zeichen-für-Zeichen Vergleich
    min_length = min(len(text1), len(text2))
    char_differences = []
    
    for i in range(min_length):
        if text1[i] != text2[i]:
            char_differences.append({
                'position': i,
                'char1': text1[i],
                'char2': text2[i],
                'context1': text1[max(0, i-20):i+20],
                'context2': text2[max(0, i-20):i+20]
            })
            
            # Begrenze auf erste 50 Unterschiede
            if len(char_differences) >= 50:
                char_differences.append({
                    'position': '...',
                    'char1': '...',
                    'char2': '...',
                    'context1': f'... und {len(text1) - min_length} weitere Unterschiede',
                    'context2': f'... und {len(text2) - min_length} weitere Unterschiede'
                })
                break
    
    # Spezifische Muster-Tests
    patterns = {
        'anwesenheit': r'Anwesend[:\s]*(.*?)(?=Abwesend|TOP|Tagesordnung)',
        'abwesend': r'Abwesend[:\s]*(.*?)(?=TOP|Tagesordnung)',
        'tagesordnung': r'Tagesordnung[:\s]*(.*?)(?=TOP\s+1|Beschluss)',
        'top_numbers': r'TOP\s+(\d+(?:\.\d+)?)',
        'datum': r'(\d{1,2}\.\d{1,2}\.\d{4})',
        'zeit': r'(\d{1,2}:\d{2})',
        'ort': r'(Pohlheim|Sitzungssaal)'
    }
    
    pattern_results = {}
    for pattern_name, pattern in patterns.items():
        matches1 = re.findall(pattern, text1, re.DOTALL | re.IGNORECASE)
        matches2 = re.findall(pattern, text2, re.DOTALL | re.IGNORECASE)
        
        pattern_results[pattern_name] = {
            'method1_count': len(matches1),
            'method2_count': len(matches2),
            'method1_matches': matches1[:10],  # Erste 10 Matches
            'method2_matches': matches2[:10]
        }
    
    return {
        'statistics': stats,
        'character_differences': char_differences,
        'pattern_analysis': pattern_results
    }

def analyze_specific_sections(text, method_name):
    """Analysiere spezifische Abschnitte des Dokuments"""
    analysis = {
        'method': method_name,
        'total_length': len(text),
        'sections': {}
    }
    
    # Anwesenheitsliste
    anwesen_match = re.search(r'Anwesend[:\s]*(.*?)(?=Abwesend|TOP|Tagesordnung)', text, re.DOTALL | re.IGNORECASE)
    if anwesen_match:
        anwesen_text = anwesen_match.group(1).strip()
        analysis['sections']['anwesenheit'] = {
            'found': True,
            'length': len(anwesen_text),
            'preview': anwesen_text[:200],
            'person_count': len(re.findall(r'STV\s+\w+', anwesen_text))
        }
    else:
        analysis['sections']['anwesenheit'] = {'found': False}
    
    # Abwesend
    abwesend_match = re.search(r'Abwesend[:\s]*(.*?)(?=TOP|Tagesordnung)', text, re.DOTALL | re.IGNORECASE)
    if abwesend_match:
        abwesend_text = abwesend_match.group(1).strip()
        analysis['sections']['abwesend'] = {
            'found': True,
            'length': len(abwesend_text),
            'preview': abwesend_text[:200],
            'person_count': len(re.findall(r'STV\s+\w+', abwesend_text))
        }
    else:
        analysis['sections']['abwesend'] = {'found': False}
    
    # Tagesordnung
    tagesordnung_match = re.search(r'Tagesordnung[:\s]*(.*?)(?=TOP\s+1|Beschluss)', text, re.DOTALL | re.IGNORECASE)
    if tagesordnung_match:
        tagesordnung_text = tagesordnung_match.group(1).strip()
        analysis['sections']['tagesordnung'] = {
            'found': True,
            'length': len(tagesordnung_text),
            'preview': tagesordnung_text[:200],
            'top_count': len(re.findall(r'TOP\s+(\d+(?:\.\d+)?)', tagesordnung_text))
        }
    else:
        analysis['sections']['tagesordnung'] = {'found': False}
    
    # TOP-Erkennung
    top_matches = re.findall(r'TOP\s+(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    analysis['sections']['top_erkenntnis'] = {
        'total_tops': len(top_matches),
        'top_numbers': top_matches[:20]  # Erste 20 TOPs
    }
    
    return analysis

def main():
    # PDF-Datei für Vergleich
    pdf_file = '2023_Juli_Stadtverordnetenversammlung_Niederschrift_STV.pdf'
    pdf_path = os.path.join('input', pdf_file)
    
    print('=== PDF-EXTRAKTIONSVERGLEICH ===')
    print(f'Datei: {pdf_file}')
    print()
    
    # Extrahiere mit allen drei Methoden
    print('Extrahiere Text mit allen drei Methoden...')
    pypdf2_text = extract_with_pypdf2(pdf_path)
    pdfplumber_text = extract_with_pdfplumber(pdf_path)
    pymupdf_text = extract_with_pymupdf(pdf_path)
    
    print(f'PyPDF2: {len(pypdf2_text)} Zeichen')
    print(f'pdfplumber: {len(pdfplumber_text)} Zeichen')
    print(f'pymupdf: {len(pymupdf_text)} Zeichen')
    print()
    
    # Analysiere spezifische Abschnitte
    print('Analysiere spezifische Abschnitte...')
    pypdf2_analysis = analyze_specific_sections(pypdf2_text, 'PyPDF2')
    pdfplumber_analysis = analyze_specific_sections(pdfplumber_text, 'pdfplumber')
    pymupdf_analysis = analyze_specific_sections(pymupdf_text, 'pymupdf')
    
    # Finde Unterschiede
    print('Finde Unterschiede...')
    pypdf2_vs_pdfplumber = find_differences(pypdf2_text, pdfplumber_text, 'PyPDF2', 'pdfplumber')
    pymupdf_vs_pypdf2 = find_differences(pymupdf_text, pypdf2_text, 'pymupdf', 'PyPDF2')
    
    # Speichere Ergebnisse
    print('Speichere Ergebnisse...')
    
    # PyPDF2 vs pdfplumber Unterschiede
    with open('pypdf2_vs_pdfplumber_differences.json', 'w', encoding='utf-8') as f:
        json.dump(pypdf2_vs_pdfplumber, f, ensure_ascii=False, indent=2)
    
    # pymupdf vs PyPDF2 Unterschiede
    with open('pymupdf_vs_pypdf2_differences.json', 'w', encoding='utf-8') as f:
        json.dump(pymupdf_vs_pypdf2, f, ensure_ascii=False, indent=2)
    
    # Vollständige Analyse
    complete_analysis = {
        'timestamp': datetime.now().isoformat(),
        'pdf_file': pdf_file,
        'extraction_results': {
            'pypdf2': pypdf2_analysis,
            'pdfplumber': pdfplumber_analysis,
            'pymupdf': pymupdf_analysis
        },
        'differences': {
            'pypdf2_vs_pdfplumber': pypdf2_vs_pdfplumber,
            'pymupdf_vs_pypdf2': pymupdf_vs_pypdf2
        }
    }
    
    with open('complete_extraction_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(complete_analysis, f, ensure_ascii=False, indent=2)
    
    # Zeige Zusammenfassung
    print('\n=== ZUSAMMENFASSUNG ===')
    print(f'PyPDF2 vs pdfplumber: {pypdf2_vs_pdfplumber["statistics"]["length_diff"]} Zeichen Unterschied')
    print(f'pymupdf vs PyPDF2: {pymupdf_vs_pypdf2["statistics"]["length_diff"]} Zeichen Unterschied')
    print()
    
    print('Anwesenheitsliste:')
    print(f'  PyPDF2: {pypdf2_analysis["sections"]["anwesenheit"]["person_count"] if pypdf2_analysis["sections"]["anwesenheit"]["found"] else "Nicht gefunden"} Personen')
    print(f'  pdfplumber: {pdfplumber_analysis["sections"]["anwesenheit"]["person_count"] if pdfplumber_analysis["sections"]["anwesenheit"]["found"] else "Nicht gefunden"} Personen')
    print(f'  pymupdf: {pymupdf_analysis["sections"]["anwesenheit"]["person_count"] if pymupdf_analysis["sections"]["anwesenheit"]["found"] else "Nicht gefunden"} Personen')
    print()
    
    print('TOP-Erkennung:')
    print(f'  PyPDF2: {pypdf2_analysis["sections"]["top_erkenntnis"]["total_tops"]} TOPs')
    print(f'  pdfplumber: {pdfplumber_analysis["sections"]["top_erkenntnis"]["total_tops"]} TOPs')
    print(f'  pymupdf: {pymupdf_analysis["sections"]["top_erkenntnis"]["total_tops"]} TOPs')
    print()
    
    print('Ergebnisse gespeichert in:')
    print('  - pypdf2_vs_pdfplumber_differences.json')
    print('  - pymupdf_vs_pypdf2_differences.json')
    print('  - complete_extraction_analysis.json')

if __name__ == '__main__':
    main()
