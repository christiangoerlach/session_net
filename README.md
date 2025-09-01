# Session Net - Website Downloader für Sitzungsdienste

Ein Node.js-basiertes Tool zum automatischen Herunterladen von Dokumenten und Tagesordnungspunkten von Sitzungsdienst-Websites.

## 🚀 Features

- **Automatische Dokumentenerkennung:** Findet und lädt alle verfügbaren Dokumente herunter
- **TOP-Erkennung:** Erkennt Tagesordnungspunkte und lädt zugehörige Dokumente herunter
- **Robuste Authentifizierung:** Verwendet Session-Cookies für sichere Downloads
- **Strukturierte Speicherung:** Organisiert Downloads in einer klaren Ordnerstruktur
- **Fortschrittsverfolgung:** Speichert den Fortschritt und überspringt bereits heruntergeladene Inhalte
- **Detailliertes Logging:** Umfassende Protokollierung aller Aktionen

## 📋 Voraussetzungen

- **Node.js** (Version 16 oder höher)
- **npm** oder **yarn**
- **Playwright** (wird automatisch installiert)

## 🛠️ Installation

1. **Repository klonen:**
```bash
git clone https://github.com/[dein-username]/session_net.git
cd session_net
```

2. **Abhängigkeiten installieren:**
```bash
npm install
```

3. **Playwright Browser installieren:**
```bash
npx playwright install
```

## ⚙️ Konfiguration

1. **Umgebungsvariablen erstellen:**
```bash
cp config.env.example config.env
```

2. **config.env bearbeiten:**
```env
# Website-Konfiguration
WEBSITE_URL=https://sitzungsdienst.pohlheim.de
USERNAME=dein_username
PASSWORD=dein_password

# Download-Konfiguration
DOWNLOAD_DIR=./downloads
LOG_LEVEL=info
```

## 🚀 Verwendung

### Grundlegende Verwendung

```bash
# Alle Termine für einen Monat herunterladen
npm run download

# Entwicklungsserver starten
npm run dev

# Mit Debug-Informationen
npm run dev -- --inspect
```

### Erweiterte Optionen

```bash
# Spezifischen Monat herunterladen
node src/main.js --month=2025_August

# Nur bestimmte Termine
node src/main.js --filter="Stadtverordnetenversammlung"

# Debug-Modus
node src/main.js --debug
```

## 📁 Projektstruktur

```
session_net/
├── src/
│   ├── main.js                 # Hauptanwendung
│   ├── termin-extractor.js     # Termin-Extraktion
│   ├── termin-processor.js     # Termin-Verarbeitung
│   ├── document-downloader.js  # Dokument-Downloader
│   └── modules/
│       ├── playwright-downloader.js
│       ├── file-manager.js
│       └── logger.js
├── downloads/                  # Heruntergeladene Dateien
├── logs/                      # Log-Dateien
├── package.json
├── .gitignore
└── README.md
```

## 🔧 Technische Details

### Verwendete Technologien

- **Node.js** - JavaScript-Runtime
- **Playwright** - Browser-Automatisierung
- **node-fetch** - HTTP-Requests
- **fs/path** - Dateisystem-Operationen

### Architektur

- **Modulare Struktur:** Klare Trennung der Verantwortlichkeiten
- **Asynchrone Verarbeitung:** Effiziente Parallelverarbeitung
- **Fehlerbehandlung:** Robuste Fehlerbehandlung und Wiederherstellung
- **Memory Management:** Optimierte Speichernutzung mit Garbage Collection

## 📊 Logging

Das Tool erstellt detaillierte Logs für:

- **Download-Fortschritt:** Status aller Downloads
- **Fehlerprotokollierung:** Detaillierte Fehlerinformationen
- **Performance-Metriken:** Download-Zeiten und Dateigrößen
- **Memory-Usage:** Speichernutzung und Garbage Collection

## 🔒 Sicherheit

- **Keine hartcodierten Anmeldedaten:** Verwendung von Umgebungsvariablen
- **Session-Management:** Sichere Cookie-Verwaltung
- **Request-Interception:** Kontrollierte Netzwerk-Requests
- **Datei-Sanitization:** Sichere Dateinamen-Generierung

## 🐛 Fehlerbehebung

### Häufige Probleme

1. **"Target page, context or browser has been closed"**
   - Lösung: Browser-Instabilität wurde durch direkte fetch-Downloads behoben

2. **"response.body.pipe is not a function"**
   - Lösung: node-fetch v3 Kompatibilität implementiert

3. **Leere PDF-Dateien**
   - Lösung: Cookie-Authentifizierung für Downloads hinzugefügt

### Debug-Modus

```bash
npm run dev -- --debug
```

## 🤝 Beitragen

1. **Fork** das Repository
2. **Feature-Branch** erstellen (`git checkout -b feature/AmazingFeature`)
3. **Commit** deine Änderungen (`git commit -m 'Add some AmazingFeature'`)
4. **Push** zum Branch (`git push origin feature/AmazingFeature`)
5. **Pull Request** erstellen

## 📝 Changelog

### Version 1.0.0
- ✅ Vollständige Dokumentenerkennung implementiert
- ✅ TOP-Link-Erkennung für to0050.asp und vo0050.asp
- ✅ Direkte fetch-Downloads mit Cookie-Authentifizierung
- ✅ Robuste Fehlerbehandlung und Wiederherstellung
- ✅ Strukturierte Ordnerorganisation
- ✅ Detailliertes Logging und Fortschrittsverfolgung

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](LICENSE) für Details.

## 👥 Autoren

- **Dein Name** - *Initiale Entwicklung* - [GitHub-Username](https://github.com/username)

## 🙏 Danksagungen

- Playwright-Team für die ausgezeichnete Browser-Automatisierung
- Node.js-Community für die robuste JavaScript-Runtime
- Alle Mitwirkenden und Tester

---

**Hinweis:** Dieses Tool ist für Bildungs- und Forschungszwecke entwickelt. Bitte respektiere die Nutzungsbedingungen der Zielwebsites.
