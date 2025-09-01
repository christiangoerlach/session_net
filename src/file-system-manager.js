const fs = require('fs');
const path = require('path');

class FileSystemManager {
  constructor(outputDirectory) {
    this.outputDirectory = outputDirectory;
  }

  // Ordner erstellen
  createDirectory(dirPath) {
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
      console.log(`📁 Ordner erstellt: ${dirPath}`);
      return true;
    } else {
      console.log(`📁 Ordner existiert bereits: ${dirPath}`);
      return false;
    }
  }

  // Datei speichern
  saveFile(filePath, content, encoding = 'utf8') {
    try {
      fs.writeFileSync(filePath, content, encoding);
      console.log(`💾 Datei gespeichert: ${filePath}`);
      return true;
    } catch (error) {
      console.error(`❌ Fehler beim Speichern von ${filePath}:`, error.message);
      return false;
    }
  }

  // Datei lesen
  readFile(filePath, encoding = 'utf8') {
    try {
      return fs.readFileSync(filePath, encoding);
    } catch (error) {
      console.error(`❌ Fehler beim Lesen von ${filePath}:`, error.message);
      return null;
    }
  }

  // Datei existiert
  fileExists(filePath) {
    return fs.existsSync(filePath);
  }

  // Ordnername bereinigen
  sanitizeFolderName(name) {
    return name
      .replace(/[<>:"/\\|?*]/g, '_')
      .replace(/\s+/g, '_')
      .replace(/_+/g, '_')
      .replace(/^_|_$/g, '');
  }

  // Eindeutigen Dateinamen generieren
  generateUniqueFileName(basePath, fileName, extension = '') {
    const ext = extension || path.extname(fileName);
    const nameWithoutExt = path.basename(fileName, ext);
    const dir = path.dirname(basePath);
    
    let counter = 1;
    let uniquePath = path.join(dir, `${nameWithoutExt}${ext}`);
    
    while (fs.existsSync(uniquePath)) {
      uniquePath = path.join(dir, `${nameWithoutExt}_${counter}${ext}`);
      counter++;
    }
    
    return uniquePath;
  }

  // Monats-Ordner erstellen
  createMonthFolder(monthName) {
    const sanitizedMonthName = this.sanitizeFolderName(monthName);
    const monthFolder = path.join(this.outputDirectory, sanitizedMonthName);
    this.createDirectory(monthFolder);
    return monthFolder;
  }

  // Termin-Ordner erstellen
  createTerminFolder(monthFolder, tag, terminName) {
    const sanitizedTerminName = this.sanitizeFolderName(terminName);
    const terminFolderName = `${tag}_${sanitizedTerminName}`;
    const terminFolder = path.join(monthFolder, terminFolderName);
    this.createDirectory(terminFolder);
    return { folder: terminFolder, name: terminFolderName };
  }

  // TOP-Ordner erstellen
  createTopFolder(terminFolder, topNumber, topName) {
    const sanitizedTopName = this.sanitizeFolderName(topName).substring(0, 100);
    const topFolderName = `TOP_${topNumber}_${sanitizedTopName}`;
    const topFolder = path.join(terminFolder, topFolderName);
    this.createDirectory(topFolder);
    return { folder: topFolder, name: topFolderName };
  }

  // JSON-Datei speichern
  saveJson(filePath, data) {
    return this.saveFile(filePath, JSON.stringify(data, null, 2));
  }

  // JSON-Datei lesen
  readJson(filePath) {
    const content = this.readFile(filePath);
    if (content) {
      try {
        return JSON.parse(content);
      } catch (error) {
        console.error(`❌ Fehler beim Parsen von JSON ${filePath}:`, error.message);
        return null;
      }
    }
    return null;
  }

  // Verzeichnis auflisten
  listDirectory(dirPath) {
    try {
      return fs.readdirSync(dirPath);
    } catch (error) {
      console.error(`❌ Fehler beim Auflisten von ${dirPath}:`, error.message);
      return [];
    }
  }

  // Datei löschen
  deleteFile(filePath) {
    try {
      fs.unlinkSync(filePath);
      console.log(`🗑️ Datei gelöscht: ${filePath}`);
      return true;
    } catch (error) {
      console.error(`❌ Fehler beim Löschen von ${filePath}:`, error.message);
      return false;
    }
  }

  // Verzeichnis löschen
  deleteDirectory(dirPath) {
    try {
      fs.rmSync(dirPath, { recursive: true, force: true });
      console.log(`🗑️ Verzeichnis gelöscht: ${dirPath}`);
      return true;
    } catch (error) {
      console.error(`❌ Fehler beim Löschen von ${dirPath}:`, error.message);
      return false;
    }
  }

  // Dateigröße ermitteln
  getFileSize(filePath) {
    try {
      const stats = fs.statSync(filePath);
      return stats.size;
    } catch (error) {
      console.error(`❌ Fehler beim Ermitteln der Dateigröße von ${filePath}:`, error.message);
      return 0;
    }
  }

  // Verzeichnisgröße ermitteln
  getDirectorySize(dirPath) {
    try {
      let totalSize = 0;
      const files = this.listDirectory(dirPath);
      
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
    } catch (error) {
      console.error(`❌ Fehler beim Ermitteln der Verzeichnisgröße von ${dirPath}:`, error.message);
      return 0;
    }
  }
}

module.exports = FileSystemManager;
