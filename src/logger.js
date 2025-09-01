const fs = require('fs');
const path = require('path');

class Logger {
  constructor(logFilePath = 'application.log', options = {}) {
    this.logFilePath = logFilePath;
    this.level = options.level || 'info'; // debug, info, warn, error
    this.consoleOutput = options.consoleOutput !== false; // Standard: true
    this.fileOutput = options.fileOutput !== false; // Standard: true
    this.maxFileSize = options.maxFileSize || 10 * 1024 * 1024; // 10MB
    this.maxFiles = options.maxFiles || 5;
    
    this.levels = {
      debug: 0,
      info: 1,
      warn: 2,
      error: 3
    };
    
    this.initializeLogFile();
  }

  initializeLogFile() {
    if (this.fileOutput && !fs.existsSync(this.logFilePath)) {
      const header = `📝 Anwendungs-Log - ${new Date().toLocaleString('de-DE')}\n`;
      const separator = '─'.repeat(80) + '\n';
      fs.writeFileSync(this.logFilePath, header + separator, 'utf8');
    }
  }

  shouldLog(level) {
    return this.levels[level] >= this.levels[this.level];
  }

  formatMessage(level, message, module = '') {
    const timestamp = new Date().toLocaleString('de-DE');
    const modulePrefix = module ? `[${module}] ` : '';
    const levelEmoji = {
      debug: '🔍',
      info: 'ℹ️',
      warn: '⚠️',
      error: '❌'
    };
    
    return `${timestamp} ${levelEmoji[level]} ${level.toUpperCase()} ${modulePrefix}${message}`;
  }

  writeToFile(message) {
    if (!this.fileOutput) return;
    
    try {
      fs.appendFileSync(this.logFilePath, message + '\n', 'utf8');
      this.rotateLogFileIfNeeded();
    } catch (error) {
      console.error('Fehler beim Schreiben ins Log:', error.message);
    }
  }

  writeToConsole(message) {
    if (!this.consoleOutput) return;
    
    console.log(message);
  }

  log(level, message, module = '') {
    if (!this.shouldLog(level)) return;
    
    const formattedMessage = this.formatMessage(level, message, module);
    
    this.writeToConsole(formattedMessage);
    this.writeToFile(formattedMessage);
  }

  debug(message, module = '') {
    this.log('debug', message, module);
  }

  info(message, module = '') {
    this.log('info', message, module);
  }

  warn(message, module = '') {
    this.log('warn', message, module);
  }

  error(message, module = '') {
    this.log('error', message, module);
  }

  // Spezielle Logging-Methoden für das Projekt
  startOperation(operation, module = '') {
    this.info(`🚀 Starte: ${operation}`, module);
  }

  completeOperation(operation, module = '') {
    this.info(`✅ Abgeschlossen: ${operation}`, module);
  }

  skipOperation(operation, reason, module = '') {
    this.info(`⏭️ Überspringe: ${operation} - ${reason}`, module);
  }

  downloadProgress(current, total, fileName, module = '') {
    const percentage = Math.round((current / total) * 100);
    this.info(`📥 Download: ${fileName} - ${percentage}% (${current}/${total})`, module);
  }

  navigationProgress(current, total, url, module = '') {
    this.info(`🌐 Navigation: ${current}/${total} - ${url}`, module);
  }

  memoryUsage(module = '') {
    const memUsage = process.memoryUsage();
    const usedMB = Math.round(memUsage.heapUsed / 1024 / 1024);
    const totalMB = Math.round(memUsage.heapTotal / 1024 / 1024);
    this.debug(`🧠 Speicher: ${usedMB}MB / ${totalMB}MB`, module);
  }

  // Log-Datei rotieren wenn zu groß
  rotateLogFileIfNeeded() {
    try {
      const stats = fs.statSync(this.logFilePath);
      if (stats.size > this.maxFileSize) {
        this.rotateLogFile();
      }
    } catch (error) {
      // Datei existiert nicht oder andere Fehler - ignorieren
    }
  }

  rotateLogFile() {
    try {
      // Bestehende Log-Dateien verschieben
      for (let i = this.maxFiles - 1; i >= 1; i--) {
        const oldFile = `${this.logFilePath}.${i}`;
        const newFile = `${this.logFilePath}.${i + 1}`;
        
        if (fs.existsSync(oldFile)) {
          if (i === this.maxFiles - 1) {
            fs.unlinkSync(oldFile); // Älteste Datei löschen
          } else {
            fs.renameSync(oldFile, newFile);
          }
        }
      }
      
      // Aktuelle Log-Datei verschieben
      const backupFile = `${this.logFilePath}.1`;
      fs.renameSync(this.logFilePath, backupFile);
      
      // Neue Log-Datei erstellen
      this.initializeLogFile();
      
      this.info(`📝 Log-Datei rotiert: ${backupFile} erstellt`);
    } catch (error) {
      console.error('Fehler beim Rotieren der Log-Datei:', error.message);
    }
  }

  // Log-Statistiken
  getLogStats() {
    try {
      const logContent = fs.readFileSync(this.logFilePath, 'utf8');
      const lines = logContent.split('\n').filter(line => line.trim() && !line.startsWith('─') && !line.startsWith('📝'));
      
      const stats = {
        total: lines.length,
        byLevel: {},
        byModule: {},
        recent: lines.slice(-20) // Letzte 20 Einträge
      };
      
      lines.forEach(line => {
        const parts = line.split(' ');
        if (parts.length >= 4) {
          const level = parts[2];
          const moduleMatch = line.match(/\[([^\]]+)\]/);
          const module = moduleMatch ? moduleMatch[1] : 'Unknown';
          
          stats.byLevel[level] = (stats.byLevel[level] || 0) + 1;
          stats.byModule[module] = (stats.byModule[module] || 0) + 1;
        }
      });
      
      return stats;
    } catch (error) {
      console.error('Fehler beim Lesen der Log-Statistiken:', error.message);
      return { total: 0, byLevel: {}, byModule: {}, recent: [] };
    }
  }

  // Log-Datei bereinigen
  cleanupLog(maxAge = 30) { // Tage
    try {
      const logContent = fs.readFileSync(this.logFilePath, 'utf8');
      const lines = logContent.split('\n');
      const headerLines = lines.slice(0, 2); // Header beibehalten
      const dataLines = lines.slice(2);
      
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - maxAge);
      
      const filteredLines = dataLines.filter(line => {
        if (!line.trim()) return false;
        
        const parts = line.split(' ');
        if (parts.length < 2) return false;
        
        const dateStr = parts[0] + ' ' + parts[1];
        const lineDate = new Date(dateStr);
        
        return lineDate >= cutoffDate;
      });
      
      const newContent = headerLines.join('\n') + '\n' + filteredLines.join('\n');
      fs.writeFileSync(this.logFilePath, newContent, 'utf8');
      
      this.info(`🧹 Log bereinigt: ${dataLines.length - filteredLines.length} alte Einträge entfernt`);
    } catch (error) {
      console.error('Fehler beim Bereinigen des Logs:', error.message);
    }
  }

  // Log-Level ändern
  setLevel(level) {
    if (this.levels.hasOwnProperty(level)) {
      this.level = level;
      this.info(`Log-Level auf ${level} gesetzt`);
    } else {
      this.warn(`Ungültiges Log-Level: ${level}`);
    }
  }

  // Temporäres Log-Level für eine Operation
  async withLevel(level, operation) {
    const originalLevel = this.level;
    this.setLevel(level);
    
    try {
      return await operation();
    } finally {
      this.setLevel(originalLevel);
    }
  }
}

// Singleton-Instanz für einfache Verwendung
let globalLogger = null;

function getLogger(options = {}) {
  if (!globalLogger) {
    globalLogger = new Logger(options.logFilePath, options);
  }
  return globalLogger;
}

module.exports = { Logger, getLogger };
