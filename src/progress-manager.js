const fs = require('fs');
const path = require('path');

class ProgressManager {
  constructor(outputDirectory) {
    this.outputDirectory = outputDirectory;
    this.progressFilePath = path.join(outputDirectory, 'download_fortschritt.txt');
    this.alreadyDownloadedFolders = new Set();
  }

  async loadProgress() {
    if (fs.existsSync(this.progressFilePath)) {
      console.log('📋 Lade bestehenden Download-Fortschritt...');
      const progressContent = fs.readFileSync(this.progressFilePath, 'utf8');
      const lines = progressContent.split('\n').filter(line => line.trim());
      
      for (const line of lines) {
        if (line.startsWith('✅')) {
          const folderName = line.substring(2).trim();
          // Nur den Ordnernamen extrahieren (alles vor dem ersten Leerzeichen)
          const folderNameClean = folderName.split(' ')[0];
          this.alreadyDownloadedFolders.add(folderNameClean);
        }
      }
      console.log(`📊 ${this.alreadyDownloadedFolders.size} Ordner bereits vollständig geladen`);
    } else {
      console.log('📋 Erstelle neue Fortschrittsdatei im Root-Ordner...');
      await this.createNewProgressFile();
    }
  }

  async createNewProgressFile(monthFolderName = 'Unbekannt') {
    const header = `📊 Download-Fortschritt - ${new Date().toLocaleString('de-DE')}\n`;
    const monthHeader = `📅 Monat: ${monthFolderName}\n`;
    const separator = '─'.repeat(50) + '\n';
    fs.writeFileSync(this.progressFilePath, header + monthHeader + separator, 'utf8');
  }

  isAlreadyDownloaded(folderName) {
    return this.alreadyDownloadedFolders.has(folderName);
  }

  markAsDownloaded(folderName, message = 'vollständig geladen') {
    this.alreadyDownloadedFolders.add(folderName);
    const successLog = `✅ ${folderName} - ${message}\n`;
    fs.appendFileSync(this.progressFilePath, successLog);
  }

  logError(folderName, errorMessage) {
    const errorLog = `❌ ${folderName} - Fehler: ${errorMessage}\n`;
    fs.appendFileSync(this.progressFilePath, errorLog);
  }

  logDocumentDownload(folderName, documentName, fileName) {
    const successLog = `✅ ${folderName} - Dokument: ${documentName} - ${fileName}\n`;
    fs.appendFileSync(this.progressFilePath, successLog);
  }

  logTopDownload(folderName, topNumber, topName, documentName, fileName) {
    const successLog = `✅ ${folderName} - TOP ${topNumber}: ${topName} - Dokument: ${documentName} - ${fileName}\n`;
    fs.appendFileSync(this.progressFilePath, successLog);
  }

  logTopPageDownload(folderName, topNumber, topName) {
    const successLog = `✅ ${folderName} - TOP ${topNumber}: ${topName} - Seite gespeichert\n`;
    fs.appendFileSync(this.progressFilePath, successLog);
  }

  async addSummary(totalTermine, alreadyDownloadedCount, newlyDownloadedCount) {
    const summary = `\n📊 Download-Zusammenfassung - ${new Date().toLocaleString('de-DE')}\n`;
    fs.appendFileSync(this.progressFilePath, summary);
    fs.appendFileSync(this.progressFilePath, `   Gesamt: ${totalTermine} Termine\n`);
    fs.appendFileSync(this.progressFilePath, `   Bereits geladen: ${alreadyDownloadedCount} Termine\n`);
    fs.appendFileSync(this.progressFilePath, `   Neu geladen: ${newlyDownloadedCount} Termine\n`);
  }

  getAlreadyDownloadedCount() {
    return this.alreadyDownloadedFolders.size;
  }

  getProgressFilePath() {
    return this.progressFilePath;
  }
}

module.exports = ProgressManager;
