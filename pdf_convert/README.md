# PDF OCR Tool für Session Net

Ein Python-Tool zum automatischen OCR (Optical Character Recognition) von PDF-Dateien, die keine durchsuchbare Textschicht enthalten.

## 🚀 Features

- **Automatische Text-Erkennung:** Prüft, ob PDFs bereits Text enthalten
- **OCR-Verarbeitung:** Wendet Tesseract OCR auf PDFs ohne Text an
- **Rekursive Verarbeitung:** Durchsucht alle Unterverzeichnisse
- **Intelligente Überspringung:** Überspringt bereits OCR-bearbeitete Dateien
- **Detaillierte Statistiken:** Zeigt Verarbeitungsstatistiken an

## 📋 Voraussetzungen

### Python-Abhängigkeiten
```bash
pip install -r requirements.txt
```

### System-Abhängigkeiten

#### Windows:
1. **Tesseract OCR:** [Download hier](https://github.com/UB-Mannheim/tesseract/wiki)
2. **Poppler:** [Download hier](https://github.com/oschwartz10612/poppler-windows/releases/)

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-deu poppler-utils
```

#### macOS:
```bash
brew install tesseract tesseract-lang poppler
```

## 🛠️ Installation

1. **Abhängigkeiten installieren:**
```bash
cd pdf_convert
pip install -r requirements.txt
```

2. **Tesseract konfigurieren (falls nötig):**
```python
# In pdfconvert.py, falls Tesseract nicht im PATH ist:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## 🚀 Verwendung

### Grundlegende Verwendung

```bash
# Automatische Verzeichnissuche
python pdfconvert.py

# Spezifisches Verzeichnis
python pdfconvert.py "D:\ADN\session_net\pohlheim_geschuetzt\Kalender_2025_August"

# Hilfe anzeigen
python pdfconvert.py --help
```

### Beispiele

```bash
# Einzelnes Verzeichnis
python pdfconvert.py "Kalender_2025_August"

# Mit rekursiver Suche
python pdfconvert.py "pohlheim_geschuetzt" --recursive

# Automatische Suche nach Standardverzeichnissen
python pdfconvert.py
```

## 📁 Ausgabe

- **Original-PDFs:** Bleiben unverändert
- **OCR-PDFs:** Werden als `ocr_<originalname>.pdf` gespeichert
- **Logs:** Detaillierte Verarbeitungsinformationen

## 🔧 Funktionsweise

1. **Text-Erkennung:** Prüft mit `pdfplumber`, ob PDFs bereits Text enthalten
2. **Bild-Konvertierung:** Konvertiert PDF-Seiten in hochauflösende Bilder (300 DPI)
3. **OCR-Verarbeitung:** Wendet Tesseract OCR mit deutscher Sprachunterstützung an
4. **PDF-Erstellung:** Erstellt neue PDFs mit durchsuchbarer Textschicht

## 📊 Statistiken

Das Tool zeigt nach der Verarbeitung:
- **Gesamt PDFs gefunden:** Anzahl aller gefundenen PDFs
- **Übersprungen:** PDFs mit bereits vorhandenem Text
- **Erfolgreich OCR-bearbeitet:** Erfolgreich verarbeitete PDFs
- **Fehler:** Fehlgeschlagene Verarbeitungen

## 🐛 Fehlerbehebung

### Häufige Probleme

1. **"Tesseract not found"**
   - Lösung: Tesseract installieren und PATH konfigurieren

2. **"Poppler not found"**
   - Lösung: Poppler installieren und PATH konfigurieren

3. **"Permission denied"**
   - Lösung: Schreibrechte für das Ausgabeverzeichnis prüfen

### Debug-Modus

```bash
# Erhöhte Ausführlichkeit
python pdfconvert.py --verbose
```

## 🔒 Sicherheit

- **Keine Originaländerung:** Original-PDFs bleiben unverändert
- **Backup-Strategie:** OCR-PDFs werden mit `ocr_` Präfix gespeichert
- **Fehlerbehandlung:** Robuste Fehlerbehandlung ohne Datenverlust

## 📝 Hinweise

- **Verarbeitungszeit:** OCR kann je nach PDF-Größe und -Qualität lange dauern
- **Speicherverbrauch:** Hohe DPI-Einstellung benötigt mehr RAM
- **Sprachunterstützung:** Standardmäßig deutsche Sprache (`deu`)

---

**Hinweis:** Dieses Tool ist für die Nachbearbeitung der Session Net Downloads entwickelt.

