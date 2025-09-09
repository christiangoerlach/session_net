import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv('../config.env')

class DocumentModelTrainer:
    def __init__(self):
        self.endpoint = os.getenv('DOCUMENTINTELLIGENCE_ENDPOINT')
        self.api_key = os.getenv('DOCUMENTINTELLIGENCE_API_KEY')
        self.blob_sas_url = os.getenv('BLOBSASURL')
        
        if not self.endpoint or not self.api_key:
            raise ValueError("Document Intelligence Endpoint und API Key müssen in config.env gesetzt werden")
        
        if not self.blob_sas_url:
            # Fallback: Kombiniere Container URL und SAS Token
            blob_container_url = os.getenv('BLOBCONTAINERURL')
            blob_sas_token = os.getenv('BLOBSASTOKEN')
            
            if blob_container_url and blob_sas_token:
                self.blob_sas_url = f"{blob_container_url}?{blob_sas_token}"
            else:
                # Verwende feste Werte als Fallback
                blob_container_url = "https://sessionnetblob.blob.core.windows.net/containersessionnet"
                blob_sas_token = os.getenv('BLOBSASTOKEN')
                
                if blob_sas_token:
                    self.blob_sas_url = f"{blob_container_url}?{blob_sas_token}"
                else:
                    raise ValueError("BLOBSASURL oder BLOBSASTOKEN muss in config.env gesetzt werden")
        
        # Entferne trailing slash falls vorhanden
        self.endpoint = self.endpoint.rstrip('/')
        self.blob_url = self.blob_sas_url
        
    def train_custom_model(self, model_id, container_url=None, description=None, build_mode="template"):
        """
        Trainiert ein benutzerdefiniertes Document Intelligence Modell
        
        Args:
            model_id (str): Eindeutige ID für das Modell
            container_url (str): Azure Blob Storage Container URL mit SAS Token (optional, verwendet config.env wenn nicht angegeben)
            description (str): Beschreibung des Modells
            build_mode (str): "template" oder "neural" (Standard: template)
        
        Returns:
            dict: Antwort vom Azure Service
        """
        
        # Verwende Blob URL aus config.env falls nicht angegeben
        if not container_url:
            container_url = self.blob_url
        
        # API Endpoint für Modell-Training (Region: eastus)
        api_url = f"{self.endpoint}/documentIntelligence/documentModels:build?api-version=2024-02-29-preview"
        
        # Request Body
        request_body = {
            "modelId": model_id,
            "buildMode": build_mode,
            "azureBlobSource": {
                "containerUrl": container_url
            }
        }
        
        # Füge Beschreibung hinzu falls vorhanden
        if description:
            request_body["description"] = description
        
        # Headers
        headers = {
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": self.api_key
        }
        
        print(f"🚀 Starte Training für Modell: {model_id}")
        print(f"📦 Container URL: {container_url}")
        print(f"🔧 Build Mode: {build_mode}")
        print(f"📝 Beschreibung: {description or 'Keine'}")
        print(f"🌐 API Endpoint: {api_url}")
        
        # Überprüfe ob SAS Token in der URL ist
        if "?" in container_url and "sv=" in container_url:
            print("✅ SAS Token in Blob URL erkannt")
        else:
            print("⚠️  WARNUNG: Blob Container URL scheint keinen SAS Token zu enthalten!")
            print("   Stellen Sie sicher, dass die URL ein SAS Token enthält (z.B. ?sv=...)")
        
        # Debug: Zeige die vollständige Request-URL
        print(f"🔍 Debug: Vollständige Request-URL: {api_url}")
        print(f"🔍 Debug: Request Body: {json.dumps(request_body, indent=2)}")
        
        try:
            # Sende POST Request
            response = requests.post(
                api_url,
                headers=headers,
                json=request_body,
                timeout=30
            )
            
            print(f"\n📊 Response Status: {response.status_code}")
            
            if response.status_code == 202:
                print("✅ Training erfolgreich gestartet!")
                print("⏳ Das Training läuft im Hintergrund...")
                
                # Speichere Response für späteren Abruf
                response_data = response.json()
                self._save_training_info(model_id, response_data)
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "message": "Training erfolgreich gestartet",
                    "response": response_data
                }
                
            elif response.status_code == 400:
                print("❌ Fehler: Ungültige Anfrage")
                error_detail = response.json() if response.content else "Keine Details verfügbar"
                print(f"Fehlerdetails: {error_detail}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": "Bad Request",
                    "details": error_detail
                }
                
            elif response.status_code == 401:
                print("❌ Fehler: Unauthorized - API Key ungültig")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": "Unauthorized - API Key ungültig"
                }
                
            elif response.status_code == 404:
                print("❌ Fehler: Resource not found (404)")
                print("   Mögliche Ursachen:")
                print("   - Blob Container URL ist falsch oder nicht erreichbar")
                print("   - SAS Token fehlt oder ist abgelaufen")
                print("   - Container existiert nicht")
                print("   - Endpoint URL ist falsch")
                error_detail = response.json() if response.content else "Keine Details verfügbar"
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": "Resource not found (404)",
                    "details": error_detail,
                    "suggestions": [
                        "Überprüfen Sie die Blob Container URL",
                        "Stellen Sie sicher, dass ein gültiger SAS Token vorhanden ist",
                        "Überprüfen Sie den Document Intelligence Endpoint"
                    ]
                }
                
            else:
                print(f"❌ Unerwarteter Fehler: {response.status_code}")
                print(f"Response: {response.text}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": "Unerwarteter Fehler",
                    "response": response.text
                }
                
        except requests.exceptions.Timeout:
            print("❌ Timeout: Request dauerte zu lange")
            return {
                "success": False,
                "error": "Timeout - Request dauerte zu lange"
            }
            
        except requests.exceptions.ConnectionError:
            print("❌ Verbindungsfehler: Endpoint nicht erreichbar")
            return {
                "success": False,
                "error": "Verbindungsfehler - Endpoint nicht erreichbar"
            }
            
        except Exception as e:
            print(f"❌ Unerwarteter Fehler: {e}")
            return {
                "success": False,
                "error": f"Unerwarteter Fehler: {e}"
            }
    
    def get_model_status(self, model_id):
        """
        Ruft den aktuellen Status eines trainierten Modells ab
        
        Args:
            model_id (str): ID des Modells
            
        Returns:
            dict: Modell-Status und Details
        """
        
        api_url = f"{self.endpoint}/documentIntelligence/documentModels/{model_id}?api-version=2024-02-29-preview"
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key
        }
        
        try:
            response = requests.get(api_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                model_info = response.json()
                print(f"✅ Modell '{model_id}' Status abgerufen")
                return {
                    "success": True,
                    "model_info": model_info
                }
            else:
                print(f"❌ Fehler beim Abrufen des Modell-Status: {response.status_code}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
                
        except Exception as e:
            print(f"❌ Fehler beim Abrufen des Modell-Status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_models(self):
        """
        Listet alle verfügbaren Modelle auf
        
        Returns:
            dict: Liste aller Modelle
        """
        
        api_url = f"{self.endpoint}/documentIntelligence/documentModels?api-version=2024-02-29-preview"
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key
        }
        
        try:
            response = requests.get(api_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                models = response.json()
                print(f"✅ {len(models.get('value', []))} Modelle gefunden")
                return {
                    "success": True,
                    "models": models
                }
            else:
                print(f"❌ Fehler beim Auflisten der Modelle: {response.status_code}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
                
        except Exception as e:
            print(f"❌ Fehler beim Auflisten der Modelle: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def train_with_config_blob(self, model_id, description=None, build_mode="template"):
        """
        Trainiert ein Modell mit der Blob URL aus config.env
        
        Args:
            model_id (str): Eindeutige ID für das Modell
            description (str): Beschreibung des Modells
            build_mode (str): "template" oder "neural" (Standard: template)
        
        Returns:
            dict: Antwort vom Azure Service
        """
        return self.train_custom_model(
            model_id=model_id,
            container_url=self.blob_url,
            description=description,
            build_mode=build_mode
        )
    
    def _save_training_info(self, model_id, response_data):
        """Speichert Training-Informationen für späteren Abruf"""
        
        training_info = {
            "model_id": model_id,
            "training_started": datetime.now().isoformat(),
            "response": response_data
        }
        
        filename = f"{model_id}_training_info.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(training_info, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Training-Info gespeichert in: {filename}")


def main():
    """Hauptfunktion für interaktive Nutzung"""
    
    print("🤖 Azure Document Intelligence - Modell Training")
    print("=" * 50)
    
    try:
        trainer = DocumentModelTrainer()
        
        print("\n📋 Verfügbare Aktionen:")
        print("1. Schnell-Training (mit Blob URL aus config.env)")
        print("2. Modell-Status abrufen")
        print("3. Alle Modelle auflisten")
        print("4. Beenden")
        
        while True:
            choice = input("\n🎯 Wählen Sie eine Aktion (1-4): ").strip()
            
            if choice == "1":
                print("\n⚡ Schnell-Training mit config.env Blob URL:")
                
                model_id = input("📝 Modell-ID: ").strip()
                if not model_id:
                    print("❌ Modell-ID ist erforderlich!")
                    continue
                
                description = input("📄 Beschreibung (optional): ").strip()
                if not description:
                    description = f"Modell für {model_id} - trainiert am {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                
                build_mode = input("🔧 Build Mode (template/neural, Standard: template): ").strip()
                if not build_mode:
                    build_mode = "template"
                
                print(f"✅ Verwende Blob URL aus config.env: {trainer.blob_url}")
                
                result = trainer.train_with_config_blob(
                    model_id=model_id,
                    description=description,
                    build_mode=build_mode
                )
                
                if result["success"]:
                    print(f"\n✅ Training erfolgreich gestartet für Modell: {model_id}")
                    print("⏳ Überprüfen Sie den Status später mit Option 2")
                else:
                    print(f"\n❌ Training fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
                    print("🛑 Script wird beendet aufgrund des Fehlers.")
                    break
            
            elif choice == "2":
                print("\n📊 Modell-Status abrufen:")
                
                model_id = input("📝 Modell-ID: ").strip()
                if not model_id:
                    print("❌ Modell-ID ist erforderlich!")
                    continue
                
                result = trainer.get_model_status(model_id)
                
                if result["success"]:
                    model_info = result["model_info"]
                    print(f"\n✅ Modell '{model_id}' Details:")
                    print(f"   Status: {model_info.get('status', 'Unbekannt')}")
                    print(f"   Erstellt: {model_info.get('createdDateTime', 'Unbekannt')}")
                    print(f"   Beschreibung: {model_info.get('description', 'Keine')}")
                else:
                    print(f"\n❌ Fehler beim Abrufen des Status: {result.get('error', 'Unbekannter Fehler')}")
            
            elif choice == "3":
                print("\n📋 Alle Modelle auflisten:")
                
                result = trainer.list_models()
                
                if result["success"]:
                    models = result["models"].get("value", [])
                    if models:
                        print(f"\n✅ {len(models)} Modelle gefunden:")
                        for model in models:
                            print(f"   📝 {model.get('modelId', 'Unbekannt')} - Status: {model.get('status', 'Unbekannt')}")
                    else:
                        print("\n📭 Keine Modelle gefunden")
                else:
                    print(f"\n❌ Fehler beim Auflisten: {result.get('error', 'Unbekannter Fehler')}")
            
            elif choice == "4":
                print("\n👋 Auf Wiedersehen!")
                break
            
            else:
                print("❌ Ungültige Auswahl! Bitte wählen Sie 1-4.")
    
    except ValueError as e:
        print(f"❌ Konfigurationsfehler: {e}")
        print("\n🔧 Bitte überprüfen Sie Ihre config.env Datei:")
        print("   - DOCUMENTINTELLIGENCE_ENDPOINT")
        print("   - DOCUMENTINTELLIGENCE_API_KEY")
        print("   - BLOBSASURL")
    
    except KeyboardInterrupt:
        print("\n\n👋 Training abgebrochen!")
    
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")


if __name__ == "__main__":
    main()