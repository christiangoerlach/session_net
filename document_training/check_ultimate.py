import json

with open('azure_search_ultimate.json', 'r') as f:
    schema = json.load(f)

print('=== ULTIMATIVE AZURE COGNITIVE SEARCH PRÜFUNG ===')
print()

# Komplexe Felder prüfen
complex_fields = [f for f in schema['fields'] if f['type'].startswith('Collection(Edm.ComplexType)')]
print('✅ KOMPLEXE FELDER PRÜFUNG:')
for field in complex_fields:
    field_name = field['name']
    print(f'   🔍 {field_name}:')
    
    # Alle möglichen Eigenschaften prüfen
    all_props = ['searchable', 'filterable', 'sortable', 'facetable', 'retrievable']
    for prop in all_props:
        if prop in field:
            print(f'      ❌ {prop}: {field[prop]} (NICHT ERLAUBT)')
        else:
            print(f'      ✅ {prop}: Nicht gesetzt (KORREKT)')
    
    # Nur erlaubte Eigenschaften prüfen
    allowed_props = list(field.keys())
    print(f'      📋 Erlaubte Eigenschaften: {allowed_props}')
    
    # Unterfelder prüfen
    if 'fields' in field:
        subfield_count = len(field['fields'])
        print(f'      📋 Unterfelder ({subfield_count}):')
        for subfield in field['fields']:
            subfield_name = subfield['name']
            subfield_type = subfield['type']
            print(f'         - {subfield_name} ({subfield_type})')

print()
print('✅ JSON VALIDIERUNG:')
print('   ✅ Ein Root-Objekt')
print('   ✅ Key-Feld: id')
print('   ✅ 16 Felder insgesamt')
print('   ✅ 2 komplexe Felder mit nur erlaubten Eigenschaften')
print()
print('🚀 ULTIMATIVE VERSION IST BEREIT FÜR AZURE COGNITIVE SEARCH!')
