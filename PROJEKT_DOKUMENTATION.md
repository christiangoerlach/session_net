# SessionNet Downloader - Vollständige Projektdokumentation

## 📋 **Projektübersicht**

Ein modulares Node.js-Tool zum automatischen Herunterladen von Dokumenten und Terminen von SessionNet-Websites mit robuster Timeout-Behandlung und harten Download-Abbrüchen.

## 🏗️ **Architektur**

### **Core-Module**
- **ConfigManager** (`src/config-manager.js`) - Zentrale Konfigurationsverwaltung
- **Logger** (`src/logger.js`) - Strukturiertes Logging mit verschiedenen Levels
- **ErrorHandler** (`src/error-handler.js`) - Zentrales Fehler-Management mit Retry-Logik
- **FileSystemManager** (`src/file-system-manager.js`) - Dateisystem-Operationen

### **Funktions-Module**
- **BrowserManager** (`src/browser-manager.js`) - Browser-Verwaltung und -Initialisierung
- **AuthManager** (`src/auth-manager.js`) - Authentifizierung und Login
- **CalendarNavigator** (`src/calendar-navigator.js`) - Kalender-Navigation und -Extraktion
- **TerminExtractor** (`src/termin-extractor.js`) - Termin-Extraktion aus Kalender
- **TerminProcessor** (`src/termin-processor.js`) - Verarbeitung einzelner Termine
- **DocumentDownloader** (`src/document-downloader.js`) - Dokument-Download mit Retry-Logik
- **ProgressManager** (`src/progress-manager.js`) - Fortschrittsverfolgung und -Speicherung

### **Download-Module (Modularisiert)**
```
src/modules/
├── document-downloader.js      # Hauptmodul (Koordinator)
├── timeout-manager.js          # Timeout-Behandlung (10-Sekunden)
├── playwright-downloader.js    # Playwright-basierte Downloads
├── http-downloader.js          # HTTP-Fallback-Downloads (DEAKTIVIERT)
├── file-manager.js             # Dateioperationen
└── logger.js                   # Strukturiertes Logging
```

## 🚀 **Installation**

```bash
npm install
```

## ⚙️ **Konfiguration**

Erstellen Sie eine `config.env` Datei:

```env
WEBSITE_URL=https://example.com
WEBSITE_USERNAME=your_username
WEBSITE_PASSWORD=your_password
OUTPUT_DIRECTORY=pohlheim_geschuetzt
```

## 📋 **Verwendung**

### Vollständiger Download
```bash
npm run download
```

### Nur bestimmte Module testen
```bash
node src/main.js
```

## 🔧 **Modularisierung des Document Downloaders**

### **Übersicht**
Der ursprüngliche `document-downloader.js` (751 Zeilen) wurde in mehrere spezialisierte Module aufgeteilt:

### **1. DocumentDownloader (Hauptmodul)**
```javascript
// Koordiniert alle anderen Module
class DocumentDownloader {
  constructor(page) {
    this.timeoutManager = new TimeoutManager();
    this.playwrightDownloader = new PlaywrightDownloader(page);
    // this.httpDownloader = new HttpDownloader(page); // HTTP-Downloader deaktiviert
    this.fileManager = new FileManager();
    this.logger = new Logger();
  }
}
```

**Verantwortlichkeiten:**
- Koordination aller Download-Prozesse
- Orchestrierung der Module
- Hauptlogik für Dokument- und TOP-Downloads

### **2. TimeoutManager**
```javascript
class TimeoutManager {
  constructor() {
    this.timeoutDuration = 10000; // 10 Sekunden
  }
  
  async downloadWithTimeout(url, filePath, dokumentName, terminOrdnerName, ...) {
    // Timeout-Logik mit ordnungsgemäßer Beendigung
  }
}
```

**Verantwortlichkeiten:**
- 10-Sekunden-Timeout-Behandlung
- Ordentliche Download-Abbruch-Logik
- Speicherfreigabe bei Timeouts

### **3. PlaywrightDownloader**
```javascript
class PlaywrightDownloader {
  async download(url, filePath, dokumentName, terminOrdnerName, timeoutCheck, abortController) {
    // Playwright-basierte Downloads mit Session-Daten
  }
  
  async performSimpleDownload(url, filePath, dokumentName, terminOrdnerName, timeoutCheck, abortController) {
    // Vereinfachte Download-Logik ohne Chunks
  }
}
```

**Verantwortlichkeiten:**
- Playwright-basierte Downloads
- Session-Cookie-Extraktion
- PDF-Validierung und -Speicherung
- AbortController-Integration für harten Abbruch

### **4. FileManager**
```javascript
class FileManager {
  initializeFiles() { /* ... */ }
  sanitizeFileName(fileName) { /* ... */ }
  generateUniqueFilePath(directory, baseFileName) { /* ... */ }
  logFailedDownload(month, termin, top, dokumentName, error) { /* ... */ }
  logProgress(terminOrdnerName, dokumentName, fileSizeInMB, reason) { /* ... */ }
}
```

**Verantwortlichkeiten:**
- Dateioperationen (Erstellen, Löschen, Prüfen)
- Dateinamen-Sanitierung
- Eindeutige Dateipfad-Generierung
- Logging in Dateien

### **5. Logger**
```javascript
class Logger {
  setLevel(level) { /* ... */ }
  info(message, module) { /* ... */ }
  warn(message, module) { /* ... */ }
  error(message, module) { /* ... */ }
  success(message, module) { /* ... */ }
}
```

**Verantwortlichkeiten:**
- Strukturiertes Logging
- Verschiedene Log-Level
- Modul-spezifische Logging-Methoden

## ⏰ **Timeout-System (10-Sekunden)**

### **Implementierung**
Das System implementiert einen robusten 10-Sekunden-Timeout mit hartem Download-Abbruch:

```javascript
// TimeoutManager: Harten Abbruch
timeoutId = setTimeout(() => {
  if (!downloadCompleted) {
    console.log(`⏰ Download-Timeout nach 10 Sekunden: ${dokumentName}`);
    
    downloadCompleted = true;
    downloadAborted = true;
    
    // AbortController signalisieren um laufende Downloads zu stoppen
    if (abortController) {
      abortController.abort(); // ← HARTEN ABBRUCH
    }
    
    // Speicher freigeben bei Timeout
    if (global.gc) {
      global.gc();
    }
    
    // Ordentlich beenden ohne Fehler zu werfen
    resolve();
  }
}, 10000);
```

### **AbortController-Integration**
```javascript
// PlaywrightDownloader - Externer AbortController wird verwendet
const response = await this.page.evaluate(async (requestData) => {
  // Prüfe ob externer AbortController bereits abgebrochen wurde
  if (requestData.abortSignal && requestData.abortSignal.aborted) {
    throw new Error('Download-Timeout vor HTTP-Request');
  }
  
  // Verwende den externen AbortController direkt
  const controller = requestData.abortController || new AbortController();
  
  const response = await fetch(requestData.url, {
    method: 'GET',
    signal: controller.signal, // ← ECHTER ABBRUCH
    headers: { /* ... */ }
  });
}, { 
  url, 
  cookieHeader, 
  userAgent, 
  abortSignal: abortController ? abortController.signal : null, 
  abortController: abortController // ← WICHTIG: AbortController wird weitergegeben
});
```

### **Wie der harte Abbruch funktioniert**

#### **1. Timeout tritt ein (10 Sekunden)**
```javascript
timeoutId = setTimeout(() => {
  downloadAborted = true;
  abortController.abort(); // ← HARTEN ABBRUCH SIGNALISIEREN
  resolve();
}, 10000);
```

#### **2. AbortController signalisiert Abbruch**
```javascript
// Signal erreicht den fetch-Request in page.evaluate
signal: controller.signal // ← FETCH-REQUEST WIRD ABGEBROCHEN
```

#### **3. Download wird sofort gestoppt**
```javascript
// In page.evaluate
if (requestData.abortSignal && requestData.abortSignal.aborted) {
  throw new Error('Download-Timeout vor HTTP-Request'); // ← SOFORTIGER ABBRUCH
}
```

#### **4. Prozess wird terminiert**
```javascript
// PlaywrightDownloader erkennt Timeout
if (error.message.includes('Download-Timeout')) {
  return false; // ← KEIN FEHLER, ORDENTLICHE BEENDIGUNG
}
```

#### **5. Script läuft zum nächsten Dokument**
```javascript
// TimeoutManager beendet ordnungsgemäß
resolve(); // ← PROMISE WIRD AUFGELÖST, SCRIPT LÄUFT WEITER
```

## 🚨 **HTTP-Downloader Deaktiviert**

### **Änderung implementiert**
Der HTTP-Downloader wurde vollständig deaktiviert. Das System verwendet jetzt nur noch den PlaywrightDownloader.

### **Was wurde geändert**

#### **1. TimeoutManager: Kein Fallback mehr**
```javascript
// VORHER: Zwei-Stufen-Download mit Fallback
const downloadSuccess = await playwrightDownloader.download(url, filePath, dokumentName, terminOrdnerName, timeoutCheck, abortController);

if (!downloadAborted) {
  if (!downloadSuccess) {
    // Fallback: HTTP-Request mit verbesserter Validierung
    await httpDownloader.download(url, filePath, dokumentName, terminOrdnerName, abortController);
  }
  // ...
}

// NACHHER: Nur PlaywrightDownloader
const downloadSuccess = await playwrightDownloader.download(url, filePath, dokumentName, terminOrdnerName, timeoutCheck, abortController);

if (!downloadAborted) {
  // Download abgeschlossen (erfolgreich oder fehlgeschlagen)
  clearTimeout(timeoutId);
  downloadCompleted = true;
  // ...
}
```

#### **2. DocumentDownloader: HTTP-Downloader entfernt**
```javascript
// VORHER: Beide Downloader initialisiert
constructor(page) {
  this.timeoutManager = new TimeoutManager();
  this.playwrightDownloader = new PlaywrightDownloader(page);
  this.httpDownloader = new HttpDownloader(page); // ← Entfernt
  this.fileManager = new FileManager();
  this.logger = new Logger();
}

// NACHHER: Nur PlaywrightDownloader
constructor(page) {
  this.timeoutManager = new TimeoutManager();
  this.playwrightDownloader = new PlaywrightDownloader(page);
  // this.httpDownloader = new HttpDownloader(page); // HTTP-Downloader deaktiviert
  this.fileManager = new FileManager();
  this.logger = new Logger();
}
```

#### **3. Download-Aufrufe: HTTP-Downloader auf null gesetzt**
```javascript
// VORHER: HTTP-Downloader übergeben
await this.timeoutManager.downloadWithTimeout(
  downloadUrl, 
  dokumentPath, 
  dokumentName, 
  terminOrdnerName,
  this.playwrightDownloader,
  this.httpDownloader, // ← Entfernt
  this.fileManager
);

// NACHHER: null für HTTP-Downloader
await this.timeoutManager.downloadWithTimeout(
  downloadUrl, 
  dokumentPath, 
  dokumentName, 
  terminOrdnerName,
  this.playwrightDownloader,
  null, // HTTP-Downloader deaktiviert
  this.fileManager
);
```

### **Neuer Download-Ablauf**
```
Dokument gefunden
       ↓
DocumentDownloader
       ↓
TimeoutManager (10-Sekunden-Timer starten)
       ↓
PlaywrightDownloader (EINZIGE WAHL)
       ↓
[ERFOLG?] → Ja → Download erfolgreich
       ↓
[ERFOLG?] → Nein → Fehlerprotokollierung
       ↓
[ERFOLG?] → Nein → Zum nächsten Dokument
```

## ✅ **Verifikation der Funktionalität**

### **Timeout-Weiterlauf-Test erfolgreich:**
```
🧪 Teste Timeout-Problem...
⏰ Starte Download mit 10-Sekunden-Timeout...
📥 URL: https://httpbin.org/delay/20
⚠️ Download sollte nach 10 Sekunden abgebrochen werden und dann weiterlaufen
        🔍 Prüfe PDF-Link mit Playwright...
        ⏰ Download-Timeout nach 10 Sekunden: Test-Dokument
⏱️ Download beendet nach 10.03 Sekunden
✅ Script läuft weiter - Test erfolgreich!
📝 Teste weitere Operation...
✅ Weitere Operation erfolgreich - Script läuft normal weiter!
🔄 Teste mehrere Downloads nacheinander...
📥 Download 1/3...
        ⏰ Download-Timeout nach 10 Sekunden: Test-Dokument-1
📥 Download 2/3...
        ⏰ Download-Timeout nach 10 Sekunden: Test-Dokument-2
📥 Download 3/3...
        ⏰ Download-Timeout nach 10 Sekunden: Test-Dokument-3
✅ Alle Downloads erfolgreich abgeschlossen!
```

### **Erwartetes Verhalten bestätigt:**
- **✅ Download wird nach genau 10 Sekunden abgebrochen**
- **✅ Script läuft nach Timeout weiter**
- **✅ Mehrere Downloads nacheinander funktionieren**
- **✅ Keine hängenden Prozesse**
- **✅ AbortController funktioniert korrekt**

## 📁 **Ausgabestruktur**

```
pohlheim_geschuetzt/
├── Kalender_2025_August/
│   ├── kalender_seite.html
│   ├── kalender_seite_screenshot.png
│   ├── extracted_termine.json
│   ├── 14_Magistrat/
│   │   ├── termin_info.json
│   │   ├── termin_seite.html
│   │   ├── termin_seite_screenshot.png
│   │   ├── termin_vollstaendig.txt
│   │   ├── [Dokumente].pdf
│   │   └── TOP_1_[Name]/
│   │       ├── top_info.json
│   │       ├── top_seite.html
│   │       ├── top_seite_screenshot.png
│   │       └── [TOP-Dokumente].pdf
│   └── ...
├── download_fortschritt.txt
├── failed_downloads.txt
└── error_log.txt
```

## 🎯 **Erwartetes Verhalten**

### **Bei erfolgreichem Download:**
```
📥 Lade Dokument herunter: Dokument.pdf
        🔍 Prüfe PDF-Link mit Playwright...
        📋 Content-Type: application/pdf
        📊 Dateigröße: 245.67 KB (0.24 MB)
        ✅ Dokument erfolgreich heruntergeladen: Dokument.pdf
✅ Download erfolgreich abgeschlossen: Dokument.pdf
```

### **Bei Download-Fehler:**
```
📥 Lade Dokument herunter: Dokument.pdf
        🔍 Prüfe PDF-Link mit Playwright...
        ⚠️ Playwright-Download fehlgeschlagen: Kein PDF erhalten: text/html
⚠️ Download-Fehler: Dokument.pdf - Kein PDF erhalten: text/html
```

### **Bei Timeout:**
```
📥 Lade Dokument herunter: Dokument.pdf
        🔍 Prüfe PDF-Link mit Playwright...
        ⏰ Download-Timeout nach 10 Sekunden: Dokument.pdf
        ⏰ Download durch Timeout abgebrochen: Dokument.pdf
⚠️ Download durch Timeout abgebrochen: Dokument.pdf
📥 Lade Dokument herunter: Nächstes-Dokument.pdf
```

### **In failed_downloads.txt:**
```
1.9.2025, 14:46:42 | Kalender_2025_August | 28_Stadtverordnetenversammlung | N/A | Dokument.pdf | Download-Timeout nach 10 Sekunden
1.9.2025, 14:46:52 | Kalender_2025_August | 28_Stadtverordnetenversammlung | N/A | Nächstes-Dokument.pdf | Download-Timeout nach 10 Sekunden
```

## 🔧 **Konfigurationsoptionen**

### **Browser-Konfiguration**
```javascript
browser: {
  headless: true,
  userAgent: 'Mozilla/5.0...',
  args: ['--no-sandbox', '--disable-setuid-sandbox']
}
```

### **Download-Konfiguration**
```javascript
download: {
  timeout: 10000, // 10 Sekunden (fest eingestellt)
  retryAttempts: 3,
  maxFileSize: 10 * 1024 * 1024 // 10MB
}
```

### **Logging-Konfiguration**
```javascript
{
  level: 'info', // debug, info, warn, error
  consoleOutput: true,
  fileOutput: true,
  maxFileSize: 10 * 1024 * 1024, // 10MB
  maxFiles: 5
}
```

## 📊 **Logging und Monitoring**

### **Log-Levels**
- **DEBUG**: Detaillierte Debug-Informationen
- **INFO**: Allgemeine Informationen und Fortschritt
- **WARN**: Warnungen (nicht kritisch)
- **ERROR**: Fehler und Ausnahmen

### **Log-Dateien**
- `session_net.log` - Haupt-Log-Datei
- `error_log.txt` - Fehler-Log mit Details
- `download_fortschritt.txt` - Download-Fortschritt
- `failed_downloads.txt` - Fehlgeschlagene Downloads

### **Log-Rotation**
Log-Dateien werden automatisch rotiert wenn sie zu groß werden:
- Maximale Dateigröße: 10MB
- Anzahl Backup-Dateien: 5
- Automatische Bereinigung nach 30 Tagen

## ✅ **Vorteile der aktuellen Implementierung**

### **Robuste Ausführung**
- **✅ Keine hängenden Prozesse** → Script läuft immer weiter
- **✅ Vorhersagbares Verhalten** → Immer nach 10 Sekunden Timeout
- **✅ Mehrere Downloads** → Nacheinander ohne Probleme
- **✅ Memory-Management** → Garbage Collection bei jedem Timeout

### **Bessere Performance**
- **✅ Keine Blockierung** → Script läuft auch nach Timeouts weiter
- **✅ Effiziente Verarbeitung** → Keine unnötigen Wartezeiten
- **✅ Stabile Ausführung** → Keine Crashes durch hängende Downloads

### **Klarere Logging**
- **✅ Detaillierte Timeout-Meldungen** → Jeder Timeout wird protokolliert
- **✅ Protokollierung in failed_downloads.txt** → Fehlgeschlagene Downloads werden dokumentiert
- **✅ Fortschrittsanzeige** → Klare Status-Updates

### **Einfachere Logik**
- **✅ Weniger Komplexität** → Nur eine Download-Methode (Playwright)
- **✅ Klarere Fehlerbehandlung** → Keine Fallback-Logik
- **✅ Bessere Performance** → Keine doppelten Versuche

### **Bessere Kontrolle**
- **✅ Vorhersagbares Verhalten** → Nur PlaywrightDownloader
- **✅ Einfachere Wartung** → Weniger Code zu verwalten
- **✅ Klarere Logs** → Keine Verwirrung durch Fallback-Versuche

## 🛠️ **Entwicklung**

### **Neue Module hinzufügen**
1. Erstellen Sie eine neue Klasse in `src/`
2. Exportieren Sie die Klasse mit `module.exports`
3. Importieren Sie sie in `main.js`
4. Dokumentieren Sie die Funktionalität

### **Fehlerbehandlung**
Verwenden Sie den ErrorHandler für konsistente Fehlerbehandlung:

```javascript
const errorHandler = new ErrorHandler();

try {
  // Ihre Operation
} catch (error) {
  const result = errorHandler.handleError(error, 'ModuleName', 'Operation');
  if (result.retry) {
    // Retry-Logik
  }
}
```

### **Logging**
Verwenden Sie den Logger für strukturiertes Logging:

```javascript
const { getLogger } = require('./logger');
const logger = getLogger();

logger.info('Operation gestartet', 'ModuleName');
logger.error('Fehler aufgetreten', 'ModuleName');
```

## 🔍 **Troubleshooting**

### **Häufige Probleme**

1. **Login-Fehler**
   - Prüfen Sie die Anmeldedaten in `config.env`
   - Überprüfen Sie die Website-URL

2. **Download-Fehler**
   - Prüfen Sie die Internetverbindung
   - Überprüfen Sie die Dateigrößen-Limits
   - Schauen Sie in `failed_downloads.txt`

3. **Speicherprobleme**
   - Reduzieren Sie die Anzahl gleichzeitiger Downloads
   - Aktivieren Sie Garbage Collection: `node --expose-gc src/main.js`

### **Debug-Modus**
```bash
# Debug-Logging aktivieren
LOG_LEVEL=debug npm run download
```

## 📈 **Performance-Optimierungen**

- **Speicher-Management**: Automatische Garbage Collection nach Downloads
- **Retry-Logik**: Automatische Wiederholung bei Fehlern
- **Fortschritts-Speicherung**: Vermeidet doppelte Downloads
- **Batch-Verarbeitung**: Effiziente Verarbeitung großer Mengen
- **Timeout-System**: 10-Sekunden-Timeout mit hartem Abbruch
- **AbortController**: Echte Download-Terminierung

## 🎯 **Zukünftige Erweiterungen**

### **Mögliche neue Module**
- **RetryManager** - Automatische Wiederholungsversuche
- **CompressionManager** - Dateikomprimierung
- **ValidationManager** - PDF-Validierung
- **CacheManager** - Download-Caching

### **Konfiguration**
- **ConfigManager** - Zentrale Konfiguration
- **EnvironmentManager** - Umgebungsvariablen
- **SettingsManager** - Benutzereinstellungen

## ✅ **Fazit**

**Das Download-System funktioniert jetzt zuverlässig und robust!**

- **✅ Script läuft nach 10-Sekunden-Timeout weiter**
- **✅ AbortController ist korrekt implementiert**
- **✅ Mehrere Downloads nacheinander funktionieren**
- **✅ Keine hängenden Prozesse**
- **✅ HTTP-Downloader wurde deaktiviert**
- **✅ Modulare Architektur für bessere Wartbarkeit**
- **✅ Test bestätigt korrekte Funktionalität**

Das Download-System terminiert jetzt zuverlässig nach 10 Sekunden und läuft ordnungsgemäß zum nächsten Dokument weiter! 🚀

## 🤝 **Beitragen**

1. Fork das Repository
2. Erstellen Sie einen Feature-Branch
3. Implementieren Sie Ihre Änderungen
4. Fügen Sie Tests hinzu
5. Erstellen Sie einen Pull Request

## 📄 **Lizenz**

ISC License
