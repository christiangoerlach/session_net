class Logger {
  constructor() {
    this.logLevels = {
      DEBUG: 0,
      INFO: 1,
      WARN: 2,
      ERROR: 3,
      SUCCESS: 4
    };
    
    this.currentLevel = this.logLevels.INFO;
  }

  setLevel(level) {
    this.currentLevel = this.logLevels[level.toUpperCase()] || this.logLevels.INFO;
  }

  shouldLog(level) {
    return level >= this.currentLevel;
  }

  formatMessage(level, message, module = '') {
    const timestamp = new Date().toLocaleTimeString('de-DE');
    const modulePrefix = module ? `[${module}] ` : '';
    
    switch (level) {
      case this.logLevels.DEBUG:
        return `🔍 ${timestamp} ${modulePrefix}${message}`;
      case this.logLevels.INFO:
        return `📋 ${timestamp} ${modulePrefix}${message}`;
      case this.logLevels.WARN:
        return `⚠️ ${timestamp} ${modulePrefix}${message}`;
      case this.logLevels.ERROR:
        return `❌ ${timestamp} ${modulePrefix}${message}`;
      case this.logLevels.SUCCESS:
        return `✅ ${timestamp} ${modulePrefix}${message}`;
      default:
        return `${timestamp} ${modulePrefix}${message}`;
    }
  }

  debug(message, module = '') {
    if (this.shouldLog(this.logLevels.DEBUG)) {
      console.log(this.formatMessage(this.logLevels.DEBUG, message, module));
    }
  }

  info(message, module = '') {
    if (this.shouldLog(this.logLevels.INFO)) {
      console.log(this.formatMessage(this.logLevels.INFO, message, module));
    }
  }

  warn(message, module = '') {
    if (this.shouldLog(this.logLevels.WARN)) {
      console.log(this.formatMessage(this.logLevels.WARN, message, module));
    }
  }

  error(message, module = '') {
    if (this.shouldLog(this.logLevels.ERROR)) {
      console.log(this.formatMessage(this.logLevels.ERROR, message, module));
    }
  }

  success(message, module = '') {
    if (this.shouldLog(this.logLevels.SUCCESS)) {
      console.log(this.formatMessage(this.logLevels.SUCCESS, message, module));
    }
  }

  // Spezielle Logging-Methoden für Downloads
  downloadStart(dokumentName, module = '') {
    this.info(`Lade Dokument herunter: ${dokumentName}`, module);
  }

  downloadSuccess(dokumentName, module = '') {
    this.success(`Download erfolgreich abgeschlossen: ${dokumentName}`, module);
  }

  downloadError(dokumentName, error, module = '') {
    this.error(`Download-Fehler: ${dokumentName} - ${error}`, module);
  }

  downloadTimeout(dokumentName, module = '') {
    this.warn(`Download-Timeout nach 10 Sekunden: ${dokumentName}`, module);
  }

  downloadAborted(dokumentName, module = '') {
    this.warn(`Download abgebrochen - Timeout erreicht: ${dokumentName}`, module);
  }

  // Spezielle Logging-Methoden für Dokumente
  documentsFound(count, module = '') {
    this.info(`${count} Dokumente mit Download-Tooltip gefunden`, module);
  }

  topDocumentsFound(count, module = '') {
    this.info(`${count} Dokumente auf TOP-Seite gefunden`, module);
  }

  // Spezielle Logging-Methoden für Dateien
  fileTooLarge(dokumentName, fileSizeInMB, module = '') {
    this.warn(`Dokument zu groß (${fileSizeInMB} MB > 10 MB) - Überspringe Download: ${dokumentName}`, module);
  }

  fileSaved(filePath, module = '') {
    this.success(`Dokument gespeichert: ${filePath}`, module);
  }

  // Spezielle Logging-Methoden für Content-Types
  contentTypeReceived(contentType, module = '') {
    this.info(`Content-Type: ${contentType}`, module);
  }

  notPdfReceived(contentType, module = '') {
    this.warn(`Kein PDF erhalten: ${contentType}`, module);
  }

  // Spezielle Logging-Methoden für Dateigrößen
  fileSizeInfo(fileSizeInKB, fileSizeInMB, module = '') {
    this.info(`Dateigröße: ${fileSizeInKB} KB (${fileSizeInMB} MB)`, module);
  }

  fileSizeUnknown(module = '') {
    this.info(`Dateigröße: Unbekannt (kein Content-Length Header)`, module);
  }

  // Spezielle Logging-Methoden für Fehler
  documentError(index, error, module = '') {
    this.warn(`Fehler bei Dokument ${index}: ${error}`, module);
  }

  topDocumentError(index, error, module = '') {
    this.warn(`Fehler bei TOP-Dokument ${index}: ${error}`, module);
  }

  downloadError(message, module = '') {
    this.error(`Fehler beim Herunterladen der Dokumente: ${message}`, module);
  }

  topDownloadError(message, module = '') {
    this.error(`Fehler beim Herunterladen der TOP-Dokumente: ${message}`, module);
  }
}

module.exports = Logger;
