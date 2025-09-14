import json

# Erstelle eine neue, korrekte fields.json Datei
fields_data = {
    'fields': [
        {'name': 'id', 'type': 'string'},
        {'name': 'document_type', 'type': 'string'},
        {'name': 'session_type', 'type': 'string'},
        {'name': 'date', 'type': 'date'},
        {'name': 'duration', 'type': 'string'},
        {'name': 'location', 'type': 'string'},
        {'name': 'attendance_present', 'type': 'array'},
        {'name': 'attendance_excused', 'type': 'array'},
        {'name': 'total_present', 'type': 'number'},
        {'name': 'total_excused', 'type': 'number'},
        {'name': 'total_participants', 'type': 'number'},
        {'name': 'analysis_method', 'type': 'string'},
        {'name': 'total_pages', 'type': 'number'},
        {'name': 'extraction_timestamp', 'type': 'date'},
        {'name': 'document_path', 'type': 'string'},
        {'name': 'full_text', 'type': 'string'}
    ]
}

# Schreibe die Datei
with open('fields.json', 'w', encoding='utf-8') as f:
    json.dump(fields_data, f, indent=2, ensure_ascii=False)

print('✅ FIELDS.JSON ERSTELLT')
print()

# Prüfe die erstellte Datei
with open('fields.json', 'r', encoding='utf-8') as f:
    loaded_data = json.load(f)

print('✅ VALIDIERUNG:')
print(f'   📊 Root-Objekt: {"fields" in loaded_data}')
print(f'   📊 Fields Array: {isinstance(loaded_data.get("fields"), list)}')
print(f'   📊 Anzahl Felder: {len(loaded_data.get("fields", []))}')

# Prüfe Feldtypen
allowed_types = ['string', 'number', 'date', 'array', 'object']
field_types = {}
for field in loaded_data['fields']:
    field_type = field.get('type')
    if field_type in allowed_types:
        if field_type not in field_types:
            field_types[field_type] = 0
        field_types[field_type] += 1

print('   📊 Feldtypen:')
for field_type, count in field_types.items():
    print(f'      - {field_type}: {count} Felder')

print()
print('🚀 FIELDS.JSON IST BEREIT FÜR AZURE COGNITIVE SEARCH!')
