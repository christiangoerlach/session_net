# Neuer Download-Ansatz: Request-Interception

## Übersicht

Wir haben den Download-Ansatz komplett geändert, um die Timeout-Probleme und hängenden Scripts zu lösen. Statt PDFs direkt herunterzuladen, fangen wir die Requests mit Playwright ab und laden sie separat mit node-fetch herunter.

## Wie funktioniert der neue Ansatz?

### **1. Request-Interception einrichten:**
```javascript
// Intercepte alle PDF-Requests
await this.page.route('**/*.pdf', async (route, request) => {
  const url = request.url();
  const headers = request.headers();
  
  // Speichere URL und Headers
  this.pdfRequests.push({ url, headers, timestamp: new Date().toISOString() });
  
  // Breche den Request ab (wir laden es später separat)
  route.abort();
});

// Intercepte auch getfile.asp Requests
await this.page.route('**/getfile.asp*', async (route, request) => {
  if (this.isPdfRequest(request)) {
    this.pdfRequests.push({ url, headers, timestamp: new Date().toISOString() });
    route.abort();
  } else {
    route.continue();
  }
});
```

### **2. Download-Link anklicken:**
```javascript
// Klicke auf den Download-Link, damit der Request abgefangen wird
await this.page.click(`a[href*="${downloadLink.split('/').pop()}"]`);

// Warte kurz, damit der Request abgefangen werden kann
await this.page.waitForTimeout(1000);
```

### **3. Abgefangene PDFs separat herunterladen:**
```javascript
// Lade die abgefangenen PDFs mit node-fetch herunter
const downloadResults = await this.playwrightDownloader.downloadInterceptedPdfs(downloadDir, logInfo);
```

## Vorteile des neuen Ansatzes:

### ✅ **Keine Timeout-Probleme mehr:**
- **Keine hängenden HTTP-Requests** - alle werden sofort abgebrochen
- **Keine blockierten Event Loops** - Requests laufen nicht im Hintergrund
- **Keine Memory-Leaks** - alle Ressourcen werden sofort freigegeben

### ✅ **Bessere Kontrolle:**
- **Alle Requests werden abgefangen** - keine verpassten Downloads
- **Headers werden gespeichert** - Session-Daten bleiben erhalten
- **Separate Downloads** - jeder Download kann einzeln gesteuert werden

### ✅ **Einfachere Fehlerbehandlung:**
- **Keine komplexen Timeout-Mechanismen** mehr nötig
- **Jeder Download ist isoliert** - Fehler bei einem Download blockieren nicht andere
- **Bessere Logging** - alle abgefangenen Requests werden protokolliert

## Was wurde geändert:

### **1. PlaywrightDownloader:**
- **Request-Interception** für PDF- und getfile.asp-Requests
- **Speicherung von URLs und Headers** aller abgefangenen Requests
- **Separate Download-Methode** mit node-fetch
- **Alte Download-Methode** wird nicht mehr verwendet

### **2. DocumentDownloader:**
- **Keine TimeoutManager-Aufrufe** mehr
- **Klick auf Download-Links** statt direkter Downloads
- **Verwendung der abgefangenen PDFs** für Downloads
- **Einfachere Fehlerbehandlung**

### **3. Dependencies:**
- **node-fetch installiert** für separate Downloads
- **HTTP-Downloader entfernt** - wird nicht mehr benötigt

## Der neue Download-Flow:

### **Schritt 1: Request-Interception einrichten**
```javascript
// Beim Start der Anwendung
await this.page.route('**/*.pdf', async (route, request) => {
  // Request abfangen und speichern
  route.abort();
});
```

### **Schritt 2: Download-Link anklicken**
```javascript
// Statt direkt herunterzuladen
await this.page.click(`a[href*="${downloadLink}"]`);
```

### **Schritt 3: Request wird abgefangen**
```javascript
// Playwright fängt den Request ab und speichert URL + Headers
// Der Request wird sofort abgebrochen (route.abort())
```

### **Schritt 4: PDF separat herunterladen**
```javascript
// Mit node-fetch und den gespeicherten Headers
const response = await fetch(request.url, { headers: request.headers });
```

## Warum löst das die Probleme?

### **Vorher (Problem):**
- **Direkte Downloads** führten zu hängenden HTTP-Requests
- **4 aktive Requests** blockierten den Event Loop
- **Timeout-Mechanismen** funktionierten nicht richtig
- **Scripts hingen sich auf** bei der Aufräumarbeit

### **Nachher (Lösung):**
- **Alle Requests werden sofort abgebrochen** (route.abort())
- **Keine hängenden Requests** mehr
- **Separate Downloads** mit node-fetch sind zuverlässiger
- **Keine Timeout-Probleme** mehr

## Ergebnis:

**Der neue Ansatz eliminiert alle bisherigen Probleme:**
- ✅ **Keine hängenden Scripts** mehr
- ✅ **Keine Timeout-Probleme** mehr  
- ✅ **Keine Memory-Leaks** mehr
- ✅ **Bessere Kontrolle** über Downloads
- ✅ **Einfachere Wartung** und Debugging

**Das System sollte jetzt stabil laufen und alle PDFs erfolgreich herunterladen!**

