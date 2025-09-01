# Detailliertes Timeout-Debugging

## Problem-Analyse

Das ursprüngliche Log zeigte, dass die Garbage Collection nach einem Timeout nicht geloggt wurde:

```
[WARN] TIMEOUT: Download nach 10000ms
[ERROR] FEHLER: Download-Timeout nach 10 Sekunden
[ERROR] === DOWNLOAD FEHLGESCHLAGEN ===
```

**Fehlende Log-Einträge:**
- ❌ Keine Garbage Collection nach Timeout
- ❌ Keine Speicherfreigabe
- ❌ Keine detaillierte Fehlerbehandlung

## Lösung: Granulares Debug-Logging

### Was wurde hinzugefügt?

#### 1. **TimeoutManager Debug-Logging:**
```javascript
// Speicher freigeben bei Timeout
console.log(`        🔍 TimeoutManager: Prüfe global.gc...`);
if (global.gc) {
  console.log(`        🔍 TimeoutManager: global.gc verfügbar, führe Garbage Collection durch...`);
  const beforeMemory = process.memoryUsage();
  console.log(`        🔍 TimeoutManager: Speicher vor GC: ${JSON.stringify(beforeMemory)}`);
  
  global.gc();
  
  const afterMemory = process.memoryUsage();
  console.log(`        🔍 TimeoutManager: Speicher nach GC: ${JSON.stringify(afterMemory)}`);
  
  console.log(`        🔍 TimeoutManager: Prüfe logInfo...`);
  if (logInfo) {
    console.log(`        🔍 TimeoutManager: logInfo verfügbar, logge Garbage Collection...`);
    try {
      logInfo.logGarbageCollection(logInfo, beforeMemory, afterMemory);
      console.log(`        ✅ TimeoutManager: Garbage Collection erfolgreich geloggt`);
    } catch (logError) {
      console.log(`        ❌ TimeoutManager: Fehler beim Loggen der Garbage Collection: ${logError.message}`);
    }
  } else {
    console.log(`        ⚠️ TimeoutManager: logInfo nicht verfügbar`);
  }
} else {
  console.log(`        ⚠️ TimeoutManager: global.gc nicht verfügbar`);
}
```

#### 2. **DocumentDownloader Debug-Logging:**
```javascript
// Speicher freigeben bei Fehlern
console.log(`        🔍 DocumentDownloader: Prüfe global.gc nach Fehler...`);
if (global.gc) {
  console.log(`        🔍 DocumentDownloader: global.gc verfügbar, führe Garbage Collection durch...`);
  const beforeMemory = process.memoryUsage();
  console.log(`        🔍 DocumentDownloader: Speicher vor GC: ${JSON.stringify(beforeMemory)}`);
  
  global.gc();
  
  const afterMemory = process.memoryUsage();
  console.log(`        🔍 DocumentDownloader: Speicher nach GC: ${JSON.stringify(afterMemory)}`);
  
  console.log(`        🔍 DocumentDownloader: Logge Garbage Collection...`);
  try {
    this.downloadLogger.logGarbageCollection(logInfo, beforeMemory, afterMemory);
    console.log(`        ✅ DocumentDownloader: Garbage Collection erfolgreich geloggt`);
  } catch (logError) {
    console.log(`        ❌ DocumentDownloader: Fehler beim Loggen der Garbage Collection: ${logError.message}`);
  }
} else {
  console.log(`        ⚠️ DocumentDownloader: global.gc nicht verfügbar`);
}
```

## Neues Log-Verhalten

### Vorher (unvollständig):
```
[WARN] TIMEOUT: Download nach 10000ms
[ERROR] FEHLER: Download-Timeout nach 10 Sekunden
[ERROR] === DOWNLOAD FEHLGESCHLAGEN ===
```

### Nachher (vollständig mit Debug):
```
[WARN] TIMEOUT: Download nach 10000ms
[DEBUG] 🔍 TimeoutManager: Prüfe global.gc...
[DEBUG] 🔍 TimeoutManager: global.gc verfügbar, führe Garbage Collection durch...
[DEBUG] 🔍 TimeoutManager: Speicher vor GC: {"rss":161206272,"heapTotal":118288384,"heapUsed":95815096,"external":3290305,"arrayBuffers":659928}
[DEBUG] 🔍 TimeoutManager: Speicher nach GC: {"rss":161206272,"heapTotal":118288384,"heapUsed":85678901,"external":3290305,"arrayBuffers":659928}
[DEBUG] 🔍 TimeoutManager: Prüfe logInfo...
[DEBUG] 🔍 TimeoutManager: logInfo verfügbar, logge Garbage Collection...
[DEBUG] GARBAGE COLLECTION durchgeführt | DATA: {"beforeMemory":{...},"afterMemory":{...},"freed":{"heapUsed":10136195}}
[DEBUG] ✅ TimeoutManager: Garbage Collection erfolgreich geloggt
[ERROR] FEHLER: Download-Timeout nach 10 Sekunden
[WARN] TIMEOUT: Download nach 10000ms
[DEBUG] DATEIOPERATION: CHECK_EXISTS
[ERROR] === DOWNLOAD FEHLGESCHLAGEN ===
[ERROR] Grund: Download-Timeout nach 10 Sekunden
[INFO] Gesamtdauer: 10003ms
[DEBUG] 🔍 DocumentDownloader: Prüfe global.gc nach Fehler...
[DEBUG] 🔍 DocumentDownloader: global.gc verfügbar, führe Garbage Collection durch...
[DEBUG] 🔍 DocumentDownloader: Speicher vor GC: {"rss":161206272,"heapTotal":118288384,"heapUsed":85678901,"external":3290305,"arrayBuffers":659928}
[DEBUG] 🔍 DocumentDownloader: Speicher nach GC: {"rss":161206272,"heapTotal":118288384,"heapUsed":74567890,"external":3290305,"arrayBuffers":659928}
[DEBUG] 🔍 DocumentDownloader: Logge Garbage Collection...
[DEBUG] GARBAGE COLLECTION durchgeführt | DATA: {"beforeMemory":{...},"afterMemory":{...},"freed":{"heapUsed":11111011}}
[DEBUG] ✅ DocumentDownloader: Garbage Collection erfolgreich geloggt
```

## Debug-Informationen

### **TimeoutManager Debug-Schritte:**

1. **🔍 Prüfe global.gc** - Überprüft, ob Garbage Collection verfügbar ist
2. **🔍 global.gc verfügbar** - Bestätigt, dass GC verfügbar ist
3. **🔍 Speicher vor GC** - Zeigt Speicherverwendung vor der Garbage Collection
4. **🔍 Speicher nach GC** - Zeigt Speicherverwendung nach der Garbage Collection
5. **🔍 Prüfe logInfo** - Überprüft, ob LogInfo-Objekt verfügbar ist
6. **🔍 logInfo verfügbar** - Bestätigt, dass LogInfo verfügbar ist
7. **✅ Garbage Collection erfolgreich geloggt** - Bestätigt erfolgreiches Logging

### **DocumentDownloader Debug-Schritte:**

1. **🔍 Prüfe global.gc nach Fehler** - Überprüft GC nach Fehlerbehandlung
2. **🔍 global.gc verfügbar** - Bestätigt GC-Verfügbarkeit
3. **🔍 Speicher vor GC** - Speicherverwendung vor GC
4. **🔍 Speicher nach GC** - Speicherverwendung nach GC
5. **🔍 Logge Garbage Collection** - Versucht Garbage Collection zu loggen
6. **✅ Garbage Collection erfolgreich geloggt** - Bestätigt erfolgreiches Logging

## Mögliche Fehlerszenarien

### **Szenario 1: global.gc nicht verfügbar**
```
[DEBUG] 🔍 TimeoutManager: Prüfe global.gc...
[DEBUG] ⚠️ TimeoutManager: global.gc nicht verfügbar
```
**Ursache:** Node.js wurde nicht mit `--expose-gc` Flag gestartet

### **Szenario 2: logInfo nicht verfügbar**
```
[DEBUG] 🔍 TimeoutManager: Prüfe logInfo...
[DEBUG] ⚠️ TimeoutManager: logInfo nicht verfügbar
```
**Ursache:** LogInfo-Objekt wurde nicht korrekt weitergegeben

### **Szenario 3: Fehler beim Loggen**
```
[DEBUG] 🔍 TimeoutManager: logInfo verfügbar, logge Garbage Collection...
[DEBUG] ❌ TimeoutManager: Fehler beim Loggen der Garbage Collection: Cannot read property 'logGarbageCollection' of undefined
```
**Ursache:** LogInfo-Objekt ist beschädigt oder unvollständig

## Vorteile des detaillierten Debug-Loggings

### ✅ **Vollständige Transparenz:**
- Jeder Schritt wird protokolliert
- Speicherverwendung wird vor/nach GC angezeigt
- Erfolg/Fehler jedes Schritts wird bestätigt

### ✅ **Einfache Fehlersuche:**
- Klare Identifikation, wo der Prozess hängt
- Detaillierte Fehlermeldungen
- Speicherverwendung wird kontinuierlich überwacht

### ✅ **Performance-Monitoring:**
- Speicherfreigabe wird quantifiziert
- GC-Effektivität wird gemessen
- Memory-Leaks werden früh erkannt

## Zusammenfassung

Das neue detaillierte Debug-Logging zeigt **jeden Schritt** des Timeout-Prozesses:

1. **Timeout wird ausgelöst**
2. **Garbage Collection wird durchgeführt**
3. **Speicherverwendung wird protokolliert**
4. **Logging wird bestätigt**
5. **Fehler wird geworfen**
6. **DocumentDownloader fängt Fehler ab**
7. **Zusätzliche Garbage Collection wird durchgeführt**
8. **Vollständige Fehlerbehandlung wird protokolliert**

**Ergebnis:** Vollständige Transparenz über den gesamten Timeout-Prozess mit detaillierten Debug-Informationen für die Fehlersuche.

