import os
from openai import AzureOpenAI
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus config.env
load_dotenv('config.env')

class AzureOpenAIChat:
    def __init__(self):
        """Initialisiere den Azure OpenAI Chat"""
        # Erstelle Azure OpenAI Client
        self.client = AzureOpenAI(
            api_key=os.getenv('AZURE_API_KEY'),
            api_version=os.getenv('AZURE_API_VERSION', '2023-07-01-preview'),
            azure_endpoint=os.getenv('AZURE_ENDPOINT')
        )
        
        self.deployment = os.getenv('AZURE_DEPLOYMENT', 'gpt-35-turbo')
        self.messages = []
        
        # System-Nachricht für den Assistenten
        self.system_message = {
            "role": "system", 
            "content": "Du bist ein hilfreicher Assistent für die Stadt Pohlheim. Du hilfst bei Fragen zu kommunalen Angelegenheiten, Sitzungen und Terminen. Inhaltliche Informationen dürfen nur aus den bereitgestellten Daten kommen, wenn diese icht vorhanden sind, dann antworte, dass du es nicht weisst"
        }
        
        # Initialisiere mit System-Nachricht
        self.messages.append(self.system_message)
    
    def add_message_to_history(self, role, content):
        """Füge eine Nachricht zum Chatverlauf hinzu"""
        self.messages.append({"role": role, "content": content})
    
    def get_conversation_summary(self):
        """Gibt eine Zusammenfassung des aktuellen Gesprächs zurück"""
        user_messages = [msg for msg in self.messages if msg["role"] == "user"]
        assistant_messages = [msg for msg in self.messages if msg["role"] == "assistant"]
        
        return f"Gespräch: {len(user_messages)} Fragen, {len(assistant_messages)} Antworten"
        
    def initialize(self):
        """Initialisiere Azure OpenAI Verbindung"""
        try:
            # Teste die Verbindung mit einer einfachen Anfrage
            test_response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "Du bist ein Test-Assistent."},
                    {"role": "user", "content": "Antworte nur mit 'Verbindung erfolgreich'"}
                ],
                temperature=0.7,
                top_p=0.95,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                max_tokens=10000
            )
            
            print(f"✅ Azure OpenAI Verbindung erfolgreich")
            print(f"✅ Projekt-Instanz: {os.getenv('AZURE_ENDPOINT')}")
            print(f"✅ Deployment: {self.deployment}")
            print(f"✅ API-Version: {os.getenv('AZURE_API_VERSION')}")
            return True
            
        except Exception as e:
            print(f"❌ Fehler bei der Initialisierung: {e}")
            return False
    
    def send_message(self, message):
        """Sende eine Nachricht an Azure OpenAI"""
        try:
            # Füge Benutzer-Nachricht zum Verlauf hinzu
            self.add_message_to_history("user", message)
            
            # Sende Anfrage an Azure OpenAI mit Playground-Parametern
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=self.messages,
                temperature=0.7,
                top_p=0.95,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                max_tokens=15000
            )
            
            # Extrahiere die Antwort
            assistant_message = response.choices[0].message.content
            
            # Füge Assistant-Antwort zum Verlauf hinzu
            self.add_message_to_history("assistant", assistant_message)
            
            return assistant_message
                
        except Exception as e:
            return f"❌ Fehler beim Senden der Nachricht: {e}"
    
    def chat_loop(self):
        """Hauptschleife für den Chat"""
        print("\n" + "="*60)
        print("🤖 Session Net Pohlheim Azure OpenAI Chat")
        print("="*60)
        print("Version: Azure OpenAI Integration")
        print("'quit', 'exit' oder 'beenden' um den Chat zu verlassen.")
        print("'clear' um den Chat-Verlauf zu löschen und neu zu starten.")
        print("'history' um den Chat-Status anzuzeigen.")
        print("-"*60)
        
        while True:
            try:
                # Eingabe vom Benutzer
                user_input = input("\n👤 Sie: ").strip()
                
                # Beenden-Befehle
                if user_input.lower() in ['quit', 'exit', 'beenden', 'q']:
                    print("👋 Auf Wiedersehen!")
                    break
                
                # Chat-Verlauf löschen
                if user_input.lower() in ['clear', 'neu', 'reset']:
                    self.messages = [self.system_message]  # Nur System-Nachricht behalten
                    print("✅ Chat-Verlauf gelöscht!")
                    continue
                
                # Chat-Verlauf anzeigen
                if user_input.lower() in ['history', 'verlauf', 'status']:
                    print(f"📊 {self.get_conversation_summary()}")
                    continue
                
                # Leere Eingabe ignorieren
                if not user_input:
                    continue
                
                # Nachricht an Azure OpenAI senden
                response = self.send_message(user_input)
                
                # Antwort anzeigen
                print(f"🤖 Assistant: {response}")
                
            except KeyboardInterrupt:
                print("\n👋 Chat beendet!")
                break
            except Exception as e:
                print(f"❌ Unerwarteter Fehler: {e}")

def main():
    """Hauptfunktion"""
    chat = AzureOpenAIChat()
    
    if chat.initialize():
        chat.chat_loop()
    else:
        print("❌ Chat konnte nicht initialisiert werden.")

if __name__ == "__main__":
    main()