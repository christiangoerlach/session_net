const fs = require('fs');
const path = require('path');

class DownloadLogger {
  constructor() {
    this.logsDir = 'download_logs';
    this.ensureLogsDirectory();
  }

  ensureLogsDirectory() {
    if (!fs.existsSync(this.logsDir)) {
      fs.mkdirSync(this.logsDir, { recursive: true });
    }
  }

  /**
   * Erstellt eine eindeutige Log-Datei für ein spezifisches Dokument
   */
  createDocumentLog(dokumentName, terminOrdnerName, topInfo = null) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const cleanDocName = this.sanitizeFileName(dokumentName);
    const topSuffix = topInfo ? `_TOP${topInfo.topNumber}_${this.sanitizeFileName(topInfo.topName)}` : '';
    const logFileName = `${timestamp}_${this.sanitizeFileName(terminOrdnerName)}${topSuffix}_${cleanDocName}.log`;
    const logFilePath = path.join(this.logsDir, logFileName);
    
    const logInfo = {
      filePath: logFilePath,
      fileName: logFileName,
      startTime: new Date(),
      entries: []
    };
    
    // Füge Logger-Methoden direkt zum logInfo-Objekt hinzu
    logInfo.logFunctionCall = (logInfo, functionName, parameters) => this.logFunctionCall(logInfo, functionName, parameters);
    logInfo.logFunctionResult = (logInfo, functionName, result, duration) => this.logFunctionResult(logInfo, functionName, result, duration);
    logInfo.logHttpRequest = (logInfo, url, headers, method) => this.logHttpRequest(logInfo, url, headers, method);
    logInfo.logHttpResponse = (logInfo, statusCode, headers, contentLength) => this.logHttpResponse(logInfo, statusCode, headers, contentLength);
    logInfo.logTimeout = (logInfo, timeoutType, duration) => this.logTimeout(logInfo, timeoutType, duration);
    logInfo.logError = (logInfo, error, context) => this.logError(logInfo, error, context);
    logInfo.logMemoryUsage = (logInfo) => this.logMemoryUsage(logInfo);
    logInfo.logFileOperation = (logInfo, operation, filePath, result) => this.logFileOperation(logInfo, operation, filePath, result);
    logInfo.logDownloadSuccess = (logInfo, fileSize, duration) => this.logDownloadSuccess(logInfo, fileSize, duration);
    logInfo.logDownloadFailure = (logInfo, reason, duration) => this.logDownloadFailure(logInfo, reason, duration);
    logInfo.logGarbageCollection = (logInfo, beforeMemory, afterMemory) => this.logGarbageCollection(logInfo, beforeMemory, afterMemory);
    logInfo.logAbortEvent = (logInfo, reason) => this.logAbortEvent(logInfo, reason);
    logInfo.logContentValidation = (logInfo, contentType, isValid, expectedType) => this.logContentValidation(logInfo, contentType, isValid, expectedType);
    logInfo.logFileSizeCheck = (logInfo, fileSize, maxSize, isTooLarge) => this.logFileSizeCheck(logInfo, fileSize, maxSize, isTooLarge);
    logInfo.addLogEntry = (logInfo, level, message, data) => this.addLogEntry(logInfo, level, message, data);
    
    return logInfo;
  }

  /**
   * Fügt einen Log-Eintrag hinzu
   */
  addLogEntry(logInfo, level, message, data = null) {
    const timestamp = new Date().toISOString();
    const entry = {
      timestamp,
      level,
      message,
      data,
      elapsedMs: logInfo.startTime ? Date.now() - logInfo.startTime.getTime() : 0
    };
    
    logInfo.entries.push(entry);
    
    // Sofort in Datei schreiben
    const logLine = this.formatLogEntry(entry);
    fs.appendFileSync(logInfo.filePath, logLine + '\n');
    
    return entry;
  }

  /**
   * Formatiert einen Log-Eintrag für die Datei
   */
  formatLogEntry(entry) {
    const elapsedStr = entry.elapsedMs > 0 ? ` [+${entry.elapsedMs}ms]` : '';
    const dataStr = entry.data ? ` | DATA: ${JSON.stringify(entry.data)}` : '';
    return `[${entry.timestamp}]${elapsedStr} [${entry.level}] ${entry.message}${dataStr}`;
  }

  /**
   * Loggt den Start eines Downloads
   */
  logDownloadStart(logInfo, dokumentName, downloadUrl, filePath, terminOrdnerName, topInfo = null) {
    const data = {
      dokumentName,
      downloadUrl,
      filePath,
      terminOrdnerName,
      topInfo,
      systemInfo: {
        nodeVersion: process.version,
        platform: process.platform,
        arch: process.arch,
        memoryUsage: process.memoryUsage(),
        uptime: process.uptime()
      }
    };
    
    this.addLogEntry(logInfo, 'INFO', '=== DOWNLOAD START ===', data);
    this.addLogEntry(logInfo, 'INFO', `Dokument: ${dokumentName}`);
    this.addLogEntry(logInfo, 'INFO', `Download URL: ${downloadUrl}`);
    this.addLogEntry(logInfo, 'INFO', `Zieldatei: ${filePath}`);
    this.addLogEntry(logInfo, 'INFO', `Termin: ${terminOrdnerName}`);
    if (topInfo) {
      this.addLogEntry(logInfo, 'INFO', `TOP: ${topInfo.topNumber} - ${topInfo.topName}`);
    }
  }

  /**
   * Loggt Funktionsaufrufe
   */
  logFunctionCall(logInfo, functionName, parameters = {}) {
    this.addLogEntry(logInfo, 'DEBUG', `FUNKTION: ${functionName} aufgerufen`, parameters);
  }

  /**
   * Loggt Funktionsergebnisse
   */
  logFunctionResult(logInfo, functionName, result, duration = null) {
    const data = { result, duration };
    this.addLogEntry(logInfo, 'DEBUG', `FUNKTION: ${functionName} abgeschlossen`, data);
  }

  /**
   * Loggt HTTP-Request Details
   */
  logHttpRequest(logInfo, url, headers = {}, method = 'GET') {
    const data = { url, method, headers };
    this.addLogEntry(logInfo, 'DEBUG', 'HTTP-REQUEST gestartet', data);
  }

  /**
   * Loggt HTTP-Response Details
   */
  logHttpResponse(logInfo, statusCode, headers = {}, contentLength = null) {
    const data = { statusCode, headers, contentLength };
    this.addLogEntry(logInfo, 'DEBUG', 'HTTP-RESPONSE erhalten', data);
  }

  /**
   * Loggt Timeout-Ereignisse
   */
  logTimeout(logInfo, timeoutType, duration) {
    const data = { timeoutType, duration };
    this.addLogEntry(logInfo, 'WARN', `TIMEOUT: ${timeoutType} nach ${duration}ms`, data);
  }

  /**
   * Loggt Fehler
   */
  logError(logInfo, error, context = '') {
    const data = {
      error: {
        message: error.message,
        stack: error.stack,
        name: error.name
      },
      context
    };
    this.addLogEntry(logInfo, 'ERROR', `FEHLER: ${error.message}`, data);
  }

  /**
   * Loggt Speicherverwendung
   */
  logMemoryUsage(logInfo) {
    const memoryUsage = process.memoryUsage();
    this.addLogEntry(logInfo, 'DEBUG', 'Speicherverwendung', memoryUsage);
  }

  /**
   * Loggt Dateioperationen
   */
  logFileOperation(logInfo, operation, filePath, result = null) {
    const data = { operation, filePath, result };
    this.addLogEntry(logInfo, 'DEBUG', `DATEIOPERATION: ${operation}`, data);
  }

  /**
   * Loggt den erfolgreichen Abschluss eines Downloads
   */
  logDownloadSuccess(logInfo, fileSize = null, duration = null) {
    const data = { fileSize, duration };
    this.addLogEntry(logInfo, 'SUCCESS', '=== DOWNLOAD ERFOLGREICH ===', data);
    this.addLogEntry(logInfo, 'INFO', `Gesamtdauer: ${duration}ms`);
    if (fileSize) {
      this.addLogEntry(logInfo, 'INFO', `Dateigröße: ${fileSize} Bytes`);
    }
  }

  /**
   * Loggt den fehlgeschlagenen Abschluss eines Downloads
   */
  logDownloadFailure(logInfo, reason, duration = null) {
    const data = { reason, duration };
    this.addLogEntry(logInfo, 'ERROR', '=== DOWNLOAD FEHLGESCHLAGEN ===', data);
    this.addLogEntry(logInfo, 'ERROR', `Grund: ${reason}`);
    if (duration) {
      this.addLogEntry(logInfo, 'INFO', `Gesamtdauer: ${duration}ms`);
    }
  }

  /**
   * Loggt Garbage Collection
   */
  logGarbageCollection(logInfo, beforeMemory, afterMemory) {
    const data = {
      beforeMemory,
      afterMemory,
      freed: {
        rss: beforeMemory.rss - afterMemory.rss,
        heapUsed: beforeMemory.heapUsed - afterMemory.heapUsed,
        heapTotal: beforeMemory.heapTotal - afterMemory.heapTotal,
        external: beforeMemory.external - afterMemory.external
      }
    };
    this.addLogEntry(logInfo, 'DEBUG', 'GARBAGE COLLECTION durchgeführt', data);
  }

  /**
   * Loggt AbortController-Ereignisse
   */
  logAbortEvent(logInfo, reason) {
    this.addLogEntry(logInfo, 'WARN', `ABORT: ${reason}`);
  }

  /**
   * Loggt Content-Type und Validierung
   */
  logContentValidation(logInfo, contentType, isValid, expectedType = 'application/pdf') {
    const data = { contentType, isValid, expectedType };
    this.addLogEntry(logInfo, 'DEBUG', `CONTENT-VALIDATION: ${isValid ? 'ERFOLGREICH' : 'FEHLGESCHLAGEN'}`, data);
  }

  /**
   * Loggt Dateigrößenprüfung
   */
  logFileSizeCheck(logInfo, fileSize, maxSize, isTooLarge) {
    const data = { fileSize, maxSize, isTooLarge };
    this.addLogEntry(logInfo, 'DEBUG', `DATEIGRÖSSE-PRÜFUNG: ${isTooLarge ? 'ZU GROSS' : 'OK'}`, data);
  }

  /**
   * Bereinigt Dateinamen für Log-Dateien
   */
  sanitizeFileName(fileName) {
    return fileName
      .replace(/[<>:"/\\|?*]/g, '_')
      .replace(/\s+/g, '_')
      .substring(0, 50);
  }

  /**
   * Erstellt eine Zusammenfassung aller Logs
   */
  createSummary() {
    const summaryFile = path.join(this.logsDir, 'download_summary.log');
    const timestamp = new Date().toISOString();
    
    let summary = `=== DOWNLOAD SUMMARY ===\n`;
    summary += `Erstellt: ${timestamp}\n`;
    summary += `Logs-Verzeichnis: ${this.logsDir}\n\n`;
    
    try {
      const logFiles = fs.readdirSync(this.logsDir)
        .filter(file => file.endsWith('.log') && file !== 'download_summary.log')
        .sort();
      
      summary += `Gefundene Log-Dateien: ${logFiles.length}\n\n`;
      
      for (const logFile of logFiles) {
        const logPath = path.join(this.logsDir, logFile);
        const stats = fs.statSync(logPath);
        summary += `- ${logFile} (${stats.size} Bytes, ${stats.mtime.toISOString()})\n`;
      }
      
      fs.writeFileSync(summaryFile, summary);
      return summaryFile;
    } catch (error) {
      console.error('Fehler beim Erstellen der Zusammenfassung:', error);
      return null;
    }
  }
}

module.exports = DownloadLogger;
