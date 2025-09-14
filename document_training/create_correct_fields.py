import json
import os

def create_correct_fields_json():
    """Erstellt eine korrekte fields.json basierend auf tatsächlich gelabelten Feldern"""
    
    # Pfad zu den Labels
    labels_path = "../pohlheim_protokolle/Stavo"
    
    if not os.path.exists(labels_path):
        print(f"❌ Pfad nicht gefunden: {labels_path}")
        return
    
    # Finde alle .labels.json Dateien
    label_files = [f for f in os.listdir(labels_path) if f.endswith('.labels.json')]
    
    if not label_files:
        print(f"❌ Keine .labels.json Dateien in {labels_path} gefunden")
        return
    
    print(f"✅ Gefunden: {len(label_files)} .labels.json Dateien")
    
    # Sammle alle einzigartigen gelabelten Felder (mit boundingRegions)
    labeled_fields = {}
    
    for label_file in label_files:
        file_path = os.path.join(labels_path, label_file)
        print(f"\n📄 Analysiere: {label_file}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extrahiere nur Felder aus dem "fields" Objekt (nicht azure_metadata)
            if 'fields' in data:
                fields = data['fields']
                for field_name, field_data in fields.items():
                    field_type = field_data.get('type', 'unknown')
                    
                    # Prüfe ob das Feld boundingRegions hat (also gelabelt ist)
                    if 'boundingRegions' in field_data:
                        labeled_fields[field_name] = field_type
                        print(f"   ✅ {field_name}: {field_type} (gelabelt)")
                    else:
                        print(f"   ⚠️ {field_name}: {field_type} (keine boundingRegions)")
            else:
                print(f"   ❌ Kein 'fields' Objekt gefunden")
                
        except Exception as e:
            print(f"   ❌ Fehler beim Lesen: {e}")
    
    print(f"\n=== ZUSAMMENFASSUNG ===")
    print(f"📊 Gefundene gelabelte Felder: {len(labeled_fields)}")
    
    # Erstelle fields.json basierend auf gelabelten Feldern
    fields_json = {
        "fields": []
    }
    
    for field_name, field_type in labeled_fields.items():
        fields_json["fields"].append({
            "name": field_name,
            "type": field_type
        })
    
    # Speichere die fields.json im document_training Ordner
    output_path = "fields.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(fields_json, f, indent=2, ensure_ascii=False)
    
    print(f"✅ fields.json erstellt in document_training Ordner mit {len(labeled_fields)} gelabelten Feldern")
    
    # Zeige die erstellten Felder
    print(f"\n📋 ERSTELLTE FELDER:")
    for field in fields_json["fields"]:
        print(f"   - {field['name']}: {field['type']}")
    
    # Validiere die Datei
    print(f"\n✅ VALIDIERUNG:")
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            validation_data = json.load(f)
        
        print(f"   📊 JSON-Syntax: ✅ Korrekt")
        has_fields = "fields" in validation_data
        is_fields_list = isinstance(validation_data.get("fields"), list)
        print(f"   📊 Root-Struktur: ✅ {has_fields}")
        print(f"   📊 Fields Array: ✅ {is_fields_list}")
        fields_count = len(validation_data.get("fields", []))
        print(f"   📊 Anzahl Felder: {fields_count}")
        
        # Prüfe Azure-konforme Typen
        allowed_types = ['string', 'number', 'date', 'array', 'object']
        invalid_types = []
        for field in validation_data.get("fields", []):
            if field.get("type") not in allowed_types:
                invalid_types.append(f"{field.get('name')}: {field.get('type')}")
        
        if invalid_types:
            print(f"   ❌ Ungültige Typen: {invalid_types}")
        else:
            print(f"   ✅ Alle Typen Azure-konform")
            
    except Exception as e:
        print(f"   ❌ Validierungsfehler: {e}")
    
    return fields_json

if __name__ == "__main__":
    create_correct_fields_json()
