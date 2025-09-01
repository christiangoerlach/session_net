const fs = require('fs');
const path = require('path');
const TimeoutManager = require('./timeout-manager');
const PlaywrightDownloader = require('./playwright-downloader');
// HTTP-Downloader entfernt - wird nicht mehr verwendet
const FileManager = require('./file-manager');
const Logger = require('./logger');
const DownloadLogger = require('./download-logger');

class DocumentDownloader {
  constructor(page) {
    this.page = page;
    this.timeoutManager = new TimeoutManager();
    this.playwrightDownloader = new PlaywrightDownloader(page);
    // HTTP-Downloader komplett entfernt
    this.fileManager = new FileManager();
    this.logger = new Logger();
    this.downloadLogger = new DownloadLogger();
    
    // Initialisiere Dateien
    this.fileManager.initializeFiles();
  }

  async downloadDocuments(terminOrdner, terminOrdnerName) {
    this.logger.info('Suche nach Dokumenten...', 'DocumentDownloader');
    
    try {
      // Warte bis die Seite vollständig geladen ist
      await this.page.waitForLoadState('networkidle', { timeout: 10000 });
      
      // Neue Logik: Alle Dokumente auf einmal finden und dann verarbeiten
      this.logger.info(`🔍 Suche alle Dokumente auf der Seite...`, 'DocumentDownloader');
      
      // Verwende verschiedene Selektoren für Dokument-Links
      const documentSelectors = [
        'a[title*="Dokument Download"]',
        'a[aria-label*="Dokument Download"]',
        'a[href*="getfile.asp"]',
        '.smc-downloaded a[href*="getfile.asp"]',
        'a.smc-link-normal[href*="getfile.asp"]'
      ];
      
      let allDocuments = [];
      
      // Durch alle Selektoren gehen und Dokumente sammeln
      for (const selector of documentSelectors) {
        try {
          const documents = await this.page.locator(selector).all();
          this.logger.info(`🔍 Selektor "${selector}": ${documents.length} Dokumente gefunden`, 'DocumentDownloader');
          
          for (const doc of documents) {
            try {
              const docName = await doc.textContent();
              const docLink = await doc.getAttribute('href');
              
              if (docName && docLink && docLink.includes('getfile.asp')) {
                // Prüfe ob das Dokument bereits in der Liste ist
                const exists = allDocuments.find(d => d.name === docName.trim() && d.link === docLink);
                if (!exists) {
                  allDocuments.push({
                    name: docName.trim(),
                    link: docLink,
                    element: doc
                  });
                }
              }
            } catch (e) {
              this.logger.warn(`Fehler beim Extrahieren eines Dokuments: ${e.message}`, 'DocumentDownloader');
            }
          }
          
          // Wenn wir Dokumente gefunden haben, aufhören
          if (allDocuments.length > 0) {
            break;
          }
          
        } catch (e) {
          this.logger.warn(`Fehler mit Selektor "${selector}": ${e.message}`, 'DocumentDownloader');
        }
      }
      
      this.logger.info(`📊 Insgesamt ${allDocuments.length} eindeutige Dokumente gefunden`, 'DocumentDownloader');
      
      // Alle gefundenen Dokumente verarbeiten
      for (let i = 0; i < allDocuments.length; i++) {
        const doc = allDocuments[i];
        this.logger.info(`Verarbeite Dokument ${i + 1}/${allDocuments.length}: ${doc.name}`, 'DocumentDownloader');
        
        try {
          await this.downloadSingleDocument(doc.name, doc.link, terminOrdner, terminOrdnerName);
          
          // Kurz warten vor dem nächsten Dokument
          this.logger.info(`⏱️ Warte 1 Sekunde vor dem nächsten Dokument...`, 'DocumentDownloader');
          await this.page.waitForTimeout(1000);
          
        } catch (error) {
          this.logger.warn(`Fehler bei Dokument ${i + 1}: ${error.message}`, 'DocumentDownloader');
        }
      }
      
    } catch (error) {
      this.logger.error(`Fehler beim Herunterladen der Dokumente: ${error.message}`, 'DocumentDownloader');
    }
  }

    async downloadSingleDocument(dokumentName, downloadLink, terminOrdner, terminOrdnerName) {
    const cleanName = this.fileManager.sanitizeFileName(dokumentName);
    const dokumentPath = this.fileManager.generateUniqueFilePath(terminOrdner, cleanName);
    
    // Erstelle detailliertes Log für dieses Dokument
    const logInfo = this.downloadLogger.createDocumentLog(dokumentName, terminOrdnerName);
    
    this.logger.info(`Lade Dokument herunter: ${dokumentName}`, 'DocumentDownloader');
    
    // PDF-Datei herunterladen
    const downloadUrl = downloadLink.startsWith('http') ? downloadLink : new URL(downloadLink, this.page.url()).href;
    
    // Logge Download-Start
    this.downloadLogger.logDownloadStart(logInfo, dokumentName, downloadUrl, dokumentPath, terminOrdnerName);
    this.downloadLogger.logMemoryUsage(logInfo);
    
    const startTime = Date.now();
    
    try {
      // Stelle sicher, dass Request-Interception aktiv ist
      await this.playwrightDownloader.ensureRequestInterception();
      
      // Neuer Ansatz: Direkter Download über fetch statt JavaScript-Click
      this.downloadLogger.logFunctionCall(logInfo, 'direct_fetch_download', {
        url: downloadUrl,
        dokumentName
      });
      
      console.log(`        🔗 Direkter Download: ${dokumentName} -> ${downloadUrl}`);
      
      // Direkter Download über fetch statt JavaScript-Click
      // Hole Cookies vom Browser für Authentifizierung
      const cookies = await this.page.context().cookies();
      const cookieHeader = cookies.map(cookie => `${cookie.name}=${cookie.value}`).join('; ');
      
      console.log(`        🔐 Verwende ${cookies.length} Cookies für Authentifizierung`);
      
      const response = await fetch(downloadUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
          'Accept': 'application/pdf,application/octet-stream,*/*',
          'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache',
          'Cookie': cookieHeader,
          'Referer': this.page.url()
        },
        timeout: 30000 // 30 Sekunden Timeout
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Prüfe Content-Type
      const contentType = response.headers.get('content-type');
      console.log(`        📄 Content-Type: ${contentType}`);
      
      if (!contentType || (!contentType.includes('application/pdf') && !contentType.includes('application/octet-stream'))) {
        console.log(`        ⚠️ Warnung: Content-Type ist nicht PDF: ${contentType}`);
      }
      
      // Schreibe Datei direkt - Kompatibel mit node-fetch v3
      const arrayBuffer = await response.arrayBuffer();
      const buffer = Buffer.from(arrayBuffer);
      fs.writeFileSync(dokumentPath, buffer);
      
      // Prüfe Dateigröße
      const stats = fs.statSync(dokumentPath);
      const duration = Date.now() - startTime;
      
      console.log(`        ✅ Direkter Download erfolgreich: ${dokumentName} (${stats.size} Bytes)`);
      
      this.downloadLogger.logDownloadSuccess(logInfo, stats.size, duration);
      this.logger.success(`Download erfolgreich abgeschlossen: ${dokumentName}`, 'DocumentDownloader');
      
      // Manuelle Garbage Collection nach jedem Dokument
      if (global.gc) {
        const beforeMemory = process.memoryUsage();
        global.gc();
        const afterMemory = process.memoryUsage();
        this.downloadLogger.logGarbageCollection(logInfo, beforeMemory, afterMemory);
      }
      
      // Erstelle Zusammenfassung aller Logs
      this.downloadLogger.createSummary();
      
    } catch (downloadError) {
      const duration = Date.now() - startTime;
      this.downloadLogger.logError(logInfo, downloadError, 'downloadSingleDocument');
      
      // Prüfe ob es ein Timeout-Fehler ist
      if (downloadError.message.includes('Download-Timeout')) {
        this.downloadLogger.logTimeout(logInfo, 'Download', 10000);
        this.logger.warn(`Download durch Timeout abgebrochen: ${dokumentName}`, 'DocumentDownloader');
      } else {
        this.logger.error(`Download-Fehler: ${dokumentName} - ${downloadError.message}`, 'DocumentDownloader');
        
        // Fehlgeschlagenen Download protokollieren
        const month = path.basename(path.dirname(terminOrdner));
        this.fileManager.logFailedDownload(month, terminOrdnerName, null, dokumentName, downloadError.message);
      }
      
      this.downloadLogger.logDownloadFailure(logInfo, downloadError.message, duration);
      
      // Speicher freigeben bei Fehlern
      if (global.gc) {
        const beforeMemory = process.memoryUsage();
        global.gc();
        const afterMemory = process.memoryUsage();
        this.downloadLogger.logGarbageCollection(logInfo, beforeMemory, afterMemory);
      }
    }
  }

  async downloadTopDocuments(topOrdner, terminOrdnerName, topNumber, topName) {
    this.logger.info('Suche nach Dokumenten auf TOP-Seite...', 'DocumentDownloader');
    
    try {
      // Warte bis die Seite vollständig geladen ist
      await this.page.waitForLoadState('networkidle', { timeout: 10000 });
      
      // Neue Logik: Alle TOP-Dokumente auf einmal finden und dann verarbeiten
      this.logger.info(`🔍 Suche alle TOP-Dokumente auf der Seite...`, 'DocumentDownloader');
      
      // Verwende verschiedene Selektoren für TOP-Dokument-Links
      const topDocumentSelectors = [
        'a[title*="Dokument Download"]',
        'a[aria-label*="Dokument Download"]',
        'a[href*="getfile.asp"]',
        '.smc-downloaded a[href*="getfile.asp"]',
        'a.smc-link-normal[href*="getfile.asp"]'
      ];
      
      let allTopDocuments = [];
      
      // Durch alle Selektoren gehen und TOP-Dokumente sammeln
      for (const selector of topDocumentSelectors) {
        try {
          const documents = await this.page.locator(selector).all();
          this.logger.info(`🔍 TOP-Selektor "${selector}": ${documents.length} Dokumente gefunden`, 'DocumentDownloader');
          
          for (const doc of documents) {
            try {
              const docName = await doc.textContent();
              const docLink = await doc.getAttribute('href');
              
              if (docName && docLink && docLink.includes('getfile.asp')) {
                // Prüfe ob das Dokument bereits in der Liste ist
                const exists = allTopDocuments.find(d => d.name === docName.trim() && d.link === docLink);
                if (!exists) {
                  allTopDocuments.push({
                    name: docName.trim(),
                    link: docLink,
                    element: doc
                  });
                }
              }
            } catch (e) {
              this.logger.warn(`Fehler beim Extrahieren eines TOP-Dokuments: ${e.message}`, 'DocumentDownloader');
            }
          }
          
          // Wenn wir Dokumente gefunden haben, aufhören
          if (allTopDocuments.length > 0) {
            break;
          }
          
        } catch (e) {
          this.logger.warn(`Fehler mit TOP-Selektor "${selector}": ${e.message}`, 'DocumentDownloader');
        }
      }
      
      this.logger.info(`📊 Insgesamt ${allTopDocuments.length} eindeutige TOP-Dokumente gefunden`, 'DocumentDownloader');
      
      // Alle gefundenen TOP-Dokumente verarbeiten
      for (let i = 0; i < allTopDocuments.length; i++) {
        const doc = allTopDocuments[i];
        this.logger.info(`Verarbeite TOP-Dokument ${i + 1}/${allTopDocuments.length}: ${doc.name}`, 'DocumentDownloader');
        
        try {
          await this.downloadSingleTopDocument(doc.name, doc.link, topOrdner, terminOrdnerName, topNumber, topName);
          
          // Kurz warten vor dem nächsten TOP-Dokument
          await this.page.waitForTimeout(1000);
          
        } catch (error) {
          this.logger.warn(`Fehler bei TOP-Dokument ${i + 1}: ${error.message}`, 'DocumentDownloader');
        }
      }
      
    } catch (error) {
      this.logger.error(`Fehler beim Herunterladen der TOP-Dokumente: ${error.message}`, 'DocumentDownloader');
    }
  }

    async downloadSingleTopDocument(dokumentName, downloadLink, topOrdner, terminOrdnerName, topNumber, topName) {
    const cleanName = this.fileManager.sanitizeFileName(dokumentName);
    const dokumentPath = this.fileManager.generateUniqueFilePath(topOrdner, cleanName);
    
    // Erstelle detailliertes Log für dieses TOP-Dokument
    const topInfo = { topNumber, topName };
    const logInfo = this.downloadLogger.createDocumentLog(dokumentName, terminOrdnerName, topInfo);
    
    this.logger.info(`Lade TOP-Dokument herunter: ${dokumentName}`, 'DocumentDownloader');
    
    // PDF-Datei herunterladen
    const downloadUrl = downloadLink.startsWith('http') ? downloadLink : new URL(downloadLink, this.page.url()).href;
    
    // Logge Download-Start
    this.downloadLogger.logDownloadStart(logInfo, dokumentName, downloadUrl, dokumentPath, terminOrdnerName, topInfo);
    this.downloadLogger.logMemoryUsage(logInfo);
    
    const startTime = Date.now();
    
        try {
      // Stelle sicher, dass Request-Interception aktiv ist
      await this.playwrightDownloader.ensureRequestInterception();
      
      // Neuer Ansatz: Direkter Download über fetch statt JavaScript-Click
      this.downloadLogger.logFunctionCall(logInfo, 'direct_fetch_download - TOP', {
        url: downloadUrl,
        dokumentName,
        topInfo
      });
      
      console.log(`        🔗 Direkter TOP-Download: ${dokumentName} -> ${downloadUrl}`);
      
      // Direkter Download über fetch statt JavaScript-Click
      // Hole Cookies vom Browser für Authentifizierung
      const cookies = await this.page.context().cookies();
      const cookieHeader = cookies.map(cookie => `${cookie.name}=${cookie.value}`).join('; ');
      
      console.log(`        🔐 Verwende ${cookies.length} Cookies für TOP-Authentifizierung`);
      
      const response = await fetch(downloadUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
          'Accept': 'application/pdf,application/octet-stream,*/*',
          'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache',
          'Cookie': cookieHeader,
          'Referer': this.page.url()
        },
        timeout: 30000 // 30 Sekunden Timeout
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Prüfe Content-Type
      const contentType = response.headers.get('content-type');
      console.log(`        📄 TOP-Content-Type: ${contentType}`);
      
      if (!contentType || (!contentType.includes('application/pdf') && !contentType.includes('application/octet-stream'))) {
        console.log(`        ⚠️ Warnung: TOP-Content-Type ist nicht PDF: ${contentType}`);
      }
      
      // Schreibe Datei direkt - Kompatibel mit node-fetch v3
      const arrayBuffer = await response.arrayBuffer();
      const buffer = Buffer.from(arrayBuffer);
      fs.writeFileSync(dokumentPath, buffer);
      
      // Prüfe Dateigröße
      const stats = fs.statSync(dokumentPath);
      const duration = Date.now() - startTime;
      
      console.log(`        ✅ Direkter TOP-Download erfolgreich: ${dokumentName} (${stats.size} Bytes)`);
      
      this.downloadLogger.logDownloadSuccess(logInfo, stats.size, duration);
      this.logger.success(`TOP-Download erfolgreich abgeschlossen: ${dokumentName}`, 'DocumentDownloader');
      
      // Manuelle Garbage Collection nach jedem Dokument
      if (global.gc) {
        const beforeMemory = process.memoryUsage();
        global.gc();
        const afterMemory = process.memoryUsage();
        this.downloadLogger.logGarbageCollection(logInfo, beforeMemory, afterMemory);
      }
      
    } catch (downloadError) {
      const duration = Date.now() - startTime;
      this.downloadLogger.logError(logInfo, downloadError, 'downloadSingleTopDocument');
      
      // Prüfe ob es ein Timeout-Fehler ist
      if (downloadError.message.includes('Download-Timeout')) {
        this.downloadLogger.logTimeout(logInfo, 'Download', 10000);
        this.logger.warn(`TOP-Download durch Timeout abgebrochen: ${dokumentName}`, 'DocumentDownloader');
      } else {
        this.logger.error(`TOP-Download-Fehler: ${dokumentName} - ${downloadError.message}`, 'DocumentDownloader');
        
        // Fehlgeschlagenen Download protokollieren
        const month = path.basename(path.dirname(path.dirname(topOrdner)));
        this.fileManager.logFailedDownload(month, terminOrdnerName, `${topNumber}_${topName}`, dokumentName, downloadError.message);
      }
      
      this.downloadLogger.logDownloadFailure(logInfo, downloadError.message, duration);
      
      // Speicher freigeben bei Fehlern
      if (global.gc) {
        const beforeMemory = process.memoryUsage();
        global.gc();
        const afterMemory = process.memoryUsage();
        this.downloadLogger.logGarbageCollection(logInfo, beforeMemory, afterMemory);
      }
    }
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
      downloadProcessActive: this.isDownloadProcessActive(),
      browserContexts: this.page ? this.page.contexts ? this.page.contexts().length : 'Nicht verfügbar' : 'Nicht verfügbar',
      pageCount: this.page ? this.page.context ? this.page.context().pages().length : 'Nicht verfügbar' : 'Nicht verfügbar'
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
      
      // Prüfe ob es aktive Browser-Operationen gibt
      const activeBrowserOps = process._getActiveHandles ? 
        process._getActiveHandles().filter(handle => 
          handle.constructor.name === 'CDPSession' ||
          handle.constructor.name === 'BrowserContext' ||
          handle.constructor.name === 'Page'
        ).length : 0;
      
      return {
        activeTimers,
        activePromises,
        activeRequests,
        activeBrowserOps,
        hasActiveProcesses: (activeTimers > 0 || activePromises > 0 || activeRequests > 0 || activeBrowserOps > 0)
      };
    } catch (error) {
      return {
        error: error.message,
        hasActiveProcesses: 'Unbekannt'
      };
    }
  }
}

module.exports = DocumentDownloader;
