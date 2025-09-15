import json

# Lade eine JSON-Datei
with open('output/2023_Mai_Stadtverordnetenversammlung_Niederschrift_STV.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('=== NEUE JSON STRUKTUR VON EXTRACT2.PY ===')
print()

for key, value in data.items():
    print(f'📋 {key}: {type(value).__name__}')
    
    if key == 'attendance' and isinstance(value, list):
        print(f'   └── [{len(value)} items]')
        print(f'       └── Unterfelder: name, function, status')
        # Zeige Status-Verteilung
        present_count = sum(1 for item in value if item.get('status') == 'present')
        excused_count = sum(1 for item in value if item.get('status') == 'excused')
        print(f'       └── Status: {present_count} present, {excused_count} excused')
    elif key == 'top_contents_text':
        print(f'   └── [{len(value)} Zeichen]')
        print(f'       └── Vorschau: {value[:100]}...')
    elif isinstance(value, list) and value and isinstance(value[0], dict):
        print(f'   └── [{len(value)} items]')
        print(f'       └── Unterfelder:')
        for subkey in value[0].keys():
            print(f'           • {subkey}: {type(value[0][subkey]).__name__}')
    elif isinstance(value, str) and len(value) > 100:
        print(f'   └── "{value[:97]}..."')
    elif isinstance(value, str):
        print(f'   └── "{value}"')
    else:
        print(f'   └── {value}')
    print()