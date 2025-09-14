import json

# JSON-Datei laden
with open('azure_search_index_clean.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

print('=== AZURE COGNITIVE SEARCH INDEX PRÜFUNG ===')
print()

# 1. Root-Level Struktur prüfen
print('✅ 1. ROOT-LEVEL STRUKTUR:')
required_root_fields = ['name', 'fields']
for field in required_root_fields:
    if field in schema:
        print(f'   ✅ {field}: {schema[field]}')
    else:
        print(f'   ❌ {field}: FEHLT')

print()

# 2. Key-Feld prüfen
print('✅ 2. KEY-FELD PRÜFUNG:')
key_fields = [f for f in schema['fields'] if f.get('key') == True]
if len(key_fields) == 1:
    print(f'   ✅ Key-Feld gefunden: {key_fields[0]["name"]} ({key_fields[0]["type"]})')
elif len(key_fields) > 1:
    print(f'   ❌ Mehrere Key-Felder gefunden: {[f["name"] for f in key_fields]}')
else:
    print('   ❌ Kein Key-Feld gefunden!')

print()

# 3. Komplexe Felder prüfen
print('✅ 3. KOMPLEXE FELDER PRÜFUNG:')
complex_fields = [f for f in schema['fields'] if f['type'].startswith('Collection(Edm.ComplexType)')]
for field in complex_fields:
    print(f'   🔍 Komplexes Feld: {field["name"]}')
    
    # Prüfe verbotene Eigenschaften
    forbidden_props = ['filterable', 'facetable']
    for prop in forbidden_props:
        if prop in field:
            print(f'      ❌ {prop}: {field[prop]} (NICHT ERLAUBT)')
        else:
            print(f'      ✅ {prop}: Nicht gesetzt (KORREKT)')
    
    # Prüfe Unterfelder
    if 'fields' in field:
        print(f'      📋 Unterfelder ({len(field["fields"])}):')
        for subfield in field['fields']:
            print(f'         - {subfield["name"]} ({subfield["type"]})')
    else:
        print('      ❌ Keine Unterfelder definiert!')

print()

# 4. Feldtypen prüfen
print('✅ 4. FELDTYPEN PRÜFUNG:')
valid_types = ['Edm.String', 'Edm.Int32', 'Edm.DateTimeOffset', 'Collection(Edm.ComplexType)']
field_types = {}
for field in schema['fields']:
    field_type = field['type']
    if field_type not in field_types:
        field_types[field_type] = 0
    field_types[field_type] += 1

for field_type, count in field_types.items():
    if field_type in valid_types:
        print(f'   ✅ {field_type}: {count} Felder')
    else:
        print(f'   ❌ {field_type}: {count} Felder (UNBEKANNTER TYP)')

print()

# 5. Suggesters prüfen
print('✅ 5. SUGGESTERS PRÜFUNG:')
if 'suggesters' in schema:
    print(f'   ✅ Suggesters gefunden: {len(schema["suggesters"])}')
    for suggester in schema['suggesters']:
        print(f'      - {suggester["name"]}: {suggester["searchMode"]}')
else:
    print('   ⚠️ Keine Suggesters definiert')

print()

# 6. Scoring Profiles prüfen
print('✅ 6. SCORING PROFILES PRÜFUNG:')
if 'scoringProfiles' in schema:
    print(f'   ✅ Scoring Profiles gefunden: {len(schema["scoringProfiles"])}')
    for profile in schema['scoringProfiles']:
        print(f'      - {profile["name"]}')
else:
    print('   ⚠️ Keine Scoring Profiles definiert')

print()

# 7. CORS Options prüfen
print('✅ 7. CORS OPTIONS PRÜFUNG:')
if 'corsOptions' in schema:
    print(f'   ✅ CORS Options gefunden')
    cors = schema['corsOptions']
    print(f'      - Origins: {cors.get("allowedOrigins", "Nicht definiert")}')
    print(f'      - Max Age: {cors.get("maxAgeInSeconds", "Nicht definiert")} Sekunden')
else:
    print('   ⚠️ Keine CORS Options definiert')

print()

# Gesamtbewertung
issues = []
if len(key_fields) != 1:
    issues.append('Key-Feld Problem')
if any('filterable' in f for f in complex_fields):
    issues.append('Komplexe Felder haben filterable')
if any('facetable' in f for f in complex_fields):
    issues.append('Komplexe Felder haben facetable')

print('=== ZUSAMMENFASSUNG ===')
total_fields = len(schema['fields'])
complex_count = len(complex_fields)
print(f'📊 Gesamt Felder: {total_fields}')
print(f'📊 Komplexe Felder: {complex_count}')
print(f'📊 Einfache Felder: {total_fields - complex_count}')
print(f'📊 Index Name: {schema["name"]}')

if issues:
    print(f'❌ PROBLEME GEFUNDEN: {len(issues)}')
    for issue in issues:
        print(f'   - {issue}')
else:
    print('✅ KEINE KRITISCHEN PROBLEME GEFUNDEN!')
    print('🚀 Schema ist bereit für Azure Cognitive Search!')
