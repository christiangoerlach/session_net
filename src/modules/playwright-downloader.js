const fs = require('fs');
const path = require('path');
const fetch = require('node-fetch').default;

class PlaywrightDownloader {
  constructor(page) {
    this.page = page;
    this.pdfRequests = [];
    this.setupRequestInterception();
  }

  /**
   * Richtet die Request-Interception für PDF-Dateien ein
   */
  async setupRequestInterception() {
    try {
      // Prüfe ob bereits Interception eingerichtet ist
      console.log('        🔍 Prüfe Request-Interception Status...');
      
      // Intercepte alle PDF-Requests mit page.route() - ABER lasse sie durchlaufen
      await this.page.route('**/*.pdf', async (route, request) => {
        const url = request.url();
        const headers = request.headers();
        
        console.log(`        🔍 PDF-Request abgefangen: ${url}`);
        
        // Speichere URL und Headers
        this.pdfRequests.push({
          url: url,
          headers: headers,
          timestamp: new Date().toISOString()
        });
        
        // WICHTIG: Lasse den Request durchlaufen, breche ihn NICHT ab
        route.continue();
      });

      // Intercepte auch getfile.asp Requests (falls die PDFs darüber kommen)
      await this.page.route('**/getfile.asp*', async (route, request) => {
        const url = request.url();
        const headers = request.headers();
        
        console.log(`        🔍 getfile.asp Request abgefangen: ${url}`);
        
        // Prüfe ob es sich um eine PDF handelt
        if (this.isPdfRequest(request)) {
          this.pdfRequests.push({
            url: url,
            headers: headers,
            timestamp: new Date().toISOString(),
            type: 'getfile.asp'
          });
        }
        
        // WICHTIG: Lasse den Request durchlaufen, breche ihn NICHT ab
        route.continue();
      });

      console.log('        ✅ Request-Interception mit page.route() eingerichtet (Requests werden durchgelassen)');
    } catch (error) {
      console.error(`        ❌ Fehler beim Einrichten der Request-Interception: ${error.message}`);
    }
  }

  /**
   * Stellt sicher, dass die Request-Interception aktiv ist
   */
  async ensureRequestInterception() {
    try {
      console.log('        🔍 Stelle sicher, dass Request-Interception aktiv ist...');
      
      // Prüfe ob bereits Interception eingerichtet ist
      const hasRoute = this.page._routes && this.page._routes.length > 0;
      
      if (!hasRoute) {
        console.log('        ⚠️ Request-Interception nicht aktiv, richte neu ein...');
        await this.setupRequestInterception();
      } else {
        console.log('        ✅ Request-Interception bereits aktiv');
      }
      
    } catch (error) {
      console.error(`        ❌ Fehler beim Prüfen der Request-Interception: ${error.message}`);
      // Versuche neu einzurichten
      await this.setupRequestInterception();
    }
  }

  /**
   * Prüft ob ein Request eine PDF-Datei ist
   */
  isPdfRequest(request) {
    const url = request.url();
    const headers = request.headers();
    
    // Prüfe URL auf PDF-Endung
    if (url.toLowerCase().includes('.pdf')) {
      return true;
    }
    
    // Prüfe Content-Type Header
    if (headers['accept'] && headers['accept'].includes('application/pdf')) {
      return true;
    }
    
    // Prüfe getfile.asp mit PDF-Parameter
    if (url.includes('getfile.asp') && url.includes('type=do')) {
      return true;
    }
    
    return false;
  }

  /**
   * Lädt die abgefangenen PDFs separat herunter
   */
  async downloadInterceptedPdfs(downloadDir, logInfo = null) {
    console.log(`        🔍 Lade ${this.pdfRequests.length} abgefangene PDFs herunter...`);
    
    if (logInfo) {
      logInfo.addLogEntry(logInfo, 'INFO', `Abgefangene PDF-Requests: ${this.pdfRequests.length}`);
    }
    
    const results = [];
    
    // WICHTIG: Leere die Request-Liste nach dem Download, damit keine Duplikate entstehen
    const requestsToProcess = [...this.pdfRequests];
    this.pdfRequests = []; // Leere die Liste sofort
    
    console.log(`        🔄 Verarbeite ${requestsToProcess.length} PDF-Requests und leere Liste`);
    
    // Stelle sicher, dass Request-Interception für den nächsten Download aktiv ist
    await this.ensureRequestInterception();
    
    for (let i = 0; i < requestsToProcess.length; i++) {
      const request = requestsToProcess[i];
      try {
        console.log(`        📥 Lade PDF ${i + 1}/${requestsToProcess.length}: ${request.url}`);
        
        if (logInfo) {
          logInfo.addLogEntry(logInfo, 'INFO', `Starte Download: ${request.url}`);
        }
        
        const result = await this.downloadSinglePdf(request, downloadDir, logInfo);
        results.push(result);
        
        console.log(`        ✅ PDF ${i + 1} erfolgreich heruntergeladen: ${result.filename}`);
        
      } catch (error) {
        console.error(`        ❌ Fehler beim Download von PDF ${i + 1}: ${error.message}`);
        
        if (logInfo) {
          logInfo.addLogEntry(logInfo, 'ERROR', `Download-Fehler: ${error.message}`);
        }
        
        results.push({
          success: false,
          error: error.message,
          url: request.url
        });
      }
    }
    
    console.log(`        ✅ Alle PDF-Requests verarbeitet, Liste geleert`);
    
    return results;
  }

  /**
   * Lädt eine einzelne PDF herunter
   */
  async downloadSinglePdf(request, downloadDir, logInfo = null) {
    const startTime = Date.now();
    
    try {
      // Erstelle Download-Verzeichnis falls es nicht existiert
      if (!fs.existsSync(downloadDir)) {
        fs.mkdirSync(downloadDir, { recursive: true });
      }
      
      // Generiere Dateinamen aus URL
      const filename = this.generateFilename(request.url);
      const filePath = path.join(downloadDir, filename);
      
      if (logInfo) {
        logInfo.addLogEntry(logInfo, 'DEBUG', `Download-Pfad: ${filePath}`);
      }
      
      // Lade PDF mit node-fetch herunter
      const response = await fetch(request.url, {
        headers: request.headers,
        timeout: 30000 // 30 Sekunden Timeout
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Prüfe Content-Type
      const contentType = response.headers.get('content-type');
      if (logInfo) {
        logInfo.addLogEntry(logInfo, 'DEBUG', `Content-Type: ${contentType}`);
      }
      
      if (!contentType || !contentType.includes('application/pdf')) {
        console.log(`        ⚠️ Warnung: Content-Type ist nicht PDF: ${contentType}`);
      }
      
      // Schreibe Datei
      const fileStream = fs.createWriteStream(filePath);
      
      await new Promise((resolve, reject) => {
        response.body.pipe(fileStream);
        response.body.on('error', reject);
        fileStream.on('finish', resolve);
        fileStream.on('error', reject);
      });
      
      // Prüfe Dateigröße
      const stats = fs.statSync(filePath);
      const duration = Date.now() - startTime;
      
      if (logInfo) {
        logInfo.addLogEntry(logInfo, 'SUCCESS', `PDF erfolgreich heruntergeladen: ${filename}`);
        logInfo.addLogEntry(logInfo, 'INFO', `Dateigröße: ${stats.size} Bytes`);
        logInfo.addLogEntry(logInfo, 'INFO', `Dauer: ${duration}ms`);
      }
      
      return {
        success: true,
        filename: filename,
        filePath: filePath,
        fileSize: stats.size,
        duration: duration,
        url: request.url
      };
      
    } catch (error) {
      const duration = Date.now() - startTime;
      
      if (logInfo) {
        logInfo.addLogEntry(logInfo, 'ERROR', `PDF-Download fehlgeschlagen: ${error.message}`);
        logInfo.addLogEntry(logInfo, 'INFO', `Dauer bis Fehler: ${duration}ms`);
      }
      
      throw error;
    }
  }

  /**
   * Generiert einen Dateinamen aus der URL
   */
  generateFilename(url) {
    try {
      // Versuche den Dateinamen aus der URL zu extrahieren
      const urlObj = new URL(url);
      const pathname = urlObj.pathname;
      
      // Suche nach PDF-Dateinamen
      if (pathname.includes('.pdf')) {
        return path.basename(pathname);
      }
      
      // Suche nach getfile.asp Parametern
      if (url.includes('getfile.asp')) {
        const idMatch = url.match(/id=(\d+)/);
        const typeMatch = url.match(/type=([^&]+)/);
        
        if (idMatch && typeMatch) {
          return `document_${idMatch[1]}_${typeMatch[1]}.pdf`;
        }
      }
      
      // Fallback: Timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      return `pdf_${timestamp}.pdf`;
      
    } catch (error) {
      // Fallback bei Fehlern
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      return `pdf_${timestamp}.pdf`;
    }
  }

  /**
   * Gibt alle abgefangenen PDF-Requests zurück
   */
  getInterceptedPdfs() {
    return this.pdfRequests;
  }

  /**
   * Löscht alle abgefangenen PDF-Requests
   */
  clearInterceptedPdfs() {
    this.pdfRequests = [];
  }

  /**
   * Alte Download-Methode (wird nicht mehr verwendet)
   */
  async download(url, filePath, dokumentName, terminOrdnerName, timeoutCheck, abortController, logInfo) {
    console.log(`        ⚠️ Alte Download-Methode wird nicht mehr verwendet`);
    console.log(`        🔍 Verwende stattdessen Request-Interception`);
    
    // Warte kurz, damit Requests abgefangen werden können
    await this.page.waitForTimeout(2000);
    
    // Lade abgefangene PDFs herunter
    const downloadDir = path.dirname(filePath);
    return await this.downloadInterceptedPdfs(downloadDir, logInfo);
  }
}

module.exports = PlaywrightDownloader;
