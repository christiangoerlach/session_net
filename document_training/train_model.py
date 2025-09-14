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
        
        # Debug-Logging aktivieren
        self.debug_log_file = f"document_intelligence_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self._log_debug("=== DOCUMENT INTELLIGENCE DEBUG SESSION STARTED ===")
        self._log_debug(f"Endpoint: {self.endpoint}")
        self._log_debug(f"API Key: {self.api_key[:10]}..." if self.api_key else "API Key: NOT SET")
        self._log_debug(f"Blob SAS URL: {self.blob_sas_url[:50]}..." if self.blob_sas_url else "Blob SAS URL: NOT SET")
        
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
        
    def _log_debug(self, message):
        """Schreibt Debug-Nachrichten in die Log-Datei"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        log_entry = f"[{timestamp}] {message}\n"
        
        try:
            with open(self.debug_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"⚠️ Fehler beim Schreiben der Debug-Datei: {e}")
        
        # Auch in der Konsole ausgeben
        print(f"🔍 DEBUG: {message}")
    
    def _log_request(self, method, url, headers=None, data=None, json_data=None):
        """Protokolliert einen ausgehenden Request"""
        self._log_debug(f"=== OUTGOING REQUEST ===")
        self._log_debug(f"Method: {method}")
        self._log_debug(f"URL: {url}")
        
        if headers:
            # Verstecke API Key in Headers für Debugging
            debug_headers = headers.copy()
            if 'Ocp-Apim-Subscription-Key' in debug_headers:
                debug_headers['Ocp-Apim-Subscription-Key'] = f"{debug_headers['Ocp-Apim-Subscription-Key'][:10]}..."
            self._log_debug(f"Headers: {json.dumps(debug_headers, indent=2)}")
        
        if data:
            self._log_debug(f"Data: {data}")
        
        if json_data:
            self._log_debug(f"JSON Data: {json.dumps(json_data, indent=2, ensure_ascii=False)}")
    
    def _log_response(self, response):
        """Protokolliert eine eingehende Response"""
        self._log_debug(f"=== INCOMING RESPONSE ===")
        self._log_debug(f"Status Code: {response.status_code}")
        self._log_debug(f"Headers: {dict(response.headers)}")
        
        try:
            response_text = response.text
            self._log_debug(f"Response Body: {response_text}")
            
            # Versuche JSON zu parsen für bessere Lesbarkeit
            try:
                response_json = response.json()
                self._log_debug(f"Response JSON (formatted): {json.dumps(response_json, indent=2, ensure_ascii=False)}")
            except:
                pass
                
        except Exception as e:
            self._log_debug(f"Error reading response: {e}")
    
    def _make_request(self, method, url, headers=None, data=None, json_data=None, params=None):
        """Macht einen Request und protokolliert alles"""
        self._log_request(method, url, headers, data, json_data)
        if params:
            self._log_debug(f"Query Parameters: {params}")
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, data=data, json=json_data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, data=data, json=json_data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            self._log_response(response)
            return response
            
        except Exception as e:
            self._log_debug(f"Request failed with exception: {e}")
            raise
        
    def _get_container_url_without_sas(self):
        """Erstellt Container-URL ohne SAS Token für Document Intelligence"""
        from urllib.parse import urlparse
        
        # Parse die SAS-URL
        parsed_url = urlparse(self.blob_sas_url)
        
        # Erstelle Container-URL ohne SAS Token
        container_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        
        return container_url
    
    def _fix_container_url_for_sas_token(self):
        """
        Korrigiert die Container-URL falls der SAS Token für $root generiert wurde
        """
        from urllib.parse import urlparse, parse_qs
        
        # Parse die SAS-URL
        parsed_url = urlparse(self.blob_sas_url)
        
        print(f"🔍 URL-Analyse:")
        print(f"   📦 Vollständige URL: {self.blob_sas_url}")
        print(f"   🛣️  Pfad: '{parsed_url.path}'")
        print(f"   🔑 SAS Token: {parsed_url.query[:50]}...")
        
        # Prüfe ob der SAS Token für $root generiert wurde
        if parsed_url.path == '/container2':
            # SAS Token ist für container2 - verwende direkt
            print(f"✅ SAS Token ist für container2 - verwende direkt")
            return self.blob_sas_url
        elif parsed_url.path == '' or parsed_url.path == '/':
            # SAS Token ist für $root - verwende $root Container
            print(f"🔧 SAS Token ist für $root - verwende $root Container")
            return self.blob_sas_url
        else:
            # Unbekannter Container - verwende direkt
            print(f"⚠️  Unbekannter Container-Pfad: '{parsed_url.path}' - verwende direkt")
            return self.blob_sas_url
        
    def upload_training_data_to_blob(self, local_folder_path, blob_folder_name="training_data"):
        """
        Lädt Trainingsdaten in Azure Blob Storage hoch
        
        Args:
            local_folder_path (str): Lokaler Pfad zu den Trainingsdaten
            blob_folder_name (str): Name des Ordners im Blob Storage
        
        Returns:
            bool: True wenn erfolgreich
        """
        try:
            from azure.storage.blob import BlobServiceClient, BlobClient
            import os
            
            # Parse SAS URL für BlobServiceClient
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(self.blob_sas_url)
            
            # Erstelle BlobServiceClient mit SAS URL
            # Verwende die vollständige SAS URL als credential
            from azure.core.credentials import AzureSasCredential
            
            # Extrahiere SAS Token aus URL
            sas_token = parsed_url.query
            
            # Erstelle BlobServiceClient mit SAS Token
            blob_service_client = BlobServiceClient(
                account_url=f"https://{parsed_url.netloc}", 
                credential=AzureSasCredential(sas_token)
            )
            
            # Container-Name aus URL extrahieren
            # Verwende container2 da SAS Token dafür generiert wurde
            container_name = parsed_url.path.lstrip('/')
            if not container_name or container_name == '':
                container_name = 'container2'
            print(f"🔧 Verwende Container: {container_name}")
            
            print(f"📤 Lade Trainingsdaten hoch...")
            print(f"   📁 Lokaler Ordner: {local_folder_path}")
            print(f"   📦 Blob Container: {container_name}")
            print(f"   📂 Blob Ordner: {blob_folder_name}")
            
            # Finde alle PDF und JSON Dateien
            pdf_files = [f for f in os.listdir(local_folder_path) if f.lower().endswith('.pdf')]
            json_files = [f for f in os.listdir(local_folder_path) if f.lower().endswith('.labels.json')]
            
            print(f"   📄 Gefunden: {len(pdf_files)} PDF-Dateien")
            print(f"   📋 Gefunden: {len(json_files)} JSON-Dateien")
            
            # Lade PDF-Dateien hoch
            for pdf_file in pdf_files:
                local_path = os.path.join(local_folder_path, pdf_file)
                blob_path = f"{blob_folder_name}/{pdf_file}" if blob_folder_name else pdf_file
                
                blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)
                
                with open(local_path, "rb") as data:
                    blob_client.upload_blob(data, overwrite=True)
                
                print(f"   ✅ PDF hochgeladen: {pdf_file}")
            
            # Lade JSON-Dateien hoch
            for json_file in json_files:
                local_path = os.path.join(local_folder_path, json_file)
                blob_path = f"{blob_folder_name}/{json_file}" if blob_folder_name else json_file
                
                blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)
                
                with open(local_path, "rb") as data:
                    blob_client.upload_blob(data, overwrite=True)
                
                print(f"   ✅ JSON hochgeladen: {json_file}")
            
            print(f"🎉 Alle Trainingsdaten erfolgreich hochgeladen!")
            self._log_debug("Upload completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Hochladen: {e}")
            self._log_debug(f"Upload failed with error: {e}")
            return False

    def train_with_local_data(self, model_id, local_folder, description=None, build_mode="template"):
        """
        Trainiert ein Modell mit lokalen Trainingsdaten
        
        Args:
            model_id (str): Eindeutige ID für das Modell
            local_folder (str): Lokaler Pfad zu den Trainingsdaten
            description (str): Beschreibung des Modells
            build_mode (str): "template" oder "neural"
        
        Returns:
            dict: Antwort vom Azure Service
        """
        try:
            import os
            import base64
            
            # Finde alle PDF und JSON Dateien
            pdf_files = [f for f in os.listdir(local_folder) if f.lower().endswith('.pdf')]
            json_files = [f for f in os.listdir(local_folder) if f.lower().endswith('.labels.json')]
            
            print(f"📄 Gefunden: {len(pdf_files)} PDF-Dateien")
            print(f"📋 Gefunden: {len(json_files)} JSON-Dateien")
            
            if not pdf_files or not json_files:
                return {"success": False, "error": "Keine Trainingsdaten gefunden"}
            
            # API Endpoint für Modell-Training
            api_url = f"{self.endpoint}/documentIntelligence/documentModels:build?api-version=2024-02-29-preview"
            
            # Erstelle Trainingsdaten-Array
            training_data = []
            
            for pdf_file in pdf_files:
                pdf_path = os.path.join(local_folder, pdf_file)
                base_name = os.path.splitext(pdf_file)[0]
                json_file = f"{base_name}.labels.json"
                json_path = os.path.join(local_folder, json_file)
                
                if os.path.exists(json_path):
                    # Lese PDF-Datei
                    with open(pdf_path, "rb") as f:
                        pdf_content = base64.b64encode(f.read()).decode('utf-8')
                    
                    # Lese JSON-Labels
                    with open(json_path, "r", encoding="utf-8") as f:
                        labels = json.load(f)
                    
                    training_data.append({
                        "document": pdf_content,
                        "labels": labels
                    })
                    
                    print(f"   ✅ Trainingsdaten vorbereitet: {pdf_file}")
                else:
                    print(f"   ⚠️  JSON-Datei nicht gefunden: {json_file}")
            
            if not training_data:
                return {"success": False, "error": "Keine gültigen Trainingsdaten gefunden"}
            
            # Request Body
            request_body = {
                "modelId": model_id,
                "buildMode": build_mode,
                "trainingData": training_data
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
            print(f"🔧 Build Mode: {build_mode}")
            print(f"📝 Beschreibung: {description or 'Keine'}")
            print(f"📊 Trainingsdaten: {len(training_data)} Dokumente")
            
            # Sende Training-Request
            response = self._make_request('POST', api_url, headers=headers, json_data=request_body)
            
            if response.status_code == 202:
                # Training erfolgreich gestartet
                result = response.json()
                return {
                    "success": True,
                    "model_id": model_id,
                    "operation_location": response.headers.get("Operation-Location"),
                    "response": result
                }
            else:
                # Fehler beim Training
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_details = response.json()
                    error_msg += f": {error_details}"
                except:
                    error_msg += f": {response.text}"
                
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

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
            # Für Document Intelligence: Container-URL MIT SAS Token
            # Korrigiere Container-URL falls SAS Token für $root generiert wurde
            container_url = self._fix_container_url_for_sas_token()
        
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
        print(f"📦 Container URL (mit SAS): {container_url}")
        print(f"🔧 Build Mode: {build_mode}")
        print(f"📝 Beschreibung: {description or 'Keine'}")
        print(f"🌐 API Endpoint: {api_url}")
        
        # Detaillierte URL-Informationen für Debugging
        print(f"\n📋 DETAILLIERTE URL-INFORMATIONEN:")
        print(f"   🎯 Container-URL für Document Intelligence:")
        print(f"      {container_url}")
        print(f"   📁 Diese URL zeigt auf den Container-Root (MIT SAS Token)")
        print(f"   📄 Document Intelligence benötigt SAS Token für Blob-Zugriff")
        print(f"   🔑 Authentifizierung über SAS Token + API Key")
        
        # Zeige auch die ursprüngliche SAS-URL zum Vergleich
        print(f"\n🔍 SAS TOKEN ANALYSE:")
        print(f"   📦 Vollständige SAS-URL: {self.blob_sas_url}")
        print(f"   ✅ Document Intelligence verwendet SAS Token für Blob-Zugriff")
        
        # Parse und zeige URL-Komponenten
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(container_url)
        print(f"\n🔍 URL-KOMPONENTEN (Container-URL mit SAS):")
        print(f"   🌐 Protokoll: {parsed_url.scheme}")
        print(f"   🏢 Account: {parsed_url.netloc}")
        print(f"   📦 Container: {parsed_url.path.lstrip('/')}")
        print(f"   🔑 SAS Token vorhanden: {'Ja' if parsed_url.query else 'Nein'}")
        
        if parsed_url.query:
            sas_params = parse_qs(parsed_url.query)
            print(f"   📅 SAS Token Details:")
            if 'st' in sas_params:
                print(f"      Start: {sas_params['st'][0]}")
            if 'se' in sas_params:
                print(f"      Ende: {sas_params['se'][0]}")
            if 'sp' in sas_params:
                print(f"      Berechtigungen: {sas_params['sp'][0]}")
            if 'sv' in sas_params:
                print(f"      Version: {sas_params['sv'][0]}")
            if 'sig' in sas_params:
                print(f"      Signatur: {sas_params['sig'][0][:20]}...")
            
            # Prüfe SAS Token-Container-Kompatibilität
            self._check_sas_token_compatibility(parsed_url, sas_params)
        
        print(f"\n✅ Document Intelligence wird Dokumente aus diesem Container-Root verwenden")
        
        # Zeige verfügbare Dokumente im Container (optional)
        try:
            self._show_container_documents(container_url)
        except Exception as e:
            print(f"⚠️  Konnte Container-Inhalte nicht abrufen: {e}")
        
        # Überprüfe ob SAS Token in der URL ist
        if "?" in container_url and "sv=" in container_url:
            print("✅ SAS Token in Container URL erkannt")
            print("ℹ️  Document Intelligence verwendet SAS Token für Blob-Zugriff")
        else:
            print("⚠️  WARNUNG: Container URL scheint keinen SAS Token zu enthalten!")
            print("   Stellen Sie sicher, dass die URL ein SAS Token enthält (z.B. ?sv=...)")
        
        # Debug: Zeige die vollständige Request-URL
        print(f"\n🔍 DEBUG: Vollständige Request-URL: {api_url}")
        print(f"🔍 DEBUG: Request Body: {json.dumps(request_body, indent=2)}")
        
        try:
            # Sende POST Request
            response = self._make_request('POST', api_url, headers=headers, json_data=request_body)
            
            print(f"\n📊 Response Status: {response.status_code}")
            
            if response.status_code == 202:
                print("✅ Training erfolgreich gestartet!")
                print("⏳ Das Training läuft im Hintergrund...")
                
                # Speichere Response für späteren Abruf (falls vorhanden)
                if response.content:
                    try:
                        response_data = response.json()
                    except json.JSONDecodeError:
                        print("⚠️  Response ist nicht im JSON-Format, verwende leeres Objekt")
                        response_data = {}
                else:
                    print("ℹ️  Leere Response erhalten (normal bei 202 Status)")
                    response_data = {}
                
                self._save_training_info(model_id, response_data)
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "message": "Training erfolgreich gestartet",
                    "response": response_data
                }
                
            elif response.status_code == 400:
                print("❌ Fehler: Ungültige Anfrage")
                if response.content:
                    try:
                        error_detail = response.json()
                    except json.JSONDecodeError:
                        error_detail = response.text or "Keine Details verfügbar"
                else:
                    error_detail = "Keine Details verfügbar"
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
                if response.content:
                    try:
                        error_detail = response.json()
                    except json.JSONDecodeError:
                        error_detail = response.text or "Keine Details verfügbar"
                else:
                    error_detail = "Keine Details verfügbar"
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
            response = self._make_request('GET', api_url, headers=headers)
            
            if response.status_code == 200:
                if response.content:
                    try:
                        model_info = response.json()
                    except json.JSONDecodeError:
                        print(f"❌ Fehler: Response ist nicht im JSON-Format")
                        return {
                            "success": False,
                            "error": "Response ist nicht im JSON-Format"
                        }
                else:
                    print(f"❌ Fehler: Leere Response erhalten")
                    return {
                        "success": False,
                        "error": "Leere Response erhalten"
                    }
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
            response = self._make_request('GET', api_url, headers=headers)
            
            if response.status_code == 200:
                if response.content:
                    try:
                        models = response.json()
                    except json.JSONDecodeError:
                        print(f"❌ Fehler: Response ist nicht im JSON-Format")
                        return {
                            "success": False,
                            "error": "Response ist nicht im JSON-Format"
                        }
                else:
                    print(f"❌ Fehler: Leere Response erhalten")
                    return {
                        "success": False,
                        "error": "Leere Response erhalten"
                    }
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
    
    def _check_sas_token_compatibility(self, parsed_url, sas_params):
        """Prüft SAS Token-Container-Kompatibilität"""
        container_name = parsed_url.path.lstrip('/')
        
        print(f"\n🔍 SAS TOKEN-KOMPATIBILITÄT:")
        print(f"   📦 Ziel-Container: {container_name}")
        
        # Prüfe ob SAS Token für Root-Container generiert wurde
        if container_name != '$root':
            print(f"   ⚠️  WARNUNG: SAS Token könnte für '$root' Container generiert worden sein!")
            print(f"   📝 Der Fehler 'Signature did not match' deutet auf Container-Mismatch hin")
            print(f"   🔧 LÖSUNGEN:")
            print(f"      1. Generiere neues SAS Token für Container '{container_name}'")
            print(f"      2. Oder verschiebe Dokumente in '$root' Container")
            print(f"      3. Oder ändere Container-URL auf '$root'")
            
            # Zeige erwartete vs. tatsächliche Signatur
            print(f"\n   🔍 SIGNATUR-ANALYSE:")
            print(f"      Erwartet: /blob/sessionnetblob/{container_name}")
            print(f"      Tatsächlich: /blob/sessionnetblob/$root")
            print(f"      → SAS Token wurde für falschen Container generiert!")
        else:
            print(f"   ✅ SAS Token ist für Root-Container generiert")
    
    def _show_container_documents(self, container_url):
        """Zeigt verfügbare Dokumente im Container"""
        try:
            from urllib.parse import urlparse, parse_qs
            
            # Parse Container URL
            parsed_url = urlparse(container_url)
            account_name = parsed_url.netloc.split('.')[0]
            container_name = parsed_url.path.lstrip('/')
            sas_token = parsed_url.query
            
            # Erstelle URL für Blob-Listing
            list_url = f"https://{account_name}.blob.core.windows.net/{container_name}"
            params = {
                'resttype': 'container',
                'comp': 'list'
            }
            
            # Füge SAS Token hinzu
            sas_params = parse_qs(sas_token)
            for key, value in sas_params.items():
                params[key] = value[0]
            
            # Request an Blob Service
            response = self._make_request('GET', list_url, headers=headers, params=params)
            
            if response.status_code == 200:
                # Parse XML Response (vereinfacht)
                import re
                blob_pattern = r'<Name>(.*?)</Name>'
                matches = re.findall(blob_pattern, response.text)
                
                pdf_files = [name for name in matches if name.lower().endswith('.pdf')]
                json_files = [name for name in matches if name.lower().endswith('.json')]
                
                print(f"\n📄 VERFÜGBARE DOKUMENTE IM CONTAINER:")
                print(f"   📄 PDF-Dateien ({len(pdf_files)}):")
                for pdf in pdf_files[:5]:  # Zeige max 5 PDFs
                    print(f"      📄 {pdf}")
                if len(pdf_files) > 5:
                    print(f"      ... und {len(pdf_files) - 5} weitere PDF-Dateien")
                
                if json_files:
                    print(f"   📋 JSON-Dateien ({len(json_files)}):")
                    for json_file in json_files[:3]:  # Zeige max 3 JSONs
                        print(f"      📋 {json_file}")
                    if len(json_files) > 3:
                        print(f"      ... und {len(json_files) - 3} weitere JSON-Dateien")
                
                if not pdf_files:
                    print("   ⚠️  KEINE PDF-DATEIEN GEFUNDEN!")
                    print("   📝 Document Intelligence benötigt PDF-Dateien für Training")
                
            else:
                print(f"⚠️  Konnte Container-Inhalte nicht abrufen (Status: {response.status_code})")
                
        except Exception as e:
            print(f"⚠️  Fehler beim Abrufen der Container-Inhalte: {e}")
    
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
                print("\n⚡ Schnell-Training mit Trainingsdaten-Upload:")
                
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
                
                # Trainingsdaten direkt in Container-Root hochladen (ohne Unterordner)
                training_folder = r"D:\ki\session_net\pohlheim_protokolle\Stavo"
                
                print(f"\n📤 Lade Trainingsdaten direkt in Container-Root hoch...")
                upload_success = trainer.upload_training_data_to_blob(training_folder, "")
                
                if not upload_success:
                    print("❌ Fehler beim Hochladen der Trainingsdaten!")
                    continue
                
                # Container URL für Training (OHNE Unterordner-Pfad)
                # Azure Document Intelligence benötigt nur die Container-URL mit SAS Token
                corrected_container_url = trainer._fix_container_url_for_sas_token()
                
                print(f"✅ Verwende Container-URL: {corrected_container_url}")
                print(f"📂 Trainingsdaten wurden direkt in Container-Root hochgeladen")
                
                result = trainer.train_custom_model(
                    model_id=model_id,
                    container_url=corrected_container_url,
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
    
    finally:
        # Zeige Debug-Datei-Info am Ende
        if 'trainer' in locals():
            print(f"\n🔍 DEBUG-INFORMATION:")
            print(f"   📄 Debug-Log gespeichert in: {trainer.debug_log_file}")
            print(f"   📊 Alle Requests/Responses wurden protokolliert")
            print(f"   🔧 Überprüfen Sie die Log-Datei für detaillierte Informationen")


if __name__ == "__main__":
    main()