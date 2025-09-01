const fs = require('fs');
const path = require('path');

class FileManager {
  constructor() {
    this.progressFilePath = 'download_fortschritt.txt';
    this.failedDownloadsPath = 'failed_downloads.txt';
  }

  initializeFiles() {
    // Fortschrittsdatei initialisieren falls sie nicht existiert
    if (!fs.existsSync(this.progressFilePath)) {
      const header = `📊 Download-Fortschritt - Große Dateien (>10MB) - ${new Date().toLocaleString('de-DE')}\n`;
      const separator = '─'.repeat(80) + '\n';
      fs.writeFileSync(this.progressFilePath, header + separator, 'utf8');
    }
    
    // Failed Downloads Datei initialisieren falls sie nicht existiert
    if (!fs.existsSync(this.failedDownloadsPath)) {
      const header = `📊 Fehlgeschlagene Downloads - ${new Date().toLocaleString('de-DE')}\n`;
      const separator = '─'.repeat(80) + '\n';
      const columns = `Datum/Zeit | Monat | Termin | TOP | Dateiname | Fehler\n`;
      const columnSeparator = '─'.repeat(80) + '\n';
      fs.writeFileSync(this.failedDownloadsPath, header + separator + columns + columnSeparator, 'utf8');
    }
  }

  sanitizeFileName(fileName) {
    return fileName.trim()
      .replace(/[<>:"/\\|?*]/g, '_')
      .replace(/\s+/g, '_')
      .replace(/_+/g, '_')
      .replace(/^_|_$/g, '');
  }

  generateUniqueFilePath(directory, baseFileName) {
    // Eindeutigen Dateinamen generieren (keine Überschreibung)
    let filePath = path.join(directory, `${baseFileName}.pdf`);
    let counter = 1;
    
    while (fs.existsSync(filePath)) {
      const nameWithoutExt = baseFileName.replace(/\.pdf$/, '');
      filePath = path.join(directory, `${nameWithoutExt}_${counter}.pdf`);
      counter++;
    }
    
    return filePath;
  }

  logFailedDownload(month, termin, top, dokumentName, error) {
    const timestamp = new Date().toLocaleString('de-DE');
    const topInfo = top ? top : 'N/A';
    const entry = `${timestamp} | ${month} | ${termin} | ${topInfo} | ${dokumentName} | ${error}\n`;
    fs.appendFileSync(this.failedDownloadsPath, entry, 'utf8');
  }

  logProgress(terminOrdnerName, dokumentName, fileSizeInMB, reason = 'GROSSE_DATEI') {
    const progressEntry = `❌ ${reason}: ${terminOrdnerName} - Dokument: ${dokumentName} - Größe: ${fileSizeInMB} MB - ${new Date().toISOString()}\n`;
    fs.appendFileSync(this.progressFilePath, progressEntry);
  }

  fileExists(filePath) {
    return fs.existsSync(filePath);
  }

  deleteFile(filePath) {
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
    }
  }

  getFileSize(filePath) {
    if (fs.existsSync(filePath)) {
      const stats = fs.statSync(filePath);
      return stats.size;
    }
    return 0;
  }

  createDirectory(dirPath) {
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
    }
  }

  listDirectory(dirPath) {
    if (fs.existsSync(dirPath)) {
      return fs.readdirSync(dirPath);
    }
    return [];
  }

  getDirectorySize(dirPath) {
    if (!fs.existsSync(dirPath)) {
      return 0;
    }

    let totalSize = 0;
    const files = fs.readdirSync(dirPath);
    
    for (const file of files) {
      const filePath = path.join(dirPath, file);
      const stats = fs.statSync(filePath);
      
      if (stats.isDirectory()) {
        totalSize += this.getDirectorySize(filePath);
      } else {
        totalSize += stats.size;
      }
    }
    
    return totalSize;
  }
}

module.exports = FileManager;
