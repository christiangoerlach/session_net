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
            
            if (cleanText) {
              monatOrdnerName = cleanText;
              break;
            }
          }
        }
      } catch (e) {
        // Weiter zum nächsten Selektor
      }
    }
    
    return monatOrdnerName;
  }

  async saveCalendarPage(outputDirectory, monthFolderName) {
    const monatOrdner = path.join(outputDirectory, monthFolderName);
    if (!fs.existsSync(monatOrdner)) {
      fs.mkdirSync(monatOrdner, { recursive: true });
      console.log(`📁 Monats-Ordner erstellt: ${monatOrdner}`);
    } else {
      console.log(`📁 Monats-Ordner existiert bereits: ${monatOrdner}`);
    }

    // 📄 Kalender-Seite herunterladen
    console.log('💾 Speichere Kalender-Seite...');
    const kalenderHtml = await this.page.content();
    
    // HTML-Datei der Kalender-Seite im Monats-Ordner speichern
    const kalenderOutputPath = path.join(monatOrdner, 'kalender_seite.html');
    fs.writeFileSync(kalenderOutputPath, kalenderHtml, 'utf8');
    
    // Screenshot der Kalender-Seite im Monats-Ordner speichern
    const kalenderScreenshotPath = path.join(monatOrdner, 'kalender_seite_screenshot.png');
    await this.page.screenshot({ path: kalenderScreenshotPath, fullPage: true });
    
    console.log(`✅ Erfolgreich! Kalender-HTML gespeichert in: ${kalenderOutputPath}`);
    console.log(`📸 Kalender-Screenshot gespeichert in: ${kalenderScreenshotPath}`);

    return monatOrdner;
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
        await prevArrow.click();
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
}

module.exports = CalendarNavigator;
