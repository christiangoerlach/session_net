# Global.gc Problem und Lösung

## Problem-Analyse

### Was passiert aktuell?

Das Log zeigt:
```
[WARN] TIMEOUT: Download nach 10000ms
[ERROR] FEHLER: Download-Timeout nach 10 Sekunden
[ERROR] === DOWNLOAD FEHLGESCHLAGEN ===
```

**Im Terminal steht:** `global.gc nicht verfügbar`

**Das Script hängt sich auf und bricht ab.**

### Warum hängt das Script?

Das Problem liegt daran, dass:

1. **`global.gc` nicht verfügbar ist** - Node.js wurde nicht mit `--expose-gc` Flag gestartet
2. **Debug-Ausgaben nur in Konsole** - Die `console.log` Ausgaben werden nicht in die Log-Datei geschrieben
3. **Script wartet auf GC** - Das Script versucht Garbage Collection durchzuführen, aber `global.gc` ist nicht verfügbar

## Ursache des Problems

### **Node.js Start-Flag fehlt:**

Das Script muss mit dem `--expose-gc` Flag gestartet werden:

```bash
# FALSCH (aktuell):
node main.js

# RICHTIG:
node --expose-gc main.js
```

### **Debug-Ausgaben nicht in Log-Datei:**

Die Debug-Ausgaben werden nur über `console.log` angezeigt, aber nicht in die Log-Datei geschrieben:

```javascript
// FALSCH (aktuell):
console.log(`        🔍 TimeoutManager: Prüfe global.gc...`);

// RICHTIG (nach Korrektur):
console.log(`        🔍 TimeoutManager: Prüfe global.gc...`);
if (logInfo) {
  logInfo.addLogEntry(logInfo, 'DEBUG', '🔍 TimeoutManager: Prüfe global.gc...');
}
```

## Lösung

### **1. Node.js mit GC-Flag starten:**

```bash
node --expose-gc main.js
```

### **2. Debug-Ausgaben in Log-Datei schreiben:**

Alle Debug-Ausgaben werden jetzt sowohl in die Konsole als auch in die Log-Datei geschrieben:

```javascript
// TimeoutManager
console.log(`        🔍 TimeoutManager: Prüfe global.gc...`);
if (logInfo) {
  logInfo.addLogEntry(logInfo, 'DEBUG', '🔍 TimeoutManager: Prüfe global.gc...');
}

if (global.gc) {
  // GC verfügbar - normale Ausführung
  console.log(`        🔍 TimeoutManager: global.gc verfügbar, führe Garbage Collection durch...`);
  if (logInfo) {
    logInfo.addLogEntry(logInfo, 'DEBUG', '🔍 TimeoutManager: global.gc verfügbar, führe Garbage Collection durch...');
  }
  // ... GC durchführen
} else {
  // GC nicht verfügbar - Warnung loggen und weitermachen
  console.log(`        ⚠️ TimeoutManager: global.gc nicht verfügbar`);
  if (logInfo) {
    logInfo.addLogEntry(logInfo, 'WARN', '⚠️ TimeoutManager: global.gc nicht verfügbar');
  }
}
```

## Erwartetes Verhalten nach Korrektur

### **Mit `--expose-gc` Flag:**

```
[WARN] TIMEOUT: Download nach 10000ms
[DEBUG] 🔍 TimeoutManager: Prüfe global.gc...
[DEBUG] 🔍 TimeoutManager: global.gc verfügbar, führe Garbage Collection durch...
[DEBUG] 🔍 TimeoutManager: Speicher vor GC: {...}
[DEBUG] 🔍 TimeoutManager: Speicher nach GC: {...}
[DEBUG] 🔍 TimeoutManager: Prüfe logInfo...
[DEBUG] 🔍 TimeoutManager: logInfo verfügbar, logge Garbage Collection...
[DEBUG] GARBAGE COLLECTION durchgeführt | DATA: {...}
[DEBUG] ✅ TimeoutManager: Garbage Collection erfolgreich geloggt
[ERROR] FEHLER: Download-Timeout nach 10 Sekunden
[ERROR] === DOWNLOAD FEHLGESCHLAGEN ===
```

### **Ohne `--expose-gc` Flag:**

```
[WARN] TIMEOUT: Download nach 10000ms
[DEBUG] 🔍 TimeoutManager: Prüfe global.gc...
[WARN] ⚠️ TimeoutManager: global.gc nicht verfügbar
[ERROR] FEHLER: Download-Timeout nach 10 Sekunden
[ERROR] === DOWNLOAD FEHLGESCHLAGEN ===
```

## Warum hängt das Script aktuell?

### **Mögliche Ursachen:**

1. **Unendliche Warteschleife** - Das Script wartet auf eine GC-Operation, die nie kommt
2. **Promise wird nie aufgelöst** - Ein Promise wartet auf GC, aber `global.gc` ist nicht verfügbar
3. **Timeout-Handler blockiert** - Der Timeout-Handler wartet auf GC-Abschluss

### **Debug-Schritte:**

1. **Prüfe Node.js Start-Flag:**
   ```bash
   # Aktueller Start-Befehl prüfen
   ps aux | grep node
   ```

2. **Prüfe Log-Datei auf Debug-Ausgaben:**
   - Debug-Ausgaben sollten jetzt in der Log-Datei erscheinen
   - Zeigt genau, wo das Script hängt

3. **Prüfe Terminal-Ausgabe:**
   - `global.gc nicht verfügbar` sollte als Warnung erscheinen
   - Script sollte trotzdem weiterlaufen

## Empfohlene Lösung

### **1. Sofortige Lösung:**
```bash
node --expose-gc main.js
```

### **2. Langfristige Lösung:**
- Debug-Ausgaben sind jetzt in Log-Datei verfügbar
- Bessere Fehlerbehandlung für fehlende GC
- Vollständige Transparenz über Timeout-Prozesse

## Zusammenfassung

**Das Problem:** `global.gc` ist nicht verfügbar, weil Node.js nicht mit `--expose-gc` gestartet wurde.

**Die Lösung:** 
1. Node.js mit `--expose-gc` Flag starten
2. Debug-Ausgaben werden jetzt in Log-Datei geschrieben
3. Bessere Fehlerbehandlung für fehlende GC

**Ergebnis:** Vollständige Transparenz über den Timeout-Prozess und korrekte Behandlung von fehlender Garbage Collection.

