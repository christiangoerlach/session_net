const path = require('path');
const fs = require('fs');

class CalendarNavigator {
  constructor(page) {
    this.page = page;
  }

  async findCalendarLink() {
    console.log('📅 Suche nach Kalender-Link...');
    
    const kalenderSelectors = [
      'a:has-text("Kalender")',
      'a:has-text("calendar")',
      'a[href*="kalender"]',
      'a[href*="calendar"]',
      'a[href*="termin"]',
      'a[href*="sitzung"]',
      'a[href*="gremien"]',
      'a[href*="meeting"]',
      'a:has-text("Termine")',
      'a:has-text("Sitzungen")',
      'a:has-text("Gremien")',
      'a:has-text("Meetings")'
    ];
    
    for (const selector of kalenderSelectors) {
      try {
        const kalenderLink = await this.page.locator(selector).first();
        if (await kalenderLink.count() > 0) {
          console.log(`🎯 Kalender-Link gefunden mit Selektor: ${selector}`);
          return await kalenderLink.getAttribute('href');
        }
      } catch (e) {
        // Weiter zum nächsten Selektor
      }
    }
    
    return null;
  }

  async navigateToCalendar(calendarUrl) {
    console.log('📱 Navigiere zur Kalender-Seite...');
    const fullCalendarUrl = calendarUrl.startsWith('http') ? calendarUrl : new URL(calendarUrl, this.page.url()).href;
    await this.page.goto(fullCalendarUrl);
    
    // Warten bis Kalender-Seite geladen ist
    await this.page.waitForTimeout(3000);
    
    return this.page.url();
  }

  async extractMonthInfo() {
    console.log('📅 Extrahiere aktuellen Monat aus der Kalender-Seite...');
    let monatOrdnerName = 'Kalender_Unbekannt';
    
    const monatSelectors = [
      'h1:has-text("Kalender")',
      'h2:has-text("Kalender")',
      'h3:has-text("Kalender")',
      'h1:has-text("calendar")',
      'h2:has-text("calendar")',
      'h3:has-text("calendar")',
      '.kalender-titel',
      '.calendar-title',
      '.page-title',
      'title'
    ];
    
    for (const selector of monatSelectors) {
      try {
        const element = await this.page.locator(selector).first();
        if (await element.count() > 0) {
          const monatText = await element.textContent();
          if (monatText && monatText.trim()) {
            console.log(`📝 Monats-Text gefunden: "${monatText.trim()}"`);
            
            // Bereinige den Text und erstelle einen gültigen Ordnernamen
            let cleanText = monatText.trim()
              .replace(/[<>:"/\\|?*]/g, '_')
              .replace(/\s+/g, '_')
              .replace(/_+/g, '_')
              .replace(/^_|_$/g, '');
            
            // Prüfe ob das Jahr bereits im Text enthalten ist
            const yearMatch = cleanText.match(/(\d{4})/);
            if (yearMatch) {
              // Jahr ist bereits enthalten, verwende den Text wie er ist
              monatOrdnerName = cleanText;
            } else {
              // Jahr ist nicht enthalten, füge das aktuelle Jahr hinzu
              const currentYear = new Date().getFullYear();
              monatOrdnerName = `Kalender_${currentYear}_${cleanText}`;
            }
            
            break;
          }
        }
      } catch (e) {
        // Weiter zum nächsten Selektor
      }
    }
    
    // Fallback: Wenn kein Text gefunden wurde, verwende aktuelles Jahr und Monat
    if (monatOrdnerName === 'Kalender_Unbekannt') {
      const now = new Date();
      const currentYear = now.getFullYear();
      const currentMonth = now.toLocaleString('de-DE', { month: 'long' });
      monatOrdnerName = `Kalender_${currentYear}_${currentMonth}`;
      console.log(`📝 Fallback: Verwende aktuellen Monat: ${monatOrdnerName}`);
    }
    
    return monatOrdnerName;
  }

  async saveCalendarPage(outputDirectory, monthFolderName) {
    // Extrahiere das Jahr aus dem Monats-Ordnernamen
    const yearMatch = monthFolderName.match(/Kalender_(\d{4})_/);
    let yearFolder = null;
    let finalMonthFolderName = monthFolderName;
    
    if (yearMatch) {
      const year = yearMatch[1];
      yearFolder = path.join(outputDirectory, year);
      
      // Erstelle Jahresordner falls er nicht existiert
      if (!fs.existsSync(yearFolder)) {
        fs.mkdirSync(yearFolder, { recursive: true });
        console.log(`📁 Jahres-Ordner erstellt: ${yearFolder}`);
      } else {
        console.log(`📁 Jahres-Ordner existiert bereits: ${yearFolder}`);
      }
      
      // Der Monats-Ordner wird direkt im Jahresordner erstellt
      const monatOrdner = path.join(yearFolder, monthFolderName);
      if (!fs.existsSync(monatOrdner)) {
        fs.mkdirSync(monatOrdner, { recursive: true });
        console.log(`📁 Monats-Ordner erstellt: ${monatOrdner}`);
      } else {
        console.log(`📁 Monats-Ordner existiert bereits: ${monatOrdner}`);
      }
    } else {
      // Fallback: Wenn kein Jahr gefunden wird, erstelle den Ordner direkt im Hauptverzeichnis
      const monatOrdner = path.join(outputDirectory, monthFolderName);
      if (!fs.existsSync(monatOrdner)) {
        fs.mkdirSync(monatOrdner, { recursive: true });
        console.log(`📁 Monats-Ordner erstellt: ${monatOrdner}`);
      } else {
        console.log(`📁 Monats-Ordner existiert bereits: ${monatOrdner}`);
      }
    }

    // 📄 Kalender-Seite herunterladen
    console.log('💾 Speichere Kalender-Seite...');
    const kalenderHtml = await this.page.content();
    
    // Bestimme den finalen Pfad für die Dateien
    const finalPath = yearFolder ? path.join(yearFolder, monthFolderName) : path.join(outputDirectory, monthFolderName);
    
    // HTML-Datei der Kalender-Seite im Monats-Ordner speichern
    const kalenderOutputPath = path.join(finalPath, 'kalender_seite.html');
    fs.writeFileSync(kalenderOutputPath, kalenderHtml, 'utf8');
    
    // Screenshot der Kalender-Seite im Monats-Ordner speichern
    const kalenderScreenshotPath = path.join(finalPath, 'kalender_seite_screenshot.png');
    await this.page.screenshot({ path: kalenderScreenshotPath, fullPage: true });
    
    console.log(`✅ Erfolgreich! Kalender-HTML gespeichert in: ${kalenderOutputPath}`);
    console.log(`📸 Kalender-Screenshot gespeichert in: ${kalenderScreenshotPath}`);

    return finalPath;
  }

  // Funktion zum direkten Navigieren zu einem spezifischen Monat über Rückwärts-Navigation
  async navigateToSpecificMonth(targetYear, targetMonth) {
    console.log(`🎯 Navigiere zu ${targetMonth} ${targetYear} über Rückwärts-Navigation...`);
    
    try {
      let navigationAttempts = 0;
      const maxNavigationAttempts = 50; // Sicherheitsgrenze
      
      while (navigationAttempts < maxNavigationAttempts) {
        const currentMonthInfo = await this.getCurrentMonthInfo();
        console.log(`📍 Aktueller Monat auf der Seite: ${currentMonthInfo}`);
        
        // Prüfe ob wir bereits beim Zielmonat sind
        if (currentMonthInfo && currentMonthInfo.includes(targetMonth) && currentMonthInfo.includes(targetYear)) {
          console.log(`✅ Zielmonat erreicht: ${currentMonthInfo}`);
          return true;
        }
        
        // Navigiere zum vorherigen Monat
        console.log(`⬅️ Navigiere zum vorherigen Monat...`);
        const navigationSuccess = await this.navigateToPreviousMonth();
        
        if (!navigationSuccess) {
          console.log(`❌ Navigation zum vorherigen Monat fehlgeschlagen`);
          return false;
        }
        
        navigationAttempts++;
        await this.page.waitForTimeout(2000); // Kurze Pause zwischen Navigationen
      }
      
      console.log(`❌ Maximale Anzahl von Navigationsversuchen erreicht`);
      return false;
      
    } catch (error) {
      console.log(`❌ Fehler bei der Rückwärts-Navigation: ${error.message}`);
      return false;
    }
  }

  async navigateToPreviousMonth() {
    try {
      const currentUrl = this.page.url();
      const currentMonthInfo = await this.getCurrentMonthInfo();
      
      console.log(`🔄 Versuche Navigation zum vorherigen Monat...`);
      console.log(`📍 Aktuelle URL: ${currentUrl}`);
      console.log(`📅 Aktueller Monat: ${currentMonthInfo}`);
      
      // Navigation mit Zurück-Pfeil (vorheriger Monat)
      const prevArrow = await this.page.locator('a.smcfiltermenuprev, a[title*="Zurück"], a[title*="Previous"], a:has-text("‹"), a:has-text("←")').first();
      
      if (await prevArrow.count() > 0) {
        console.log(`⬅️ Zurück-Pfeil gefunden - klicke...`);
        try {
          await prevArrow.click();
          await this.page.waitForTimeout(5000); // Längere Wartezeit
          
          const newUrl = this.page.url();
          const newMonthInfo = await this.getCurrentMonthInfo();
          
          console.log(`🔄 Neue URL: ${newUrl}`);
          console.log(`📅 Neuer Monat: ${newMonthInfo}`);
          
          return newUrl !== currentUrl && newMonthInfo !== currentMonthInfo;
        } catch (error) {
          console.log(`⚠️ Fehler beim Klicken des Zurück-Pfeils: ${error.message}`);
          return false;
        }
      }
      
      // Alternative: Dropdown-Navigation
      const dropdown = await this.page.locator('select[name*="month"], select[name*="monat"]').first();
      
      if (await dropdown.count() > 0) {
        console.log(`📋 Dropdown gefunden - versuche Navigation...`);
        const currentMonth = await dropdown.evaluate(el => el.value);
        const options = await dropdown.locator('option').all();
        const optionValues = [];
        
        for (const option of options) {
          const value = await option.getAttribute('value');
          const text = await option.textContent();
          optionValues.push({ value, text: text.trim() });
        }
        
        const currentIndex = optionValues.findIndex(o => o.value === currentMonth);
        if (currentIndex > 0) {
          const prevMonth = optionValues[currentIndex - 1];
          console.log(`📅 Wähle vorherigen Monat: ${prevMonth.text} (${prevMonth.value})`);
          await dropdown.selectOption(prevMonth.value);
          await this.page.waitForTimeout(3000);
          
          const newUrl = this.page.url();
          const newMonthInfo = await this.getCurrentMonthInfo();
          
          console.log(`🔄 Neue URL: ${newUrl}`);
          console.log(`📅 Neuer Monat: ${newMonthInfo}`);
          
          return newUrl !== currentUrl && newMonthInfo !== currentMonthInfo;
        } else {
          console.log(`⚠️ Kein vorheriger Monat im Dropdown verfügbar`);
        }
      }
      
      console.log(`❌ Keine Navigation zum vorherigen Monat möglich`);
      return false;
      
    } catch (error) {
      console.log(`❌ Fehler bei Navigation zum vorherigen Monat: ${error.message}`);
      return false;
    }
  }

  async navigateToNextMonth() {
    try {
      const currentUrl = this.page.url();
      const currentMonthInfo = await this.getCurrentMonthInfo();
      
      console.log(`🔄 Versuche Navigation zum nächsten Monat...`);
      console.log(`📍 Aktuelle URL: ${currentUrl}`);
      console.log(`📅 Aktueller Monat: ${currentMonthInfo}`);
      
      // Navigation mit Vorwärts-Pfeil (nächster Monat)
      const nextArrow = await this.page.locator('a.smcfiltermenunext, a[title*="Weiter"], a[title*="Next"], a:has-text("›"), a:has-text("→")').first();
      
      if (await nextArrow.count() > 0) {
        console.log(`➡️ Vorwärts-Pfeil gefunden - klicke...`);
        await nextArrow.click();
        await this.page.waitForTimeout(3000);
        
        const newUrl = this.page.url();
        const newMonthInfo = await this.getCurrentMonthInfo();
        
        console.log(`🔄 Neue URL: ${newUrl}`);
        console.log(`📅 Neuer Monat: ${newMonthInfo}`);
        
        return newUrl !== currentUrl && newMonthInfo !== currentMonthInfo;
      }
      
      // Alternative: Dropdown-Navigation
      const dropdown = await this.page.locator('select[name*="month"], select[name*="monat"]').first();
      
      if (await dropdown.count() > 0) {
        console.log(`📋 Dropdown gefunden - versuche Navigation...`);
        const currentMonth = await dropdown.evaluate(el => el.value);
        const options = await dropdown.locator('option').all();
        const optionValues = [];
        
        for (const option of options) {
          const value = await option.getAttribute('value');
          const text = await option.textContent();
          optionValues.push({ value, text: text.trim() });
        }
        
        const currentIndex = optionValues.findIndex(o => o.value === currentMonth);
        if (currentIndex >= 0 && currentIndex < optionValues.length - 1) {
          const nextMonth = optionValues[currentIndex + 1];
          console.log(`📅 Wähle nächsten Monat: ${nextMonth.text} (${nextMonth.value})`);
          await dropdown.selectOption(nextMonth.value);
          await this.page.waitForTimeout(3000);
          
          const newUrl = this.page.url();
          const newMonthInfo = await this.getCurrentMonthInfo();
          
          console.log(`🔄 Neue URL: ${newUrl}`);
          console.log(`📅 Neuer Monat: ${newMonthInfo}`);
          
          return newUrl !== currentUrl && newMonthInfo !== currentMonthInfo;
        } else {
          console.log(`⚠️ Kein nächster Monat im Dropdown verfügbar`);
        }
      }
      
      console.log(`❌ Keine Navigation zum nächsten Monat möglich`);
      return false;
      
    } catch (error) {
      console.log(`❌ Fehler bei Navigation zum nächsten Monat: ${error.message}`);
      return false;
    }
  }

  async getCurrentMonthInfo() {
    try {
      const monthInfoSelectors = [
        'h1:has-text("Kalender")',
        'h2:has-text("Kalender")',
        'h3:has-text("Kalender")',
        '.calendar-title',
        '.kalender-titel',
        '.page-title',
        'title'
      ];
      
      for (const selector of monthInfoSelectors) {
        try {
          const element = await this.page.locator(selector).first();
          if (await element.count() > 0) {
            const monthText = await element.textContent();
            if (monthText && monthText.trim()) {
              return monthText.trim();
            }
          }
        } catch (e) {
          // Weiter zum nächsten Selektor
        }
      }
      
      return null;
      
    } catch (error) {
      return null;
    }
  }

  // Funktion zum Ermitteln des nächsten zu downloadenden Monats
  async findNextMonthToDownload(outputDirectory) {
    console.log('🔍 Ermittle nächsten zu downloadenden Monat...');
    
    try {
      // Alle Jahresordner finden und sortieren (absteigend)
      const items = fs.readdirSync(outputDirectory);
      const yearFolders = items.filter(item => {
        const itemPath = path.join(outputDirectory, item);
        return fs.statSync(itemPath).isDirectory() && /^\d{4}$/.test(item);
      }).sort((a, b) => parseInt(b) - parseInt(a)); // Absteigend sortieren
      
      console.log(`📁 Gefundene Jahresordner: ${yearFolders.join(', ')}`);
      
      // Suche nach dem ersten Jahr ohne jahr_vollstaendig.txt
      let targetYear = null;
      for (const year of yearFolders) {
        const yearFolder = path.join(outputDirectory, year);
        const jahrVollständigDatei = path.join(yearFolder, 'jahr_vollstaendig.txt');
        
        if (!fs.existsSync(jahrVollständigDatei)) {
          targetYear = year;
          console.log(`🎯 Zieljahr gefunden: ${targetYear} (keine jahr_vollstaendig.txt)`);
          break;
        } else {
          console.log(`✅ Jahr ${year} ist vollständig (jahr_vollstaendig.txt vorhanden)`);
        }
      }
      
      // Wenn kein Jahr gefunden wurde, verwende das nächstkleinere Jahr
      if (!targetYear) {
        if (yearFolders.length > 0) {
          // Verwende das kleinste verfügbare Jahr
          targetYear = yearFolders[yearFolders.length - 1];
          console.log(`📅 Kein unvollständiges Jahr gefunden, verwende kleinstes verfügbares Jahr: ${targetYear}`);
        } else {
          // Wenn keine Jahresordner existieren, verwende das aktuelle Jahr
          const currentYear = new Date().getFullYear().toString();
          targetYear = currentYear;
          console.log(`📅 Keine Jahresordner gefunden, verwende aktuelles Jahr: ${targetYear}`);
        }
      }
      
      const targetYearFolder = path.join(outputDirectory, targetYear);
      
      // Prüfe ob der Jahresordner existiert, wenn nicht erstelle ihn
      if (!fs.existsSync(targetYearFolder)) {
        fs.mkdirSync(targetYearFolder, { recursive: true });
        console.log(`📁 Jahresordner erstellt: ${targetYearFolder}`);
        // Wenn kein Jahresordner existiert, ist Dezember der nächste Monat
        return {
          year: targetYear,
          month: 'Dezember',
          folderName: `Kalender_${targetYear}_Dezember`
        };
      }
      
      // Alle Monatsordner im Zieljahr finden
      const yearItems = fs.readdirSync(targetYearFolder);
      const monthFolders = yearItems.filter(item => {
        const itemPath = path.join(targetYearFolder, item);
        return fs.statSync(itemPath).isDirectory() && item.startsWith('Kalender_');
      });
      
      console.log(`📁 Gefundene Monatsordner in ${targetYear}: ${monthFolders.length}`);
      
      // Wenn keine Monatsordner existieren, ist Dezember der nächste Monat
      if (monthFolders.length === 0) {
        console.log(`📅 Keine Monatsordner gefunden, nächster Monat: Dezember ${targetYear}`);
        return {
          year: targetYear,
          month: 'Dezember',
          folderName: `Kalender_${targetYear}_Dezember`
        };
      }
      
      // Monate in umgekehrter Reihenfolge prüfen (Dezember bis Januar)
      const monthOrder = [
        'Dezember', 'November', 'Oktober', 'September', 'August', 
        'Juli', 'Juni', 'Mai', 'April', 'März', 'Februar', 'Januar'
      ];
      
      for (const month of monthOrder) {
        const monthFolderName = `Kalender_${targetYear}_${month}`;
        const monthFolderPath = path.join(targetYearFolder, monthFolderName);
        const monatVollständigDatei = path.join(monthFolderPath, 'monat_vollstaendig.txt');
        
        // Prüfe ob der Monatsordner existiert
        if (!fs.existsSync(monthFolderPath)) {
          console.log(`📅 Monat ${month} ${targetYear} existiert nicht, ist der nächste zu downloadende Monat`);
          return {
            year: targetYear,
            month: month,
            folderName: monthFolderName
          };
        }
        
        // Prüfe ob der Monat vollständig ist
        if (!fs.existsSync(monatVollständigDatei)) {
          console.log(`📅 Monat ${month} ${targetYear} ist unvollständig (keine monat_vollstaendig.txt), ist der nächste zu downloadende Monat`);
          return {
            year: targetYear,
            month: month,
            folderName: monthFolderName
          };
        } else {
          console.log(`✅ Monat ${month} ${targetYear} ist vollständig`);
        }
      }
      
      // Wenn alle Monate vollständig sind, prüfe das nächste Jahr
      console.log(`📅 Alle Monate in ${targetYear} sind vollständig, prüfe nächstes Jahr`);
      
      // Finde das nächstkleinere Jahr
      const currentYearIndex = yearFolders.indexOf(targetYear);
      if (currentYearIndex < yearFolders.length - 1) {
        const nextYear = yearFolders[currentYearIndex + 1];
        console.log(`📅 Prüfe nächstes Jahr: ${nextYear}`);
        return await this.findNextMonthToDownload(outputDirectory); // Rekursiver Aufruf
      } else {
        // Wenn kein kleineres Jahr existiert, verwende das aktuelle Jahr
        const currentYear = new Date().getFullYear().toString();
        console.log(`📅 Kein kleineres Jahr gefunden, verwende aktuelles Jahr: ${currentYear}`);
        return {
          year: currentYear,
          month: 'Dezember',
          folderName: `Kalender_${currentYear}_Dezember`
        };
      }
      
    } catch (error) {
      console.log(`❌ Fehler beim Ermitteln des nächsten Monats: ${error.message}`);
      // Fallback: Verwende aktuelles Jahr und Monat
      const now = new Date();
      const currentYear = now.getFullYear();
      const currentMonth = now.toLocaleString('de-DE', { month: 'long' });
      return {
        year: currentYear.toString(),
        month: currentMonth,
        folderName: `Kalender_${currentYear}_${currentMonth}`
      };
    }
  }

  // Hilfsfunktion zum Prüfen und Erstellen der jahr_vollstaendig.txt Datei
  async checkAndCreateYearCompleteFile(outputDirectory, monthFolderName, terminCount) {
    const januaryMatch = monthFolderName.match(/Kalender_(\d{4})_Januar/);
    if (januaryMatch) {
      const year = januaryMatch[1];
      const yearFolder = path.join(outputDirectory, year);
      const jahrVollständigDatei = path.join(yearFolder, 'jahr_vollstaendig.txt');
      
      if (!fs.existsSync(jahrVollständigDatei)) {
        const jahrVollständigInfo = `Jahr vollständig geladen: ${new Date().toISOString()}\nJanuar vollständig: ${terminCount} Termine\n`;
        fs.writeFileSync(jahrVollständigDatei, jahrVollständigInfo, 'utf8');
        console.log(`✅ Jahr ${year} als vollständig markiert (Januar abgeschlossen)`);
        return true;
      } else {
        console.log(`ℹ️ Jahr ${year} bereits als vollständig markiert`);
        return false;
      }
    }
    return false;
  }

  // Hilfsfunktion zum Verschieben bestehender Kalender-Ordner in Jahresordner
  async moveExistingCalendarFolders(outputDirectory) {
    console.log('🔄 Prüfe auf bestehende Kalender-Ordner im Hauptverzeichnis...');
    
    try {
      const items = fs.readdirSync(outputDirectory);
      const calendarFolders = items.filter(item => {
        const itemPath = path.join(outputDirectory, item);
        return fs.statSync(itemPath).isDirectory() && item.startsWith('Kalender_');
      });
      
      if (calendarFolders.length === 0) {
        console.log('✅ Keine Kalender-Ordner im Hauptverzeichnis gefunden');
        return;
      }
      
      console.log(`📁 Gefundene Kalender-Ordner: ${calendarFolders.length}`);
      
      for (const folder of calendarFolders) {
        const yearMatch = folder.match(/Kalender_(\d{4})_/);
        if (yearMatch) {
          const year = yearMatch[1];
          const yearFolder = path.join(outputDirectory, year);
          const sourcePath = path.join(outputDirectory, folder);
          const targetPath = path.join(yearFolder, folder);
          
          // Erstelle Jahresordner falls er nicht existiert
          if (!fs.existsSync(yearFolder)) {
            fs.mkdirSync(yearFolder, { recursive: true });
            console.log(`📁 Jahres-Ordner erstellt: ${yearFolder}`);
          }
          
          // Verschiebe den Ordner nur wenn er noch nicht im Jahresordner existiert
          if (!fs.existsSync(targetPath)) {
            fs.renameSync(sourcePath, targetPath);
            console.log(`✅ Ordner verschoben: ${folder} → ${year}/${folder}`);
          } else {
            console.log(`⚠️ Ordner existiert bereits im Jahresordner: ${year}/${folder}`);
          }
        } else {
          console.log(`⚠️ Kalender-Ordner ohne Jahr gefunden: ${folder}`);
        }
      }
      
      console.log('✅ Verschiebung der Kalender-Ordner abgeschlossen');
      
    } catch (error) {
      console.log(`❌ Fehler beim Verschieben der Kalender-Ordner: ${error.message}`);
    }
  }
}

module.exports = CalendarNavigator;
