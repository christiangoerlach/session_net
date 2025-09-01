const path = require('path');

class TimeoutManager {
  constructor() {
    this.timeoutDuration = 10000; // 10 Sekunden
  }

  async downloadWithTimeout(url, filePath, dokumentName, terminOrdnerName, playwrightDownloader, fileManager, topInfo = null, logInfo = null) {
    return new Promise(async (resolve, reject) => {
      let timeoutId = null;
      let downloadCompleted = false;
      let downloadAborted = false;
      let abortController = null;
      
      // Timeout-Timer (10 Sekunden) - startet SOFORT für JEDES Dokument neu
      timeoutId = setTimeout(() => {
        if (!downloadCompleted) {
          console.log(`        ⏰ Download-Timeout nach 10 Sekunden: ${dokumentName}`);
          
          // Logge Timeout wenn LogInfo verfügbar
          if (logInfo) {
            logInfo.logTimeout(logInfo, 'Download', this.timeoutDuration);
          }
          
          // Fehlgeschlagenen Download protokollieren
          const month = this.extractMonthFromPath(filePath);
          fileManager.logFailedDownload(month, terminOrdnerName, topInfo, dokumentName, 'Download-Timeout nach 10 Sekunden');
          
          downloadCompleted = true;
          downloadAborted = true;
          
          // AbortController signalisieren um laufende Downloads zu stoppen
          if (abortController) {
            abortController.abort();
          }
          
          // Speicher freigeben bei Timeout
          console.log(`        🔍 TimeoutManager: Prüfe global.gc...`);
          if (logInfo) {
            logInfo.addLogEntry(logInfo, 'DEBUG', '🔍 TimeoutManager: Prüfe global.gc...');
          }
          
          if (global.gc) {
            console.log(`        🔍 TimeoutManager: global.gc verfügbar, führe Garbage Collection durch...`);
            if (logInfo) {
              logInfo.addLogEntry(logInfo, 'DEBUG', '🔍 TimeoutManager: global.gc verfügbar, führe Garbage Collection durch...');
            }
            
            const beforeMemory = process.memoryUsage();
            console.log(`        🔍 TimeoutManager: Speicher vor GC: ${JSON.stringify(beforeMemory)}`);
            if (logInfo) {
              logInfo.addLogEntry(logInfo, 'DEBUG', `🔍 TimeoutManager: Speicher vor GC: ${JSON.stringify(beforeMemory)}`);
            }
            
            global.gc();
            
            const afterMemory = process.memoryUsage();
            console.log(`        🔍 TimeoutManager: Speicher nach GC: ${JSON.stringify(afterMemory)}`);
            if (logInfo) {
              logInfo.addLogEntry(logInfo, 'DEBUG', `🔍 TimeoutManager: Speicher nach GC: ${JSON.stringify(afterMemory)}`);
            }
            
            // Logge Garbage Collection wenn logInfo verfügbar
            console.log(`        🔍 TimeoutManager: Prüfe logInfo...`);
            if (logInfo) {
              logInfo.addLogEntry(logInfo, 'DEBUG', '🔍 TimeoutManager: Prüfe logInfo...');
              console.log(`        🔍 TimeoutManager: logInfo verfügbar, logge Garbage Collection...`);
              logInfo.addLogEntry(logInfo, 'DEBUG', '🔍 TimeoutManager: logInfo verfügbar, logge Garbage Collection...');
              try {
                logInfo.logGarbageCollection(logInfo, beforeMemory, afterMemory);
                console.log(`        ✅ TimeoutManager: Garbage Collection erfolgreich geloggt`);
                logInfo.addLogEntry(logInfo, 'DEBUG', '✅ TimeoutManager: Garbage Collection erfolgreich geloggt');
              } catch (logError) {
                console.log(`        ❌ TimeoutManager: Fehler beim Loggen der Garbage Collection: ${logError.message}`);
                logInfo.addLogEntry(logInfo, 'ERROR', `❌ TimeoutManager: Fehler beim Loggen der Garbage Collection: ${logError.message}`);
              }
            } else {
              console.log(`        ⚠️ TimeoutManager: logInfo nicht verfügbar`);
            }
          } else {
            console.log(`        ⚠️ TimeoutManager: global.gc nicht verfügbar`);
            if (logInfo) {
              logInfo.addLogEntry(logInfo, 'WARN', '⚠️ TimeoutManager: global.gc nicht verfügbar');
            }
          }
          
          // Prozess-Status nach Timeout prüfen
          console.log(`        🔍 TimeoutManager: Prüfe Prozess-Status nach Timeout...`);
          if (logInfo) {
            logInfo.addLogEntry(logInfo, 'DEBUG', '🔍 TimeoutManager: Prüfe Prozess-Status nach Timeout...');
          }
          
          // Prüfe ob Download-Prozess noch aktiv ist
          const processStatus = this.checkProcessStatus();
          console.log(`        🔍 TimeoutManager: Prozess-Status: ${JSON.stringify(processStatus)}`);
          if (logInfo) {
            logInfo.addLogEntry(logInfo, 'DEBUG', `🔍 TimeoutManager: Prozess-Status: ${JSON.stringify(processStatus)}`);
          }
          
          // Speicherverwendung nach Timeout prüfen
          const memoryAfterTimeout = process.memoryUsage();
          console.log(`        🔍 TimeoutManager: Speicher nach Timeout: ${JSON.stringify(memoryAfterTimeout)}`);
          if (logInfo) {
            logInfo.addLogEntry(logInfo, 'DEBUG', `🔍 TimeoutManager: Speicher nach Timeout: ${JSON.stringify(memoryAfterTimeout)}`);
          }
          
          // Bei Timeout einen Fehler werfen, damit der DocumentDownloader das abfangen kann
          reject(new Error('Download-Timeout nach 10 Sekunden'));
        }
      }, this.timeoutDuration);

      // Timeout-Check-Funktion für Download-Methoden
      const timeoutCheck = () => downloadAborted;

      try {
        // Prüfe ob Timeout bereits abgelaufen ist VOR dem Download
        if (downloadAborted) {
          return; // Download bereits durch Timeout abgebrochen
        }
        
        // AbortController für echte Download-Abbrüche erstellen
        abortController = new AbortController();
        
                 // Nur Playwright-Download verwenden
         const downloadSuccess = await playwrightDownloader.download(url, filePath, dokumentName, terminOrdnerName, timeoutCheck, abortController, logInfo);
        
        if (!downloadAborted) {
          // Download abgeschlossen (erfolgreich oder fehlgeschlagen)
          clearTimeout(timeoutId);
          downloadCompleted = true;
          
          // Manuelle Garbage Collection nach jedem Download
          if (global.gc) {
            global.gc();
          }
          
          resolve();
        }
        
      } catch (error) {
        if (!downloadAborted) {
          clearTimeout(timeoutId);
          downloadCompleted = true;
          
          // Fehlgeschlagenen Download protokollieren bei anderen Fehlern
          const month = this.extractMonthFromPath(filePath);
          fileManager.logFailedDownload(month, terminOrdnerName, topInfo, dokumentName, error.message);
          
          // Manuelle Garbage Collection auch bei Fehlern
          if (global.gc) {
            global.gc();
          }
          
          reject(error);
        } else {
          // Bei Timeout: Fehler weiterleiten
          console.log(`        ⏰ Download durch Timeout abgebrochen: ${dokumentName}`);
          reject(error);
        }
      }
    });
  }

  extractMonthFromPath(filePath) {
    const pathParts = filePath.split(path.sep);
    // Suche nach dem Monat-Ordner (z.B. Kalender_2025_August)
    for (let i = pathParts.length - 1; i >= 0; i--) {
      if (pathParts[i].includes('Kalender_')) {
        return pathParts[i];
      }
    }
    return 'Unbekannt';
  }

  setTimeoutDuration(duration) {
    this.timeoutDuration = duration;
  }

  getTimeoutDuration() {
    return this.timeoutDuration;
  }

  /**
   * Prüft den aktuellen Prozess-Status nach einem Timeout
   */
  checkProcessStatus() {
    const status = {
      timestamp: new Date().toISOString(),
      pid: process.pid,
      uptime: process.uptime(),
      memoryUsage: process.memoryUsage(),
      cpuUsage: process.cpuUsage(),
      activeHandles: process._getActiveHandles ? process._getActiveHandles().length : 'Nicht verfügbar',
      activeRequests: process._getActiveRequests ? process._getActiveRequests().length : 'Nicht verfügbar',
      eventLoopDelay: this.measureEventLoopDelay(),
      downloadProcessActive: this.isDownloadProcessActive()
    };
    
    return status;
  }

  /**
   * Misst die Event-Loop-Verzögerung
   */
  measureEventLoopDelay() {
    const start = process.hrtime.bigint();
    // Kurze Verzögerung simulieren
    const end = process.hrtime.bigint();
    return Number(end - start) / 1000000; // In Millisekunden
  }

  /**
   * Prüft ob der Download-Prozess noch aktiv ist
   */
  isDownloadProcessActive() {
    try {
      // Prüfe ob es aktive Timer gibt
      const activeTimers = process._getActiveHandles ? 
        process._getActiveHandles().filter(handle => handle.constructor.name === 'Timeout').length : 0;
      
      // Prüfe ob es aktive Promises gibt
      const activePromises = process._getActiveHandles ? 
        process._getActiveHandles().filter(handle => handle.constructor.name === 'Promise').length : 0;
      
      // Prüfe ob es aktive HTTP-Requests gibt
      const activeRequests = process._getActiveHandles ? 
        process._getActiveHandles().filter(handle => 
          handle.constructor.name === 'Socket' || 
          handle.constructor.name === 'ServerResponse' ||
          handle.constructor.name === 'IncomingMessage'
        ).length : 0;
      
      return {
        activeTimers,
        activePromises,
        activeRequests,
        hasActiveProcesses: (activeTimers > 0 || activePromises > 0 || activeRequests > 0)
      };
    } catch (error) {
      return {
        error: error.message,
        hasActiveProcesses: 'Unbekannt'
      };
    }
  }
}

module.exports = TimeoutManager;
