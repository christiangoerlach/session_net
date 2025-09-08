import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus config.env
load_dotenv('config.env')

class AzureAgentChat:
    def __init__(self):
        """Initialisiere den Azure AI Agent Chat"""
        self.client = AIProjectClient(
            endpoint=os.getenv('AZURE_ENDPOINT'), 
            credential=DefaultAzureCredential()
        )
        self.agent_id = os.getenv('AZURE_AI_AGENT_ID')
        self.thread = None
        self.agent = None
        
    def initialize(self):
        """Initialisiere Agent und Thread"""
        try:
            # Hole den Agenten
            self.agent = self.client.agents.get_agent(self.agent_id)
            print(f"✅ Agent gefunden: {self.agent.name}")
            
            # Starte einen neuen Thread
            self.thread = self.client.agents.threads.create()
            print(f"✅ Thread erstellt: {self.thread.id}")
            return True
            
        except Exception as e:
            print(f"❌ Fehler bei der Initialisierung: {e}")
            return False
    
    def extract_text_content(self, content):
        """Extrahiere Text aus verschiedenen Content-Formaten"""
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    if 'text' in item and isinstance(item['text'], dict):
                        return item['text'].get('value', str(content))
                    elif 'value' in item:
                        return item['value']
            return str(content)
        elif isinstance(content, dict):
            if 'text' in content and isinstance(content['text'], dict):
                return content['text'].get('value', str(content))
            elif 'value' in content:
                return content['value']
            else:
                return str(content)
        else:
            return str(content)
    
    def send_message(self, message):
        """Sende eine Nachricht an den Agenten"""
        try:
            # Sende die Nachricht
            msg = self.client.agents.messages.create(
                thread_id=self.thread.id, 
                role="user", 
                content=message
            )
            
            # Starte den Run
            run = self.client.agents.runs.create(
                thread_id=self.thread.id, 
                agent_id=self.agent_id
            )
            
            # Warte auf die Antwort
            while run.status not in ["completed", "failed", "cancelled"]:
                run = self.client.agents.runs.get(thread_id=self.thread.id, run_id=run.id)
                if run.status == "completed":
                    break
            
            if run.status == "completed":
                # Hole alle Nachrichten
                messages = self.client.agents.messages.list(thread_id=self.thread.id)
                message_list = list(messages)
                
                # Debug: Zeige alle Nachrichten (nur bei Bedarf)
                # print(f"DEBUG: {len(message_list)} Nachrichten gefunden")
                # for i, msg in enumerate(message_list):
                #     print(f"  {i}: {msg.role} - {type(msg.content)} - {msg.content}")
                
                # Finde die neueste Agent-Antwort (die erste in der Liste ist die neueste)
                for msg in message_list:
                    if msg.role == "assistant":
                        # Direkte Extraktion aus dem Content
                        content = msg.content
                        if isinstance(content, list) and len(content) > 0:
                            item = content[0]
                            # Das Item ist ein MessageTextContent Objekt
                            if hasattr(item, 'text') and hasattr(item.text, 'value'):
                                return item.text.value
                            # Fallback für Dictionary-Zugriff
                            elif isinstance(item, dict) and 'text' in item:
                                text_dict = item['text']
                                if isinstance(text_dict, dict) and 'value' in text_dict:
                                    return text_dict['value']
                        return str(content)
                
                return "Keine Agent-Antwort gefunden."
            else:
                return f"❌ Run fehlgeschlagen mit Status: {run.status}"
                
        except Exception as e:
            return f"❌ Fehler beim Senden der Nachricht: {e}"
    
    def chat_loop(self):
        """Hauptschleife für den Chat"""
        print("\n" + "="*60)
        print("🤖 Session Net Pohlheim AI Agent Chat")
        print("="*60)
        print("Testversion: 2025-09-06 12:48")
        print("'quit', 'exit' oder 'beenden' um den Chat zu verlassen.")
        print("'clear' um den Thread zu löschen und neu zu starten.")
        print("-"*60)
        
        while True:
            try:
                # Eingabe vom Benutzer
                user_input = input("\n👤 Sie: ").strip()
                
                # Beenden-Befehle
                if user_input.lower() in ['quit', 'exit', 'beenden', 'q']:
                    print("👋 Auf Wiedersehen!")
                    break
                
                # Thread löschen
                if user_input.lower() in ['clear', 'neu', 'reset']:
                    self.thread = self.client.agents.threads.create()
                    print("✅ Neuer Thread erstellt!")
                    continue
                
                # Leere Eingabe ignorieren
                if not user_input:
                    continue
                
                # Nachricht an Agent senden
                # print("⏳ Agent denkt nach...")
                response = self.send_message(user_input)
                
                # Antwort anzeigen
                print(f"🤖 Agent: {response}")
                
            except KeyboardInterrupt:
                print("\n👋 Chat beendet!")
                break
            except Exception as e:
                print(f"❌ Unerwarteter Fehler: {e}")

def main():
    """Hauptfunktion"""
    chat = AzureAgentChat()
    
    if chat.initialize():
        chat.chat_loop()
    else:
        print("❌ Chat konnte nicht initialisiert werden.")

if __name__ == "__main__":
    main()