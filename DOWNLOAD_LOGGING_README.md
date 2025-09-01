# Detailliertes Download-Logging System

## Übersicht

Das neue Download-Logging-System erstellt für jedes heruntergeladene Dokument eine separate Log-Datei mit detaillierten Informationen zur Fehlersuche und Performance-Analyse.

## Funktionsweise

### 1. Log-Datei-Struktur

Für jedes Dokument wird eine eindeutige Log-Datei im Verzeichnis `download_logs/` erstellt:

```
download_logs/
├── 2024-01-15T10-30-45-123Z_14_Magistrat_Amtliche_Bekanntmachung.log
├── 2024-01-15T10-31-12-456Z_14_Magistrat_Einladung.log
├── 2024-01-15T10-32-01-789Z_15_Ortsbeirat_Grüningen_TOP1_Eröffnung_Antrag.pdf
└── download_summary.log
```

### 2. Log-Datei-Format

Jede Log-Datei enthält folgende Informationen:

```
[2024-01-15T10:30:45.123Z] [+0ms] [INFO] === DOWNLOAD START === | DATA: {"dokumentName":"Amtliche Bekanntmachung","downloadUrl":"https://...","filePath":"...","terminOrdnerName":"14_Magistrat","systemInfo":{"nodeVersion":"v18.17.0","platform":"win32","arch":"x64","memoryUsage":{"rss":12345678,"heapUsed":5678901,"heapTotal":12345678,"external":123456},"uptime":123.45}}}
[2024-01-15T10:30:45.124Z] [+1ms] [INFO] Dokument: Amtliche Bekanntmachung
[2024-01-15T10:30:45.125Z] [+2ms] [INFO] Download URL: https://pohlheim.de/getfile.asp?id=12345
[2024-01-15T10:30:45.126Z] [+3ms] [INFO] Zieldatei: C:\...\Amtliche_Bekanntmachung.pdf
[2024-01-15T10:30:45.127Z] [+4ms] [INFO] Termin: 14_Magistrat
[2024-01-15T10:30:45.128Z] [+5ms] [DEBUG] Speicherverwendung | DATA: {"rss":12345678,"heapUsed":5678901,"heapTotal":12345678,"external":123456}
[2024-01-15T10:30:45.129Z] [+6ms] [DEBUG] FUNKTION: timeoutManager.downloadWithTimeout aufgerufen | DATA: {"url":"https://...","filePath":"...","dokumentName":"Amtliche Bekanntmachung","terminOrdnerName":"14_Magistrat"}
[2024-01-15T10:30:45.130Z] [+7ms] [DEBUG] FUNKTION: page.context().cookies() aufgerufen | DATA: {}
[2024-01-15T10:30:45.135Z] [+12ms] [DEBUG] FUNKTION: page.context().cookies() abgeschlossen | DATA: {"result":{"cookieCount":5},"duration":5}
[2024-01-15T10:30:45.136Z] [+13ms] [DEBUG] FUNKTION: page.evaluate(userAgent) aufgerufen | DATA: {}
[2024-01-15T10:30:45.140Z] [+17ms] [DEBUG] FUNKTION: page.evaluate(userAgent) abgeschlossen | DATA: {"result":{"userAgent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."},"duration":4}
[2024-01-15T10:30:45.141Z] [+18ms] [DEBUG] HTTP-REQUEST gestartet | DATA: {"url":"https://...","method":"GET","headers":{"Cookie":"session=abc123...","User-Agent":"Mozilla/5.0...","Accept":"application/pdf,application/octet-stream,*/*","Accept-Language":"de-DE,de;q=0.9,en;q=0.8","Accept-Encoding":"gzip, deflate, br","Connection":"keep-alive","Upgrade-Insecure-Requests":"1"}}
[2024-01-15T10:30:46.200Z] [+1077ms] [DEBUG] HTTP-RESPONSE erhalten | DATA: {"statusCode":200,"headers":{"content-type":"application/pdf","content-length":"123456"},"contentLength":"123456"}
[2024-01-15T10:30:46.201Z] [+1078ms] [DEBUG] CONTENT-VALIDATION: ERFOLGREICH | DATA: {"contentType":"application/pdf","isValid":true,"expectedType":"application/pdf"}
[2024-01-15T10:30:46.202Z] [+1079ms] [DEBUG] DATEIGRÖSSE-PRÜFUNG: OK | DATA: {"fileSize":123456,"maxSize":10485760,"isTooLarge":false}
[2024-01-15T10:30:46.203Z] [+1080ms] [DEBUG] FUNKTION: Buffer.from() aufgerufen | DATA: {"dataLength":123456}
[2024-01-15T10:30:46.205Z] [+1082ms] [DEBUG] FUNKTION: Buffer.from() abgeschlossen | DATA: {"result":{"bufferLength":123456},"duration":2}
[2024-01-15T10:30:46.206Z] [+1083ms] [DEBUG] DATEIOPERATION: WRITE_FILE | DATA: {"operation":"WRITE_FILE","filePath":"C:\\...\\Amtliche_Bekanntmachung.pdf","result":{"size":123456}}
[2024-01-15T10:30:46.207Z] [+1084ms] [DEBUG] FUNKTION: GARBAGE_COLLECTION | DATA: {"action":"response.data = null"}
[2024-01-15T10:30:46.208Z] [+1085ms] [DEBUG] DATEIOPERATION: CHECK_EXISTS | DATA: {"operation":"CHECK_EXISTS","filePath":"C:\\...\\Amtliche_Bekanntmachung.pdf","result":{"exists":true,"size":123456}}
[2024-01-15T10:30:46.209Z] [+1086ms] [SUCCESS] === DOWNLOAD ERFOLGREICH === | DATA: {"fileSize":123456,"duration":1086}
[2024-01-15T10:30:46.210Z] [+1087ms] [INFO] Gesamtdauer: 1086ms
[2024-01-15T10:30:46.211Z] [+1088ms] [INFO] Dateigröße: 123456 Bytes
[2024-01-15T10:30:46.212Z] [+1089ms] [DEBUG] GARBAGE COLLECTION durchgeführt | DATA: {"beforeMemory":{"rss":12345678,"heapUsed":5678901,"heapTotal":12345678,"external":123456},"afterMemory":{"rss":12345678,"heapUsed":4567890,"heapTotal":12345678,"external":123456},"freed":{"rss":0,"heapUsed":1111011,"heapTotal":0,"external":0}}
```

### 3. Log-Level

Das System verwendet verschiedene Log-Level:

- **INFO**: Allgemeine Informationen über den Download-Prozess
- **DEBUG**: Detaillierte technische Informationen für Fehlersuche
- **WARN**: Warnungen (z.B. Timeouts, aber Download kann fortgesetzt werden)
- **ERROR**: Fehler, die den Download verhindern
- **SUCCESS**: Erfolgreicher Abschluss eines Downloads

### 4. Erfasste Informationen

#### System-Informationen
- Node.js Version
- Betriebssystem
- Architektur
- Speicherverwendung vor/nach Download
- System-Uptime

#### Download-Details
- Dokumentname
- Download-URL
- Zieldatei-Pfad
- Termin-Ordner
- TOP-Informationen (falls zutreffend)

#### HTTP-Request/Response
- Request-Headers (Cookie, User-Agent, etc.)
- Response-Status
- Content-Type
- Content-Length
- Response-Headers

#### Funktionsaufrufe
- Aufgerufene Funktionen mit Parametern
- Ausführungsdauer
- Rückgabewerte

#### Dateioperationen
- Datei-Erstellung
- Datei-Größe
- Existenz-Prüfungen
- Schreiboperationen

#### Performance-Metriken
- Gesamtdauer des Downloads
- Speicherverwendung vor/nach Garbage Collection
- Timeout-Ereignisse

#### Fehlerbehandlung
- Detaillierte Fehlermeldungen
- Stack-Traces
- Kontext-Informationen

### 5. Verwendung für Fehlersuche

#### Timeout-Probleme
```
[WARN] TIMEOUT: Download nach 10000ms
```
- Prüfen Sie die Netzwerkverbindung
- Überprüfen Sie die Server-Antwortzeiten
- Erhöhen Sie ggf. die Timeout-Dauer

#### HTTP-Fehler
```
[ERROR] FEHLER: HTTP 404: Not Found
```
- Prüfen Sie die Download-URL
- Überprüfen Sie die Session-Cookies
- Kontrollieren Sie die Server-Verfügbarkeit

#### Speicherprobleme
```
[DEBUG] GARBAGE COLLECTION durchgeführt | DATA: {"freed":{"heapUsed":1111011}}
```
- Überwachen Sie die Speicherverwendung
- Prüfen Sie auf Memory-Leaks
- Optimieren Sie die Garbage Collection

#### Dateigrößen-Probleme
```
[DEBUG] DATEIGRÖSSE-PRÜFUNG: ZU GROSS | DATA: {"fileSize":15728640,"maxSize":10485760}
```
- Dokument überschreitet 10MB-Limit
- Prüfen Sie die tatsächliche Dateigröße
- Erhöhen Sie ggf. das Größenlimit

### 6. Zusammenfassung

Die Datei `download_summary.log` enthält eine Übersicht aller erstellten Log-Dateien:

```
=== DOWNLOAD SUMMARY ===
Erstellt: 2024-01-15T10:35:00.000Z
Logs-Verzeichnis: download_logs

Gefundene Log-Dateien: 3

- 2024-01-15T10-30-45-123Z_14_Magistrat_Amtliche_Bekanntmachung.log (2048 Bytes, 2024-01-15T10:30:46.211Z)
- 2024-01-15T10-31-12-456Z_14_Magistrat_Einladung.log (1536 Bytes, 2024-01-15T10:31:13.567Z)
- 2024-01-15T10-32-01-789Z_15_Ortsbeirat_Grüningen_TOP1_Eröffnung_Antrag.pdf (3072 Bytes, 2024-01-15T10:32:02.890Z)
```

### 7. Konfiguration

Das Logging-System kann über folgende Parameter angepasst werden:

- **Logs-Verzeichnis**: Standardmäßig `download_logs/`
- **Dateiname-Format**: `{timestamp}_{termin}_{dokument}.log`
- **Log-Level**: Alle Level werden standardmäßig erfasst
- **Speicherverwendung**: Automatische Erfassung vor/nach wichtigen Operationen

### 8. Performance-Überlegungen

- Log-Dateien werden sofort geschrieben (kein Buffering)
- Jedes Dokument erhält eine eigene Log-Datei
- Garbage Collection wird nach jedem Download durchgeführt
- Speicherverwendung wird kontinuierlich überwacht

### 9. Wartung

- Log-Dateien können nach Bedarf gelöscht werden
- Zusammenfassung wird automatisch nach jedem Download erstellt
- Alte Log-Dateien können archiviert werden
- Log-Verzeichnis wird automatisch erstellt

## Fazit

Das neue Logging-System bietet umfassende Transparenz über den Download-Prozess und ermöglicht eine detaillierte Fehlersuche bei Problemen. Jedes Dokument wird vollständig protokolliert, von der ersten Anfrage bis zur finalen Speicherung.

