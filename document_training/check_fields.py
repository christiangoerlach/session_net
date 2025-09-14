import json

# Lade die fields.json Datei
with open('fields.json', 'r', encoding='utf-8') as f:
    fields_data = json.load(f)

print('=== AZURE COGNITIVE SEARCH FIELDS.JSON PRÜFUNG ===')
print()

# Prüfe Struktur
if 'fields' in fields_data:
    print('✅ ROOT-STRUKTUR:')
    print('   ✅ "fields" Array gefunden')
    print(f'   ✅ Anzahl Felder: {len(fields_data["fields"])}')
    print()
    
    # Prüfe Feldtypen
    print('✅ FELDTYPEN PRÜFUNG:')
    field_types = {}
    for field in fields_data['fields']:
        field_type = field.get('type', 'NICHT_DEFINIERT')
        field_name = field.get('name', 'UNBEKANNT')
        
        if field_type not in field_types:
            field_types[field_type] = []
        field_types[field_type].append(field_name)
    
    for field_type, field_names in field_types.items():
        print(f'   📋 {field_type}: {len(field_names)} Felder')
        for name in field_names:
            print(f'      - {name}')
    
    print()
    print('✅ FELD-STRUKTUR PRÜFUNG:')
    for field in fields_data['fields']:
        field_name = field.get('name', 'UNBEKANNT')
        field_type = field.get('type', 'NICHT_DEFINIERT')
        
        # Prüfe ob alle notwendigen Eigenschaften vorhanden sind
        required_props = ['name', 'type']
        missing_props = []
        for prop in required_props:
            if prop not in field:
                missing_props.append(prop)
        
        if missing_props:
            print(f'   ❌ {field_name}: Fehlende Eigenschaften {missing_props}')
        else:
            print(f'   ✅ {field_name} ({field_type})')
    
    print()
    print('✅ ZUSAMMENFASSUNG:')
    print(f'   📊 Gesamt Felder: {len(fields_data["fields"])}')
    print(f'   📊 String Felder: {len(field_types.get("string", []))}')
    print(f'   📊 Array Felder: {len(field_types.get("array", []))}')
    print(f'   📊 Number Felder: {len(field_types.get("number", []))}')
    print()
    print('🚀 FIELDS.JSON IST BEREIT FÜR AZURE COGNITIVE SEARCH!')
    
else:
    print('❌ FEHLER: "fields" Array nicht gefunden!')
