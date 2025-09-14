import json

# Lade und analysiere die aktuelle fields.json
with open('fields.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('=== AKTUELLE FIELDS.JSON ANALYSE ===')
print()

# Prüfe welche Felder enthalten sind
current_fields = [field['name'] for field in data['fields']]
print('📋 AKTUELLE FELDER:')
for field in current_fields:
    print(f'   - {field}')

print()
print('✅ ÜBERPRÜFUNG DER PROBLEME:')

# Problem 1: Ungelabelte Felder aus azure_metadata
problematic_metadata_fields = ['id', 'analysis_method', 'document_path', 'extraction_timestamp', 'full_text']
found_metadata_fields = [field for field in current_fields if field in problematic_metadata_fields]

if found_metadata_fields:
    print(f'   ❌ PROBLEM 1 - Ungelabelte Metadaten-Felder gefunden: {found_metadata_fields}')
else:
    print('   ✅ PROBLEM 1 - Keine ungelabelten Metadaten-Felder gefunden')

# Problem 2: Einzelwerte aus verschachtelten Objekten
problematic_nested_fields = ['total_present', 'total_excused', 'total_participants']
found_nested_fields = [field for field in current_fields if field in problematic_nested_fields]

if found_nested_fields:
    print(f'   ❌ PROBLEM 2 - Einzelwerte aus verschachtelten Objekten gefunden: {found_nested_fields}')
else:
    print('   ✅ PROBLEM 2 - Keine Einzelwerte aus verschachtelten Objekten gefunden')

# Problem 3: Typfehler
date_field = next((field for field in data['fields'] if field['name'] == 'date'), None)
if date_field:
    if date_field['type'] == 'date':
        print('   ✅ PROBLEM 3 - date ist korrekt als "date" typisiert')
    else:
        print(f'   ❌ PROBLEM 3 - date ist falsch typisiert als "{date_field["type"]}"')
else:
    print('   ⚠️ PROBLEM 3 - date Feld nicht gefunden')

# Gesamtbewertung
total_problems = len(found_metadata_fields) + len(found_nested_fields)
if date_field and date_field['type'] != 'date':
    total_problems += 1

print()
print('=== FINALE BEWERTUNG ===')
if total_problems == 0:
    print('🚀 ALLE PROBLEME BEHOBEN!')
    print('🚀 FIELDS.JSON IST KORREKT!')
else:
    print(f'❌ {total_problems} Probleme gefunden - Datei muss korrigiert werden')

print()
print('📊 FELD-STATISTIK:')
print(f'   - Gesamt Felder: {len(current_fields)}')
print(f'   - String Felder: {len([f for f in data["fields"] if f["type"] == "string"])}')
print(f'   - Date Felder: {len([f for f in data["fields"] if f["type"] == "date"])}')
print(f'   - Array Felder: {len([f for f in data["fields"] if f["type"] == "array"])}')
