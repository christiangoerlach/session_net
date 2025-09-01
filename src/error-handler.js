const fs = require('fs');
const path = require('path');

class ErrorHandler {
  constructor(errorLogPath = 'error_log.txt') {
    this.errorLogPath = errorLogPath;
    this.initializeErrorLog();
  }

  initializeErrorLog() {
    if (!fs.existsSync(this.errorLogPath)) {
      const header = `🚨 Fehler-Log - ${new Date().toLocaleString('de-DE')}\n`;
      const separator = '─'.repeat(80) + '\n';
      const columns = `Datum/Zeit | Modul | Operation | Fehler | Details\n`;
      const columnSeparator = '─'.repeat(80) + '\n';
      fs.writeFileSync(this.errorLogPath, header + separator + columns + columnSeparator, 'utf8');
    }
  }

  logError(module, operation, error, details = '') {
    const timestamp = new Date().toLocaleString('de-DE');
    const errorMessage = error.message || error.toString();
    const entry = `${timestamp} | ${module} | ${operation} | ${errorMessage} | ${details}\n`;
    
    try {
      fs.appendFileSync(this.errorLogPath, entry, 'utf8');
    } catch (logError) {
      console.error('❌ Fehler beim Schreiben ins Fehler-Log:', logError.message);
    }
    
    console.error(`❌ [${module}] ${operation}: ${errorMessage}`);
  }

  handleError(error, module, operation, details = '') {
    this.logError(module, operation, error, details);
    
    // Spezifische Fehlerbehandlung basierend auf Fehlertyp
    if (error.name === 'TimeoutError') {
      console.log('⏰ Timeout-Fehler - Versuche erneut...');
      return { retry: true, delay: 5000 };
    }
    
    if (error.message.includes('net::ERR_CONNECTION_REFUSED')) {
      console.log('🌐 Verbindungsfehler - Prüfe Internetverbindung...');
      return { retry: true, delay: 10000 };
    }
    
    if (error.message.includes('net::ERR_NAME_NOT_RESOLVED')) {
      console.log('🌐 DNS-Fehler - Prüfe URL...');
      return { retry: false, critical: true };
    }
    
    if (error.message.includes('net::ERR_EMPTY_RESPONSE')) {
      console.log('🌐 Leere Antwort vom Server - Versuche erneut...');
      return { retry: true, delay: 3000 };
    }
    
    // Standard-Fehlerbehandlung
    return { retry: false, critical: false };
  }

  async retryOperation(operation, maxRetries = 3, delay = 1000) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        const errorInfo = this.handleError(error, 'RetryManager', `Versuch ${attempt}/${maxRetries}`);
        
        if (errorInfo.critical) {
          throw error;
        }
        
        if (!errorInfo.retry || attempt === maxRetries) {
          throw error;
        }
        
        console.log(`🔄 Wiederholung in ${delay}ms... (${attempt}/${maxRetries})`);
        await this.sleep(delay);
        delay *= 2; // Exponential backoff
      }
    }
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Spezifische Fehlerbehandlung für verschiedene Module
  handleDownloadError(error, fileName, terminName) {
    this.logError('DocumentDownloader', `Download: ${fileName}`, error, `Termin: ${terminName}`);
    return {
      retry: true,
      delay: 2000,
      skipFile: false
    };
  }

  handleNavigationError(error, url) {
    this.logError('Navigation', `Navigation zu: ${url}`, error);
    return {
      retry: true,
      delay: 3000,
      skipPage: false
    };
  }

  handleLoginError(error) {
    this.logError('AuthManager', 'Login', error);
    return {
      retry: false,
      critical: true,
      message: 'Login fehlgeschlagen - Prüfe Anmeldedaten'
    };
  }

  handleSelectorError(error, selector, context) {
    this.logError('Selector', `Selektor: ${selector}`, error, `Kontext: ${context}`);
    return {
      retry: false,
      skipSelector: true,
      message: `Selektor nicht gefunden: ${selector}`
    };
  }

  // Fehlerstatistiken
  getErrorStats() {
    try {
      const logContent = fs.readFileSync(this.errorLogPath, 'utf8');
      const lines = logContent.split('\n').filter(line => line.trim() && !line.startsWith('─') && !line.startsWith('🚨') && !line.startsWith('Datum'));
      
      const stats = {
        total: lines.length,
        byModule: {},
        byType: {},
        recent: lines.slice(-10) // Letzte 10 Fehler
      };
      
      lines.forEach(line => {
        const parts = line.split(' | ');
        if (parts.length >= 4) {
          const module = parts[1].trim();
          const error = parts[3].trim();
          
          stats.byModule[module] = (stats.byModule[module] || 0) + 1;
          
          // Fehlertyp kategorisieren
          let errorType = 'Unknown';
          if (error.includes('Timeout')) errorType = 'Timeout';
          else if (error.includes('Connection')) errorType = 'Connection';
          else if (error.includes('Selector')) errorType = 'Selector';
          else if (error.includes('Download')) errorType = 'Download';
          else if (error.includes('Navigation')) errorType = 'Navigation';
          
          stats.byType[errorType] = (stats.byType[errorType] || 0) + 1;
        }
      });
      
      return stats;
    } catch (error) {
      console.error('Fehler beim Lesen der Fehlerstatistiken:', error.message);
      return { total: 0, byModule: {}, byType: {}, recent: [] };
    }
  }

  // Fehler-Log bereinigen
  cleanupErrorLog(maxAge = 30) { // Tage
    try {
      const logContent = fs.readFileSync(this.errorLogPath, 'utf8');
      const lines = logContent.split('\n');
      const headerLines = lines.slice(0, 4); // Header beibehalten
      const dataLines = lines.slice(4);
      
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - maxAge);
      
      const filteredLines = dataLines.filter(line => {
        if (!line.trim()) return false;
        
        const parts = line.split(' | ');
        if (parts.length < 1) return false;
        
        const dateStr = parts[0].trim();
        const lineDate = new Date(dateStr);
        
        return lineDate >= cutoffDate;
      });
      
      const newContent = headerLines.join('\n') + '\n' + filteredLines.join('\n');
      fs.writeFileSync(this.errorLogPath, newContent, 'utf8');
      
      console.log(`🧹 Fehler-Log bereinigt: ${dataLines.length - filteredLines.length} alte Einträge entfernt`);
    } catch (error) {
      console.error('Fehler beim Bereinigen des Fehler-Logs:', error.message);
    }
  }
}

module.exports = ErrorHandler;
