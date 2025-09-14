import json

# Lade und validiere die neue fields.json Datei
with open('fields.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('=== NEUE FIELDS.JSON VALIDIERUNG ===')
print()

# Prüfe Struktur
print('✅ STRUKTUR-PRÜFUNG:')
print(f'   📊 Root-Level Keys: {list(data.keys())}')
print(f'   📊 Hat "fields" Key: {"fields" in data}')
print(f'   📊 "fields" ist Liste: {isinstance(data.get("fields"), list)}')
print(f'   📊 Anzahl Felder: {len(data.get("fields", []))}')

print()
print('✅ FELD-PRÜFUNG:')

# Erlaubte Azure-Typen
allowed_types = ['string', 'number', 'date', 'array', 'object']
field_count = 0
valid_fields = 0

for field in data.get('fields', []):
    field_count += 1
    name = field.get('name', '')
    field_type = field.get('type', '')
    
    # Prüfe ob alle erforderlichen Eigenschaften vorhanden sind
    has_name = 'name' in field and isinstance(field['name'], str) and field['name'].strip() != ''
    has_type = 'type' in field and field['type'] in allowed_types
    is_valid = has_name and has_type
    
    if is_valid:
        valid_fields += 1
        print(f'   ✅ {name} ({field_type})')
    else:
        print(f'   ❌ {name or "UNBEKANNT"} ({field_type or "UNBEKANNT"})')
        if not has_name:
            print(f'      - Fehler: name fehlt oder ungültig')
        if not has_type:
            print(f'      - Fehler: type fehlt oder ungültig (erlaubt: {allowed_types})')

print()
print('✅ TYP-STATISTIK:')
type_counts = {}
for field in data.get('fields', []):
    field_type = field.get('type', '')
    if field_type in allowed_types:
        type_counts[field_type] = type_counts.get(field_type, 0) + 1

for field_type, count in type_counts.items():
    print(f'   📋 {field_type}: {count} Felder')

print()
print('✅ FINALE BEWERTUNG:')
if valid_fields == field_count and field_count > 0:
    print('   🚀 ALLE FELDER SIND KORREKT!')
    print('   🚀 FIELDS.JSON IST BEREIT FÜR AZURE!')
else:
    print(f'   ❌ {field_count - valid_fields} Felder haben Probleme!')
    print('   ❌ Datei muss korrigiert werden!')
