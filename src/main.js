const fs = require('fs');
const path = require('path');
const ConfigManager = require('./config-manager');
const { getLogger } = require('./logger');
const ErrorHandler = require('./error-handler');
const FileSystemManager = require('./file-system-manager');
const BrowserManager = require('./browser-manager');
const AuthManager = require('./auth-manager');
const CalendarNavigator = require('./calendar-navigator');
const TerminExtractor = require('./termin-extractor');
const TerminProcessor = require('./termin-processor');

(async () => {
  // Globale Services initialisieren
  const config = new ConfigManager();
  const logger = getLogger({ logFilePath: 'session_net.log' });
  const errorHandler = new ErrorHandler();
  const fileSystem = new FileSystemManager(config.get('output.directory'));
  let browserManager = null; // Browser-Manager global verfügbar machen
  
  try {
    // Konfiguration validieren
    config.validate();
    
    logger.startOperation('Website-Downloader', 'Main');
    
    browserManager = new BrowserManager();
    
    // Browser initialisieren
    const page = await browserManager.initialize();
    
    // Module initialisieren
    const authManager = new AuthManager(page);
    const calendarNavigator = new CalendarNavigator(page);
    const terminExtractor = new TerminExtractor(page);
    const terminProcessor = new TerminProcessor(page); // TerminProcessor global verfügbar machen
    
    // Login durchführen
    await authManager.login(
      config.get('website.url'),
      config.get('website.username'),
      config.get('website.password')
    );
    
    // Kalender-Link finden und navigieren
    const calendarUrl = await calendarNavigator.findCalendarLink();
    if (!calendarUrl) {
      logger.warn('Kein Kalender-Link gefunden. Versuche alternative Methode...', 'Main');
      
      // Alternative: Alle Links auf der Seite auflisten
      const allLinks = await page.locator('a').all();
      logger.info('Gefundene Links auf der Seite:', 'Main');
      for (let i = 0; i < Math.min(allLinks.length, 20); i++) {
        try {
          const linkText = await allLinks[i].textContent();
          const linkHref = await allLinks[i].getAttribute('href');
          if (linkText && linkText.trim()) {
            logger.debug(`  - ${linkText.trim()}: ${linkHref}`, 'Main');
          }
        } catch (e) {
          // Link überspringen falls Fehler
        }
      }
      return;
    }
    
    // Bestehende Kalender-Ordner in Jahresordner verschieben
    await calendarNavigator.moveExistingCalendarFolders(
      process.env.OUTPUT_DIRECTORY || 'pohlheim_geschuetzt'
    );
    
    // Nächsten zu downloadenden Monat ermitteln
    const nextMonthInfo = await calendarNavigator.findNextMonthToDownload(
      process.env.OUTPUT_DIRECTORY || 'pohlheim_geschuetzt'
    );
    
    console.log(`🎯 Nächster zu downloadender Monat: ${nextMonthInfo.month} ${nextMonthInfo.year}`);
    console.log(`📁 Zielordner: ${nextMonthInfo.folderName}`);
    
    // Zur Kalender-Seite navigieren
    const kalenderCurrentUrl = await calendarNavigator.navigateToCalendar(calendarUrl);
    
    // Monats-Informationen extrahieren
    const monthFolderName = await calendarNavigator.extractMonthInfo();
    
    // Prüfe ob der extrahierte Monat mit dem ermittelten Monat übereinstimmt
    if (monthFolderName !== nextMonthInfo.folderName) {
      console.log(`⚠️ Warnung: Extrahierter Monat (${monthFolderName}) stimmt nicht mit ermitteltem Monat (${nextMonthInfo.folderName}) überein`);
      console.log(`📅 Verwende ermittelten Monat: ${nextMonthInfo.folderName}`);
    }
    
    // Verwende den ermittelten Monatsnamen
    const targetMonthFolderName = nextMonthInfo.folderName;
    
    // Navigiere zum korrekten Monat über Rückwärts-Navigation
    console.log(`🎯 Navigiere zum Zielmonat: ${nextMonthInfo.month} ${nextMonthInfo.year}`);
    const navigationSuccess = await calendarNavigator.navigateToSpecificMonth(nextMonthInfo.year, nextMonthInfo.month);
    
    if (!navigationSuccess) {
      console.log(`⚠️ Rückwärts-Navigation fehlgeschlagen - verwende aktuellen Monat`);
    }
    
    // Finale Monatsinformationen extrahieren
    const finalMonthInfo = await calendarNavigator.getCurrentMonthInfo();
    console.log(`📅 Finaler Monat auf der Seite: ${finalMonthInfo}`);
    
    // Kalender-Seite speichern
    const monatOrdner = await calendarNavigator.saveCalendarPage(
      process.env.OUTPUT_DIRECTORY || 'pohlheim_geschuetzt',
      targetMonthFolderName
    );
    
    // Prüfen ob der Monat bereits vollständig geladen ist
    const monatVollständigGeladen = fs.existsSync(path.join(monatOrdner, 'monat_vollstaendig.txt'));
    if (monatVollständigGeladen) {
      console.log(`⏭️ Monat ${targetMonthFolderName} bereits vollständig geladen - überspringe`);
      // NICHT return - fahre mit der Navigation zu vorherigen Monaten fort
    } else {
      // Termine extrahieren (mit Cache-Funktionalität)
      const uniqueTermine = await terminExtractor.extractTermine(monatOrdner);
      
      if (uniqueTermine.length === 0) {
        logger.warn('Keine Termine gefunden. Überprüfen Sie die Selektoren.', 'Main');
        // NICHT return - fahre mit der Navigation zu vorherigen Monaten fort
             } else {
         logger.info(`${uniqueTermine.length} Termine gefunden - Prüfung erfolgt direkt über Dateisystem`, 'Main');
         
         // Termine verarbeiten
         for (let i = 0; i < uniqueTermine.length; i++) {
           const termin = uniqueTermine[i];
           
           await terminProcessor.processTermin(termin, monatOrdner, kalenderCurrentUrl);
          
          // Speicher nach jedem Termin freigeben
          console.log(`  🧹 Termin abgeschlossen: ${termin.terminName}`);
          
          // Speicher freigeben ohne Browser-Kontext neu zu starten
          if (i < uniqueTermine.length - 1) { // Nicht beim letzten Termin
            console.log(`  🧹 Speicher wird freigegeben...`);
            
            // Zurück zur Kalender-Seite navigieren (bleibt im gleichen Kontext)
            await page.goto(kalenderCurrentUrl);
            await page.waitForTimeout(2000);
            
            // Manuell Garbage Collection anstoßen
            if (global.gc) {
              global.gc();
            }
            
            // Zusätzliche Speicherbereinigung
            const memUsage = process.memoryUsage();
            const usedMB = Math.round(memUsage.heapUsed / 1024 / 1024);
            console.log(`  📊 Speicherverbrauch: ${usedMB}MB`);
            
            console.log(`  ✅ Speicher freigegeben, Session bleibt erhalten`);
          }
        }
        
        console.log(`\n📋 Zusammenfassung der Termine:`);
        console.log(`   Gesamt: ${uniqueTermine.length} Termine`);
        console.log(`   Erster Termin: ${uniqueTermine[0].tag}. - ${uniqueTermine[0].terminName}`);
        console.log(`   Letzter Termin: ${uniqueTermine[uniqueTermine.length - 1].tag}. - ${uniqueTermine[uniqueTermine.length - 1].terminName}`);
        console.log(`   💡 Prüfung auf bereits geladene Termine erfolgt direkt über Dateisystem (termin_vollstaendig.txt)`);
        
        // Monat als vollständig markieren
        const monatVollständigDatei = path.join(monatOrdner, 'monat_vollstaendig.txt');
        const monatVollständigInfo = `Monat vollständig geladen: ${new Date().toISOString()}\nAnzahl Termine: ${uniqueTermine.length}\n`;
        fs.writeFileSync(monatVollständigDatei, monatVollständigInfo, 'utf8');
        console.log(`   ✅ Monat ${targetMonthFolderName} als vollständig markiert`);
        
        // Prüfe ob es sich um Januar handelt und erstelle jahr_vollstaendig.txt
        await calendarNavigator.checkAndCreateYearCompleteFile(
          process.env.OUTPUT_DIRECTORY || 'pohlheim_geschuetzt',
          targetMonthFolderName,
          uniqueTermine.length
        );
      }
    }
    
    // Aktuelle URL der Kalender-Seite anzeigen
    console.log(`🌐 Kalender-Seite URL: ${page.url()}`);
    
    // Automatische Navigation zu vorherigen Monaten (rückwärts durch die Monate)
    logger.info('Starte automatische Navigation zu vorherigen Monaten...', 'Main');
    
    let monthCounter = 1;
    let processedMonths = new Set(); // Set um bereits verarbeitete Monate zu tracken
    processedMonths.add(targetMonthFolderName); // Aktueller Monat ist bereits verarbeitet
    
    while (true) { // Unbegrenzte Schleife - läuft bis keine Navigation mehr möglich ist
      logger.info(`Verarbeite Monat ${monthCounter}...`, 'Main');
      
      // Versuche zum vorherigen Monat zu navigieren
      const navigationSuccess = await calendarNavigator.navigateToPreviousMonth();
      
      if (!navigationSuccess) {
        logger.warn('Navigation zum vorherigen Monat fehlgeschlagen - beende automatische Navigation', 'Main');
        break;
      }
      
      const newMonthInfo = await calendarNavigator.getCurrentMonthInfo();
      if (!newMonthInfo) {
        logger.warn('Keine neuen Monats-Informationen gefunden - beende automatische Navigation', 'Main');
        break;
      }
      
      // Prüfe ob wir diesen Monat bereits verarbeitet haben
      if (processedMonths.has(newMonthInfo)) {
        logger.info(`Monat ${newMonthInfo} bereits verarbeitet - überspringe`, 'Main');
        monthCounter++;
        continue;
      }
      
      logger.info(`Neuer Monat gefunden: ${newMonthInfo}`, 'Main');
      processedMonths.add(newMonthInfo); // Markiere als verarbeitet
      
      const newMonthFolderName = newMonthInfo
        .replace(/[<>:"/\\|?*]/g, '_')
        .replace(/\s+/g, '_')
        .replace(/_+/g, '_')
        .replace(/^_|_$/g, '');
      
      const newMonatOrdner = await calendarNavigator.saveCalendarPage(
        process.env.OUTPUT_DIRECTORY || 'pohlheim_geschuetzt',
        newMonthFolderName
      );
      
      // Prüfen ob der neue Monat bereits vollständig geladen ist
      const newMonatVollständigGeladen = fs.existsSync(path.join(newMonatOrdner, 'monat_vollstaendig.txt'));
      if (newMonatVollständigGeladen) {
        logger.info(`Monat ${newMonthInfo} bereits vollständig geladen - überspringe`, 'Main');
        monthCounter++;
        continue;
      }
      
      const newUniqueTermine = await terminExtractor.extractTermine(newMonatOrdner);
      
      if (newUniqueTermine.length === 0) {
        logger.warn('Keine Termine für den neuen Monat gefunden - fahre mit nächstem Monat fort', 'Main');
        monthCounter++;
        continue;
      }
      
      logger.info(`${newUniqueTermine.length} Termine für neuen Monat gefunden`, 'Main');
      
      for (let i = 0; i < newUniqueTermine.length; i++) {
        const termin = newUniqueTermine[i];
        await terminProcessor.processTermin(termin, newMonatOrdner, page.url());
        
        if (i < newUniqueTermine.length - 1) {
          await page.goto(page.url());
          await page.waitForTimeout(2000);
          if (global.gc) global.gc();
        }
      }
      
      logger.info(`Monat ${monthCounter} abgeschlossen: ${newMonthInfo} (${newUniqueTermine.length} Termine)`, 'Main');
      
      // Neuen Monat als vollständig markieren
      const newMonatVollständigDatei = path.join(newMonatOrdner, 'monat_vollstaendig.txt');
      const newMonatVollständigInfo = `Monat vollständig geladen: ${new Date().toISOString()}\nAnzahl Termine: ${newUniqueTermine.length}\n`;
      fs.writeFileSync(newMonatVollständigDatei, newMonatVollständigInfo, 'utf8');
      logger.info(`Monat ${newMonthInfo} als vollständig markiert`, 'Main');
      
      // Prüfe ob es sich um Januar handelt und erstelle jahr_vollstaendig.txt
      await calendarNavigator.checkAndCreateYearCompleteFile(
        process.env.OUTPUT_DIRECTORY || 'pohlheim_geschuetzt',
        newMonthFolderName,
        newUniqueTermine.length
      );
      
      monthCounter++;
    }
    
    logger.completeOperation(`Automatische Navigation abgeschlossen - ${monthCounter - 1} Monate verarbeitet`, 'Main');
    
    // Browser schließen
    await browserManager.close();
    console.log('🎉 Download abgeschlossen!');
    
  } catch (error) {
    console.error('❌ Fehler beim Ausführen des Skripts:', error);
    if (browserManager) {
      await browserManager.close();
    }
    process.exit(1);
  }
})();
