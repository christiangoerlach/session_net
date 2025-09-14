import json
import os

def extract_labeled_fields_from_labels_json():
    """Extrahiert alle gelabelten Felder aus den .labels.json Dateien"""
    
    # Pfad zu den Labels
    labels_path = "pohlheim_protokolle/Stavo"
    
    if not os.path.exists(labels_path):
        print(f"❌ Pfad nicht gefunden: {labels_path}")
        return
    
    # Finde alle .labels.json Dateien
    label_files = [f for f in os.listdir(labels_path) if f.endswith('.labels.json')]
    
    if not label_files:
        print(f"❌ Keine .labels.json Dateien in {labels_path} gefunden")
        return
    
    print(f"✅ Gefunden: {len(label_files)} .labels.json Dateien")
    
    # Sammle alle einzigartigen Felder
    all_fields = {}
    
    for label_file in label_files:
        file_path = os.path.join(labels_path, label_file)
        print(f"\n📄 Analysiere: {label_file}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extrahiere Felder aus dem "fields" Objekt
            if 'fields' in data:
                fields = data['fields']
                for field_name, field_data in fields.items():
                    field_type = field_data.get('type', 'unknown')
                    
                    # Speichere das Feld (überschreibt bei Konflikten)
                    all_fields[field_name] = field_type
                    print(f"   ✅ {field_name}: {field_type}")
            else:
                print(f"   ❌ Kein 'fields' Objekt gefunden")
                
        except Exception as e:
            print(f"   ❌ Fehler beim Lesen: {e}")
    
    print(f"\n=== ZUSAMMENFASSUNG ===")
    print(f"📊 Gefundene gelabelte Felder: {len(all_fields)}")
    
    # Erstelle fields.json basierend auf gelabelten Feldern
    fields_json = {
        "fields": []
    }
    
    for field_name, field_type in all_fields.items():
        fields_json["fields"].append({
            "name": field_name,
            "type": field_type
        })
    
    # Speichere die fields.json
    with open('fields.json', 'w', encoding='utf-8') as f:
        json.dump(fields_json, f, indent=2, ensure_ascii=False)
    
    print(f"✅ fields.json erstellt mit {len(all_fields)} gelabelten Feldern")
    
    # Zeige die erstellten Felder
    print(f"\n📋 ERSTELLTE FELDER:")
    for field in fields_json["fields"]:
        print(f"   - {field['name']}: {field['type']}")
    
    return fields_json

if __name__ == "__main__":
    extract_labeled_fields_from_labels_json()
