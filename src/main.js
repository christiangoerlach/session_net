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
  
  try {
    // Konfiguration validieren
    config.validate();
    
    logger.startOperation('Website-Downloader', 'Main');
    
    const browserManager = new BrowserManager();
    
    // Browser initialisieren
    const page = await browserManager.initialize();
    
    // Module initialisieren
    const authManager = new AuthManager(page);
    const calendarNavigator = new CalendarNavigator(page);
    const terminExtractor = new TerminExtractor(page);
    
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
    
    // Zur Kalender-Seite navigieren
    const kalenderCurrentUrl = await calendarNavigator.navigateToCalendar(calendarUrl);
    
    // Monats-Informationen extrahieren
    const monthFolderName = await calendarNavigator.extractMonthInfo();
    
    // Kalender-Seite speichern
    const monatOrdner = await calendarNavigator.saveCalendarPage(
      process.env.OUTPUT_DIRECTORY || 'pohlheim_geschuetzt',
      monthFolderName
    );
    
    // Termine extrahieren (mit Cache-Funktionalität)
    const uniqueTermine = await terminExtractor.extractTermine(monatOrdner);
    
    if (uniqueTermine.length === 0) {
      logger.warn('Keine Termine gefunden. Überprüfen Sie die Selektoren.', 'Main');
      return;
    }
    
    logger.info(`${uniqueTermine.length} Termine gefunden - Prüfung erfolgt direkt über Dateisystem`, 'Main');
    
    // Termin-Processor initialisieren
    const terminProcessor = new TerminProcessor(page);
    
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
    
    // Aktuelle URL der Kalender-Seite anzeigen
    console.log(`🌐 Kalender-Seite URL: ${kalenderCurrentUrl}`);
    
    // Automatische Navigation zum nächsten Monat (optional)
    logger.info('Starte automatische Navigation zum nächsten Monat...', 'Main');
    
    let monthCounter = 1;
    const maxMonths = 12;
    
    while (monthCounter <= maxMonths) {
      logger.info(`Verarbeite Monat ${monthCounter}/${maxMonths}...`, 'Main');
      
      const navigationSuccess = await calendarNavigator.navigateToNextMonth();
      
      if (!navigationSuccess) {
        logger.warn('Navigation zum nächsten Monat fehlgeschlagen - beende automatische Navigation', 'Main');
        break;
      }
      
      const newMonthInfo = await calendarNavigator.getCurrentMonthInfo();
      if (!newMonthInfo || newMonthInfo === monthFolderName) {
        logger.warn('Keine neuen Monats-Informationen gefunden - beende automatische Navigation', 'Main');
        break;
      }
      
      logger.info(`Neuer Monat gefunden: ${newMonthInfo}`, 'Main');
      
      const newMonthFolderName = newMonthInfo
        .replace(/[<>:"/\\|?*]/g, '_')
        .replace(/\s+/g, '_')
        .replace(/_+/g, '_')
        .replace(/^_|_$/g, '');
      
      const newMonatOrdner = await calendarNavigator.saveCalendarPage(
        process.env.OUTPUT_DIRECTORY || 'pohlheim_geschuetzt',
        newMonthFolderName
      );
      
      const newUniqueTermine = await terminExtractor.extractTermine(newMonatOrdner);
      
      if (newUniqueTermine.length === 0) {
        logger.warn('Keine Termine für den neuen Monat gefunden - fahre mit nächstem Monat fort', 'Main');
        monthCounter++;
        continue;
      }
      
      logger.info(`${newUniqueTermine.length} Termine für neuen Monat gefunden`, 'Main');
      
      for (let i = 0; i < newUniqueTermine.length; i++) {
        const termin = newUniqueTermine[i];
        await terminProcessor.processTermin(termin, newMonatOrdner, kalenderCurrentUrl);
        
        if (i < newUniqueTermine.length - 1) {
          await page.goto(kalenderCurrentUrl);
          await page.waitForTimeout(2000);
          if (global.gc) global.gc();
        }
      }
      
      logger.info(`Monat ${monthCounter} abgeschlossen: ${newMonthInfo} (${newUniqueTermine.length} Termine)`, 'Main');
      monthCounter++;
    }
    
    logger.completeOperation(`Automatische Navigation abgeschlossen - ${monthCounter - 1} Monate verarbeitet`, 'Main');
    
    // Browser schließen
    await browserManager.close();
    console.log('🎉 Download abgeschlossen!');
    
  } catch (error) {
    console.error('❌ Fehler beim Ausführen des Skripts:', error);
    await browserManager.close();
    process.exit(1);
  }
})();
