# Prozess-Monitoring nach Timeout

## Übersicht

Nach der Meldung `"Download durch Timeout abgebrochen: Einladung Vorlagen"` wird jetzt automatisch der Prozess-Status überprüft, um zu sehen, ob der Download-Prozess noch aktiv ist und wie viel Speicher belegt wird.

## Was wird überwacht?

### **1. Prozess-Status (TimeoutManager):**
```javascript
const processStatus = this.checkProcessStatus();
```

**Überwachte Metriken:**
- **PID:** Prozess-ID
- **Uptime:** Laufzeit des Prozesses
- **Memory Usage:** Aktuelle Speicherverwendung
- **CPU Usage:** CPU-Verbrauch
- **Active Handles:** Anzahl aktiver Handles
- **Active Requests:** Anzahl aktiver Requests
- **Event Loop Delay:** Verzögerung im Event Loop
- **Download Process Active:** Status des Download-Prozesses

### **2. Download-Prozess-Status:**
```javascript
downloadProcessActive: {
  activeTimers: 0,        // Aktive Timer
  activePromises: 0,      // Aktive Promises
  activeRequests: 0,      // Aktive HTTP-Requests
  hasActiveProcesses: false
}
```

### **3. Browser-Status (DocumentDownloader):**
```javascript
browserContexts: 1,       // Anzahl Browser-Kontexte
pageCount: 1              // Anzahl offener Seiten
```

## Log-Ausgabe

### **Terminal-Ausgabe:**
```
⏰ Download-Timeout nach 10 Sekunden: Einladung Vorlagen
🔍 TimeoutManager: Prüfe global.gc...
🔍 TimeoutManager: global.gc verfügbar, führe Garbage Collection durch...
🔍 TimeoutManager: Speicher vor GC: {...}
🔍 TimeoutManager: Speicher nach GC: {...}
🔍 TimeoutManager: Prüfe logInfo...
🔍 TimeoutManager: logInfo verfügbar, logge Garbage Collection...
✅ TimeoutManager: Garbage Collection erfolgreich geloggt
🔍 TimeoutManager: Prüfe Prozess-Status nach Timeout...
🔍 TimeoutManager: Prozess-Status: {"timestamp":"2025-09-01T14:57:36.750Z","pid":12345,"uptime":45.2,"memoryUsage":{...},"downloadProcessActive":{...}}
🔍 TimeoutManager: Speicher nach Timeout: {"rss":126173184,"heapTotal":25153536,"heapUsed":20258872,...}
⚠️ Download durch Timeout abgebrochen: Einladung Vorlagen
🔍 DocumentDownloader: Prüfe Prozess-Status nach Timeout...
🔍 DocumentDownloader: Prozess-Status: {"timestamp":"2025-09-01T14:57:36.751Z","pid":12345,"uptime":45.2,"memoryUsage":{...},"browserContexts":1,"pageCount":1}
🔍 DocumentDownloader: Speicher nach Timeout: {"rss":126173184,"heapTotal":25153536,"heapUsed":20258872,...}
```

### **Log-Datei-Ausgabe:**
```
[2025-09-01T14:57:36.750Z] [+10046ms] [DEBUG] 🔍 TimeoutManager: Prüfe Prozess-Status nach Timeout...
[2025-09-01T14:57:36.750Z] [+10046ms] [DEBUG] 🔍 TimeoutManager: Prozess-Status: {"timestamp":"2025-09-01T14:57:36.750Z","pid":12345,"uptime":45.2,"memoryUsage":{"rss":126173184,"heapTotal":25153536,"heapUsed":20258872,"external":3042372,"arrayBuffers":411974},"cpuUsage":{"user":123456,"system":78901},"activeHandles":15,"activeRequests":2,"eventLoopDelay":0.001,"downloadProcessActive":{"activeTimers":1,"activePromises":0,"activeRequests":1,"hasActiveProcesses":true}}
[2025-09-01T14:57:36.750Z] [+10046ms] [DEBUG] 🔍 TimeoutManager: Speicher nach Timeout: {"rss":126173184,"heapTotal":25153536,"heapUsed":20258872,"external":3042372,"arrayBuffers":411974}
[2025-09-01T14:57:36.751Z] [+10047ms] [WARN] TIMEOUT: Download nach 10000ms
[2025-09-01T14:57:36.751Z] [+10047ms] [ERROR] === DOWNLOAD FEHLGESCHLAGEN ===
[2025-09-01T14:57:36.751Z] [+10047ms] [ERROR] Grund: Download-Timeout nach 10 Sekunden
[2025-09-01T14:57:36.751Z] [+10047ms] [INFO] Gesamtdauer: 10019ms
[2025-09-01T14:57:36.752Z] [+10048ms] [DEBUG] 🔍 DocumentDownloader: Prüfe Prozess-Status nach Timeout...
[2025-09-01T14:57:36.752Z] [+10048ms] [DEBUG] 🔍 DocumentDownloader: Prozess-Status: {"timestamp":"2025-09-01T14:57:36.752Z","pid":12345,"uptime":45.2,"memoryUsage":{"rss":126173184,"heapTotal":25153536,"heapUsed":20258872,"external":3042372,"arrayBuffers":411974},"cpuUsage":{"user":123456,"system":78901},"activeHandles":15,"activeRequests":2,"eventLoopDelay":0.001,"downloadProcessActive":{"activeTimers":1,"activePromises":0,"activeRequests":1,"activeBrowserOps":2,"hasActiveProcesses":true},"browserContexts":1,"pageCount":1}
[2025-09-01T14:57:36.752Z] [+10048ms] [DEBUG] 🔍 DocumentDownloader: Speicher nach Timeout: {"rss":126173184,"heapTotal":25153536,"heapUsed":20258872,"external":3042372,"arrayBuffers":411974}
```

## Interpretation der Ergebnisse

### **Prozess noch aktiv (hasActiveProcesses: true):**
```
"downloadProcessActive": {
  "activeTimers": 1,        // ⚠️ Timer läuft noch
  "activePromises": 0,      // ✅ Keine hängenden Promises
  "activeRequests": 1,      // ⚠️ HTTP-Request läuft noch
  "hasActiveProcesses": true // ⚠️ Prozess ist noch aktiv
}
```

**Bedeutung:** Der Download-Prozess wurde nicht ordnungsgemäß beendet.

### **Prozess beendet (hasActiveProcesses: false):**
```
"downloadProcessActive": {
  "activeTimers": 0,        // ✅ Keine aktiven Timer
  "activePromises": 0,      // ✅ Keine hängenden Promises
  "activeRequests": 0,      // ✅ Keine aktiven Requests
  "hasActiveProcesses": false // ✅ Prozess ist beendet
}
```

**Bedeutung:** Der Download-Prozess wurde erfolgreich beendet.

### **Speicherverwendung:**
```
"memoryUsage": {
  "rss": 126173184,        // Resident Set Size (RAM)
  "heapTotal": 25153536,   // Heap-Gesamtgröße
  "heapUsed": 20258872,    // Aktuell verwendeter Heap
  "external": 3042372,     // Externer Speicher
  "arrayBuffers": 411974   // Array Buffer Speicher
}
```

## Vorteile des Prozess-Monitorings

### ✅ **Vollständige Transparenz:**
- Zeigt genau, welche Prozesse nach einem Timeout noch aktiv sind
- Überwacht Speicherverwendung kontinuierlich
- Erkennt hängende Downloads sofort

### ✅ **Einfache Fehlersuche:**
- Identifiziert, ob der Timeout den Prozess ordnungsgemäß beendet hat
- Zeigt Memory-Leaks auf
- Überwacht Browser-Status

### ✅ **Performance-Monitoring:**
- Event-Loop-Verzögerungen werden gemessen
- CPU-Verbrauch wird überwacht
- Aktive Handles werden gezählt

## Zusammenfassung

**Nach der Meldung `"Download durch Timeout abgebrochen"` wird automatisch überprüft:**

1. **Prozess-Status** - Läuft der Download noch?
2. **Speicherverwendung** - Wie viel Speicher ist belegt?
3. **Aktive Handles** - Gibt es hängende Operationen?
4. **Browser-Status** - Sind Browser-Kontexte noch aktiv?

**Ergebnis:** Vollständige Transparenz über den Zustand des Systems nach einem Timeout!

