#!/usr/bin/env python3
"""
Azure Blob Storage - Document Intelligence Ordnerstruktur Organizer

Dieses Script organisiert Dokumente im Azure Blob Container 
für Document Intelligence Training in die richtige Ordnerstruktur.

Erwartete Struktur:
container/
├── training/
│   └── documents/    ← PDF-Dokumente für Training
└── testing/
    └── documents/     ← PDF-Dokumente für Tests (optional)
"""

import os
import requests
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
import json
from datetime import datetime

# Lade Umgebungsvariablen
load_dotenv('../config.env')

class BlobOrganizer:
    def __init__(self, training_documents_path=None, training_labels_path=None):
        self.blob_sas_url = os.getenv('BLOBSASURL')
        self.container_name = "containersessionnet"
        
        # Konfigurierbare Pfade für Document Intelligence
        # Standard: Root-Verzeichnis (keine Ordner im Container)
        self.training_documents_path = (
            training_documents_path or 
            os.getenv('TRAINING_DOCUMENTS_PATH', '')  # Root = leerer String
        )
        self.training_labels_path = (
            training_labels_path or 
            os.getenv('TRAINING_LABELS_PATH', '')  # Root = leerer String
        )
        
        if not self.blob_sas_url:
            raise ValueError("BLOBSASURL muss in config.env gesetzt werden")
        
        # Parse SAS URL
        parsed_url = urlparse(self.blob_sas_url)
        self.account_name = parsed_url.netloc.split('.')[0]
        self.sas_token = parsed_url.query
        
        # Base URL für Blob Service
        self.base_url = f"https://{self.account_name}.blob.core.windows.net"
        
    def list_blobs(self, prefix=""):
        """
        Listet alle Blobs im Container auf
        
        Args:
            prefix (str): Ordner-Präfix für Filterung
            
        Returns:
            list: Liste der Blob-Namen
        """
        url = f"{self.base_url}/{self.container_name}"
        params = {
            'restype': 'container',
            'comp': 'list',
            'prefix': prefix
        }
        
        # Füge SAS Token zu den Parametern hinzu
        sas_params = parse_qs(self.sas_token)
        for key, value in sas_params.items():
            params[key] = value[0]
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse XML Response (vereinfacht)
            blobs = []
            content = response.text
            
            # Einfache XML-Parsing für Blob-Namen
            import re
            blob_pattern = r'<Name>(.*?)</Name>'
            matches = re.findall(blob_pattern, content)
            
            for match in matches:
                if match and not match.endswith('/'):  # Ignoriere Ordner
                    blobs.append(match)
            
            return blobs
            
        except Exception as e:
            print(f"❌ Fehler beim Auflisten der Blobs: {e}")
            return []
    
    def copy_blob(self, source_blob, dest_blob):
        """
        Kopiert einen Blob innerhalb des Containers
        
        Args:
            source_blob (str): Quell-Blob-Name
            dest_blob (str): Ziel-Blob-Name
            
        Returns:
            bool: True wenn erfolgreich
        """
        source_url = f"{self.base_url}/{self.container_name}/{source_blob}?{self.sas_token}"
        dest_url = f"{self.base_url}/{self.container_name}/{dest_blob}"
        
        headers = {
            'x-ms-copy-source': source_url,
            'x-ms-requires-sync': 'true'
        }
        
        # Füge SAS Token zu dest_url hinzu
        dest_url_with_sas = f"{dest_url}?{self.sas_token}"
        
        try:
            response = requests.put(dest_url_with_sas, headers=headers, timeout=30)
            response.raise_for_status()
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Kopieren von {source_blob} zu {dest_blob}: {e}")
            return False
    
    def delete_blob(self, blob_name):
        """
        Löscht einen Blob
        
        Args:
            blob_name (str): Name des zu löschenden Blobs
            
        Returns:
            bool: True wenn erfolgreich
        """
        url = f"{self.base_url}/{self.container_name}/{blob_name}?{self.sas_token}"
        
        try:
            response = requests.delete(url, timeout=30)
            response.raise_for_status()
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Löschen von {blob_name}: {e}")
            return False
    
    def organize_for_document_intelligence(self, move_files=True, use_root=True):
        """
        Organisiert Dokumente für Document Intelligence Training
        
        Args:
            move_files (bool): True = Dateien verschieben, False = nur kopieren
            use_root (bool): True = Dokumente im Root lassen, False = in Ordnerstruktur
            
        Returns:
            dict: Ergebnis der Organisation
        """
        print("🔍 Analysiere Blob Container Struktur...")
        
        # Liste alle Blobs auf
        all_blobs = self.list_blobs()
        
        if not all_blobs:
            print("❌ Keine Blobs im Container gefunden!")
            return {"success": False, "error": "Keine Blobs gefunden"}
        
        print(f"📋 {len(all_blobs)} Blobs gefunden:")
        for blob in all_blobs:
            print(f"   📄 {blob}")
        
        # Filtere PDF-Dokumente
        pdf_blobs = [blob for blob in all_blobs if blob.lower().endswith('.pdf')]
        json_blobs = [blob for blob in all_blobs if blob.lower().endswith('.json')]
        
        print(f"\n📊 Dokumente gefunden:")
        print(f"   📄 PDF-Dateien: {len(pdf_blobs)}")
        print(f"   📋 JSON-Dateien: {len(json_blobs)}")
        
        if not pdf_blobs:
            print("❌ Keine PDF-Dokumente für Training gefunden!")
            return {"success": False, "error": "Keine PDF-Dokumente gefunden"}
        
        # Organisiere PDF-Dokumente
        if use_root:
            print(f"\n🔄 Organisiere {len(pdf_blobs)} PDF-Dokumente im Root...")
            print("ℹ️  Dokumente bleiben im Root-Verzeichnis (keine Ordner im Container)")
        else:
            print(f"\n🔄 Organisiere {len(pdf_blobs)} PDF-Dokumente in Ordnerstruktur...")
        
        success_count = 0
        error_count = 0
        
        for pdf_blob in pdf_blobs:
            if use_root:
                # Dokumente im Root lassen (nur kopieren wenn nötig)
                dest_blob = pdf_blob
                if pdf_blob == dest_blob:
                    print(f"   ✅ Bereits im Root: {pdf_blob}")
                    success_count += 1
                    continue
            else:
                # Ziel-Pfad: konfigurierbarer Pfad/original_name.pdf
                if self.training_documents_path:
                    dest_blob = f"{self.training_documents_path}/{pdf_blob}"
                else:
                    dest_blob = pdf_blob
            
            print(f"   📄 {pdf_blob} → {dest_blob}")
            
            if self.copy_blob(pdf_blob, dest_blob):
                success_count += 1
                
                # Lösche Original wenn move_files=True und nicht im Root
                if move_files and pdf_blob != dest_blob:
                    if self.delete_blob(pdf_blob):
                        print(f"   ✅ Verschoben: {pdf_blob}")
                    else:
                        print(f"   ⚠️  Kopiert (Original nicht gelöscht): {pdf_blob}")
                else:
                    print(f"   ✅ Kopiert: {pdf_blob}")
            else:
                error_count += 1
                print(f"   ❌ Fehler: {pdf_blob}")
        
        # Organisiere JSON-Dateien (Labels)
        if json_blobs:
            if use_root:
                print(f"\n🔄 Organisiere {len(json_blobs)} JSON-Dateien im Root...")
            else:
                print(f"\n🔄 Organisiere {len(json_blobs)} JSON-Dateien in Ordnerstruktur...")
            
            for json_blob in json_blobs:
                if use_root:
                    # Labels im Root lassen
                    dest_blob = json_blob
                    if json_blob == dest_blob:
                        print(f"   ✅ Bereits im Root: {json_blob}")
                        success_count += 1
                        continue
                else:
                    # Ziel-Pfad: konfigurierbarer Pfad/original_name.json
                    if self.training_labels_path:
                        dest_blob = f"{self.training_labels_path}/{json_blob}"
                    else:
                        dest_blob = json_blob
                
                print(f"   📋 {json_blob} → {dest_blob}")
                
                if self.copy_blob(json_blob, dest_blob):
                    success_count += 1
                    
                    if move_files and json_blob != dest_blob:
                        if self.delete_blob(json_blob):
                            print(f"   ✅ Verschoben: {json_blob}")
                        else:
                            print(f"   ⚠️  Kopiert (Original nicht gelöscht): {json_blob}")
                    else:
                        print(f"   ✅ Kopiert: {json_blob}")
                else:
                    error_count += 1
                    print(f"   ❌ Fehler: {json_blob}")
        
        # Zeige finale Struktur
        print(f"\n📁 Finale Container-Struktur:")
        final_blobs = self.list_blobs()
        
        if use_root:
            # Zeige nur Root-Dateien
            root_files = [b for b in final_blobs if '/' not in b]
            for blob in sorted(root_files):
                print(f"   📄 {blob}")
        else:
            # Zeige Ordnerstruktur
            training_blobs = [b for b in final_blobs if b.startswith('training/')]
            for blob in sorted(training_blobs):
                print(f"   📄 {blob}")
        
        return {
            "success": error_count == 0,
            "pdf_count": len(pdf_blobs),
            "json_count": len(json_blobs),
            "success_count": success_count,
            "error_count": error_count,
            "use_root": use_root,
            "final_structure": final_blobs
        }
    
    def show_current_structure(self):
        """Zeigt die aktuelle Container-Struktur"""
        print("📁 Aktuelle Container-Struktur:")
        
        all_blobs = self.list_blobs()
        
        if not all_blobs:
            print("   📭 Container ist leer")
            return
        
        # Gruppiere nach Ordnern
        folders = {}
        root_files = []
        
        for blob in all_blobs:
            if '/' in blob:
                folder = blob.split('/')[0]
                if folder not in folders:
                    folders[folder] = []
                folders[folder].append(blob)
            else:
                root_files.append(blob)
        
        # Zeige Root-Dateien
        if root_files:
            print("   📄 Root-Verzeichnis:")
            for file in sorted(root_files):
                print(f"      📄 {file}")
        
        # Zeige Ordner
        for folder, files in sorted(folders.items()):
            print(f"   📁 {folder}/")
            for file in sorted(files):
                print(f"      📄 {file}")


def main():
    """Hauptfunktion"""
    print("🗂️  Azure Blob Storage - Document Intelligence Organizer")
    print("=" * 60)
    
    try:
        organizer = BlobOrganizer()
        
        print("\n📋 Verfügbare Aktionen:")
        print("1. Aktuelle Struktur anzeigen")
        print("2. Dokumente organisieren (kopieren) - Root")
        print("3. Dokumente organisieren (verschieben) - Root")
        print("4. Dokumente in Ordnerstruktur organisieren (kopieren)")
        print("5. Dokumente in Ordnerstruktur organisieren (verschieben)")
        print("6. Pfade konfigurieren")
        print("7. Beenden")
        
        while True:
            choice = input("\n🎯 Wählen Sie eine Aktion (1-7): ").strip()
            
            if choice == "1":
                print("\n📁 Aktuelle Container-Struktur:")
                organizer.show_current_structure()
            
            elif choice == "2":
                print("\n🔄 Dokumente organisieren (kopieren) - Root...")
                result = organizer.organize_for_document_intelligence(move_files=False, use_root=True)
                
                if result["success"]:
                    print(f"\n✅ Organisation erfolgreich!")
                    print(f"   📄 PDF-Dokumente: {result['pdf_count']}")
                    print(f"   📋 JSON-Dateien: {result['json_count']}")
                    print(f"   ✅ Erfolgreich: {result['success_count']}")
                    print(f"   ❌ Fehler: {result['error_count']}")
                else:
                    print(f"\n❌ Organisation fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
            
            elif choice == "3":
                print("\n🔄 Dokumente organisieren (verschieben) - Root...")
                confirm = input("⚠️  Dies wird die Original-Dateien löschen! Fortfahren? (j/n): ").strip().lower()
                
                if confirm in ['j', 'ja', 'y', 'yes']:
                    result = organizer.organize_for_document_intelligence(move_files=True, use_root=True)
                    
                    if result["success"]:
                        print(f"\n✅ Organisation erfolgreich!")
                        print(f"   📄 PDF-Dokumente: {result['pdf_count']}")
                        print(f"   📋 JSON-Dateien: {result['json_count']}")
                        print(f"   ✅ Erfolgreich: {result['success_count']}")
                        print(f"   ❌ Fehler: {result['error_count']}")
                    else:
                        print(f"\n❌ Organisation fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
                else:
                    print("❌ Organisation abgebrochen")
            
            elif choice == "4":
                print("\n🔄 Dokumente in Ordnerstruktur organisieren (kopieren)...")
                result = organizer.organize_for_document_intelligence(move_files=False, use_root=False)
                
                if result["success"]:
                    print(f"\n✅ Organisation erfolgreich!")
                    print(f"   📄 PDF-Dokumente: {result['pdf_count']}")
                    print(f"   📋 JSON-Dateien: {result['json_count']}")
                    print(f"   ✅ Erfolgreich: {result['success_count']}")
                    print(f"   ❌ Fehler: {result['error_count']}")
                else:
                    print(f"\n❌ Organisation fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
            
            elif choice == "5":
                print("\n🔄 Dokumente in Ordnerstruktur organisieren (verschieben)...")
                confirm = input("⚠️  Dies wird die Original-Dateien löschen! Fortfahren? (j/n): ").strip().lower()
                
                if confirm in ['j', 'ja', 'y', 'yes']:
                    result = organizer.organize_for_document_intelligence(move_files=True, use_root=False)
                    
                    if result["success"]:
                        print(f"\n✅ Organisation erfolgreich!")
                        print(f"   📄 PDF-Dokumente: {result['pdf_count']}")
                        print(f"   📋 JSON-Dateien: {result['json_count']}")
                        print(f"   ✅ Erfolgreich: {result['success_count']}")
                        print(f"   ❌ Fehler: {result['error_count']}")
                    else:
                        print(f"\n❌ Organisation fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
                else:
                    print("❌ Organisation abgebrochen")
            
            elif choice == "6":
                print("\n⚙️  Pfade konfigurieren:")
                print(f"   Aktueller Dokumente-Pfad: {organizer.training_documents_path}")
                print(f"   Aktueller Labels-Pfad: {organizer.training_labels_path}")
                
                new_docs_path = input(f"\n📄 Neuer Dokumente-Pfad (Enter für aktuell): ").strip()
                new_labels_path = input(f"📋 Neuer Labels-Pfad (Enter für aktuell): ").strip()
                
                if new_docs_path:
                    organizer.training_documents_path = new_docs_path
                    print(f"✅ Dokumente-Pfad geändert zu: {organizer.training_documents_path}")
                
                if new_labels_path:
                    organizer.training_labels_path = new_labels_path
                    print(f"✅ Labels-Pfad geändert zu: {organizer.training_labels_path}")
                
                if not new_docs_path and not new_labels_path:
                    print("ℹ️  Keine Änderungen vorgenommen")
            
            elif choice == "7":
                print("\n👋 Auf Wiedersehen!")
                break
            
            else:
                print("❌ Ungültige Auswahl! Bitte wählen Sie 1-7.")
    
    except ValueError as e:
        print(f"❌ Konfigurationsfehler: {e}")
        print("\n🔧 Bitte überprüfen Sie Ihre config.env Datei:")
        print("   - BLOBSASURL")
    
    except KeyboardInterrupt:
        print("\n\n👋 Organisation abgebrochen!")
    
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")


if __name__ == "__main__":
    main()
