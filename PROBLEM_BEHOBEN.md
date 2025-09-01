# Probleme behoben - Dokumentenerkennung und TOP-Link-Erkennung

## Identifizierte Probleme

### 1. Dokumentenerkennung funktionierte nur für das erste Dokument
**Problem:** Der Document-Downloader verwendete eine `while(true)`-Schleife mit `.nth(index)`, die nur das erste gefundene Dokument erkannte.

**Lösung:** 
- Neue Logik: Alle Dokumente auf einmal finden und dann verarbeiten
- Verwendung verschiedener CSS-Selektoren für bessere Erkennung
- Sammeln aller Dokumente in einem Array vor der Verarbeitung
- Duplikatsprüfung um doppelte Dokumente zu vermeiden

### 2. TOP-Link-Erkennung funktionierte nicht auf allen Seitentypen
**Problem:** Das Script suchte nach TOP-Links auf allen Termin-Seiten, aber nicht alle Termin-Seiten haben TOP-Links.

**Lösung:**
- Prüfung der URL: Nur auf `si0057.asp`-Seiten (Tagesordnungs-Seiten) nach TOP-Links suchen
- Verbesserte CSS-Selektoren für TOP-Link-Erkennung
- Klare Unterscheidung zwischen Termin-Seiten mit und ohne Tagesordnung

### 3. PDF-Zuordnung und Namensgebung funktionierte nicht korrekt
**Problem:** 
- Die Request-Liste im Playwright-Downloader wurde nicht geleert, wodurch alte PDFs erneut heruntergeladen wurden
- Die Zuordnung zwischen Dokumentnamen und heruntergeladenen PDFs ging verloren
- PDFs bekamen automatisch generierte Namen statt der korrekten Dokumentnamen

**Lösung:**
- Request-Liste wird nach jedem Download geleert um Duplikate zu vermeiden
- Verbesserte Umbenennung der heruntergeladenen PDFs mit korrekten Dokumentnamen
- Bessere Fehlerbehandlung beim Umbenennen der Dateien

### 4. Request-Interception funktionierte nur beim ersten Download
**Problem:** 
- Nach dem ersten erfolgreichen Download wurden keine PDF-Requests mehr abgefangen
- Die Request-Interception wurde möglicherweise durch das Leeren der Liste gestört
- Folge-Downloads schlugen fehl, weil keine PDFs abgefangen wurden

**Lösung:**
- Neue `ensureRequestInterception()`-Funktion prüft und stellt Request-Interception sicher
- Request-Interception wird vor jedem Download aktiviert
- Robuste Prüfung des Interception-Status mit automatischer Neu-Einrichtung

### 5. Browser-Seite wurde nach dem ersten Download instabil
**Problem:** 
- Fehler "Target page, context or browser has been closed" nach dem ersten Download
- JavaScript-Click-Events destabilisierten die Seite
- Request-Interception mit `route.abort()` störte die Seitenstabilität

**Lösung:**
- Komplett neuer Ansatz: Direkter Download über `fetch()` statt JavaScript-Click
- Request-Interception lässt Requests durchlaufen (`route.continue()`) statt sie abzubrechen
- Keine Browser-Interaktion mehr, nur noch direkte HTTP-Requests

### 6. node-fetch v3 Kompatibilitätsproblem
**Problem:** 
- Fehler "response.body.pipe is not a function" bei Downloads
- node-fetch v3 hat eine andere Response-API als v2
- Dateien wurden leer heruntergeladen

**Lösung:**
- Verwendung von `response.arrayBuffer()` statt `response.body.pipe()`
- Kompatibilität mit node-fetch v3 API
- Korrekte Datei-Schreibung mit `fs.writeFileSync()`

## Geänderte Dateien

### src/termin-processor.js
- `processTopPoints()`: URL-Prüfung hinzugefügt, verbesserte TOP-Link-Selektoren

### src/modules/document-downloader.js
- `downloadDocuments()`: Neue Logik für Dokument-Sammlung und -Verarbeitung
- `downloadTopDocuments()`: Entsprechende Anpassungen für TOP-Dokumente
- `downloadSingleDocument()`: Komplett neuer Ansatz mit direktem fetch-Download + node-fetch v3 Kompatibilität
- `downloadSingleTopDocument()`: Entsprechende Anpassungen für TOP-Dokumente + node-fetch v3 Kompatibilität

### src/modules/playwright-downloader.js
- `downloadInterceptedPdfs()`: Request-Liste wird nach jedem Download geleert
- `ensureRequestInterception()`: Neue Funktion zur Sicherstellung der Request-Interception
- `setupRequestInterception()`: Requests werden durchgelassen statt abgebrochen

## Neue Funktionalität

### Dokumentenerkennung
```javascript
const documentSelectors = [
  'a[title*="Dokument Download"]',
  'a[aria-label*="Dokument Download"]',
  'a[href*="getfile.asp"]',
  '.smc-downloaded a[href*="getfile.asp"]',
  'a.smc-link-normal[href*="getfile.asp"]'
];
```

### TOP-Link-Erkennung
```javascript
// Prüfe zuerst, ob wir auf einer Tagesordnungs-Seite sind (si0057.asp)
const currentUrl = this.page.url();
const isTagesordnungPage = currentUrl.includes('si0057.asp');

if (!isTagesordnungPage) {
  console.log(`ℹ️ Keine Tagesordnungs-Seite - keine TOP-Links erwartet`);
  return;
}
```

### Direkter Download über fetch (node-fetch v3 kompatibel)
```javascript
// Neuer Ansatz: Direkter Download über fetch statt JavaScript-Click
const response = await fetch(downloadUrl, {
  headers: {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/pdf,application/octet-stream,*/*',
    'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
  },
  timeout: 30000
});

// Schreibe Datei direkt - Kompatibel mit node-fetch v3
const arrayBuffer = await response.arrayBuffer();
const buffer = Buffer.from(arrayBuffer);
fs.writeFileSync(dokumentPath, buffer);
```

### Request-Interception-Sicherstellung
```javascript
// Stelle sicher, dass Request-Interception aktiv ist
await this.playwrightDownloader.ensureRequestInterception();

// Neue Funktion zur Status-Prüfung
async ensureRequestInterception() {
  const hasRoute = this.page._routes && this.page._routes.length > 0;
  if (!hasRoute) {
    await this.setupRequestInterception();
  }
}
```

### Robuste Request-Interception
```javascript
// WICHTIG: Lasse den Request durchlaufen, breche ihn NICHT ab
route.continue();
```

## Erwartete Verbesserungen

1. **Alle Dokumente werden erkannt:** Statt nur das erste Dokument zu finden, werden jetzt alle Dokumente auf der Seite erkannt und heruntergeladen.

2. **Korrekte TOP-Link-Erkennung:** TOP-Links werden nur auf Tagesordnungs-Seiten gesucht, was Fehlermeldungen vermeidet.

3. **Korrekte PDF-Zuordnung:** Jedes PDF bekommt den korrekten Dokumentnamen, nicht automatisch generierte Namen.

4. **Keine Duplikate:** Die Request-Liste wird nach jedem Download geleert, wodurch keine PDFs mehrfach heruntergeladen werden.

5. **Robuste Request-Interception:** Request-Interception wird vor jedem Download sichergestellt und funktioniert für alle Downloads.

6. **Stabile Browser-Seite:** Keine JavaScript-Click-Events mehr, die die Seite destabilisieren könnten.

7. **Direkte Downloads:** Verwendung von `fetch()` für direkte HTTP-Requests ohne Browser-Interaktion.

8. **node-fetch v3 Kompatibilität:** Korrekte Verwendung der node-fetch v3 API für Downloads.

9. **Korrekte Datei-Schreibung:** Dateien werden nicht mehr leer heruntergeladen.

10. **Bessere Logging:** Detailliertere Logs zeigen, welche Selektoren funktionieren und wie viele Dokumente/TOP-Links gefunden wurden.

11. **Robustere Erkennung:** Mehrere CSS-Selektoren erhöhen die Wahrscheinlichkeit, alle Elemente zu finden.

## Test-Ergebnisse

Die Änderungen wurden basierend auf der Analyse der heruntergeladenen HTML-Dateien implementiert:
- Termin-Seiten mit TOP-Links: `si0057.asp` (Tagesordnungs-Seiten)
- Termin-Seiten ohne TOP-Links: `si0050.asp` (Informations-Seiten)

Beide Seitentypen haben Dokumente, aber nur Tagesordnungs-Seiten haben TOP-Links.

## Bekannte Probleme vor der Behebung

1. **Erstes Dokument funktionierte:** Das erste Dokument wurde korrekt heruntergeladen
2. **Folgende Downloads problematisch:** Ab dem zweiten Dokument wurde das erste PDF erneut heruntergeladen, aber mit dem Namen des zweiten Dokuments
3. **Request-Liste nicht geleert:** Alte PDF-Requests blieben in der Liste und wurden erneut verarbeitet
4. **Namensgebung fehlerhaft:** PDFs bekamen automatisch generierte Namen statt der korrekten Dokumentnamen
5. **Request-Interception gestört:** Nach dem ersten Download wurden keine PDF-Requests mehr abgefangen
6. **Folge-Downloads fehlgeschlagen:** Alle Downloads nach dem ersten schlugen fehl, weil keine PDFs abgefangen wurden
7. **Browser-Seite instabil:** Fehler "Target page, context or browser has been closed" nach dem ersten Download
8. **JavaScript-Click-Events problematisch:** Browser-Interaktionen destabilisierten die Seite
9. **Request-Interception zu aggressiv:** `route.abort()` störte die Seitenstabilität
10. **node-fetch v3 Inkompatibilität:** Fehler "response.body.pipe is not a function" bei Downloads
11. **Leere Dateien:** Dateien wurden leer heruntergeladen aufgrund der falschen node-fetch API-Nutzung
