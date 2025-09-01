const fs = require('fs');
const path = require('path');
const DocumentDownloader = require('./document-downloader');

class TerminProcessor {
  constructor(page) {
    this.page = page;
    this.documentDownloader = new DocumentDownloader(page);
  }

  async processTermin(termin, monatOrdner, kalenderCurrentUrl) {
    const terminOrdnerName = `${termin.tag}_${termin.terminName.replace(/[<>:"/\\|?*]/g, '_').replace(/\s+/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '')}`;
    const terminOrdner = path.join(monatOrdner, terminOrdnerName);
    
    // Prüfen ob der Termin bereits vollständig geladen ist (direkt über Dateisystem)
    const terminVollständigGeladen = fs.existsSync(path.join(terminOrdner, 'termin_vollstaendig.txt'));
    if (terminVollständigGeladen) {
      console.log(`⏭️  ${termin.tag}. - ${termin.terminName} (bereits vollständig geladen)`);
      return;
    }
   
    if (!fs.existsSync(terminOrdner)) {
      fs.mkdirSync(terminOrdner, { recursive: true });
      console.log(`📁 Termin-Ordner erstellt: ${terminOrdnerName}`);
    } else {
      console.log(`📁 Termin-Ordner existiert bereits: ${terminOrdnerName}`);
    }
  
    // Termin-Informationen in JSON-Datei speichern
    const terminInfo = {
      tag: termin.tag,
      terminName: termin.terminName,
      originalText: termin.originalText,
      linkUrl: termin.linkUrl || null,
      ordnerName: terminOrdnerName,
      erstelltAm: new Date().toISOString()
    };
    
    const terminInfoPath = path.join(terminOrdner, 'termin_info.json');
    fs.writeFileSync(terminInfoPath, JSON.stringify(terminInfo, null, 2), 'utf8');
    
    console.log(`  📝 ${termin.tag}. - ${termin.terminName}`);
    
    // 🔗 Termin-Seite herunterladen (falls Link verfügbar)
    if (termin.linkUrl) {
      await this.downloadTerminPage(termin, terminOrdner, terminInfo, terminInfoPath);
      await this.processTopPoints(termin, terminOrdner, terminOrdnerName);
      
      // Zurück zur Kalender-Seite navigieren
      await this.page.goBack();
      await this.page.waitForTimeout(1000);
      
      // Markierungsdatei erstellen, dass der Termin vollständig geladen ist
      const terminVollständigDatei = path.join(terminOrdner, 'termin_vollstaendig.txt');
      const vollständigInfo = `Termin vollständig geladen: ${new Date().toISOString()}\n`;
      fs.writeFileSync(terminVollständigDatei, vollständigInfo, 'utf8');
      
      console.log(`    ✅ Termin vollständig geladen und in Fortschritt gespeichert`);
    } else {
      console.log(`    ⚠️ Kein Link für Termin verfügbar: ${termin.terminName}`);
      
      // Kein Link verfügbar
      terminInfo.terminSeiteGeladen = false;
      terminInfo.fehlermeldung = 'Kein Link verfügbar';
      fs.writeFileSync(terminInfoPath, JSON.stringify(terminInfo, null, 2), 'utf8');
    }
  }

  async downloadTerminPage(termin, terminOrdner, terminInfo, terminInfoPath) {
    try {
      console.log(`  🔗 Lade Termin-Seite herunter: ${termin.terminName}`);
      
      // Auf Termin-Seite navigieren
      const terminUrl = termin.linkUrl.startsWith('http') ? termin.linkUrl : new URL(termin.linkUrl, this.page.url()).href;
      await this.page.goto(terminUrl);
      
      // Warten bis Termin-Seite geladen ist
      await this.page.waitForTimeout(2000);
      
      // Termin-Seite HTML herunterladen
      const terminHtml = await this.page.content();
      const terminHtmlPath = path.join(terminOrdner, 'termin_seite.html');
      fs.writeFileSync(terminHtmlPath, terminHtml, 'utf8');
      
      // Screenshot der Termin-Seite machen
      const terminScreenshotPath = path.join(terminOrdner, 'termin_seite_screenshot.png');
      await this.page.screenshot({ path: terminScreenshotPath, fullPage: true });
      
      // Termin-Seite URL speichern
      const terminCurrentUrl = this.page.url();
      
      // Termin-Informationen aktualisieren
      terminInfo.terminSeiteUrl = terminCurrentUrl;
      terminInfo.terminSeiteHtml = 'termin_seite.html';
      terminInfo.terminSeiteScreenshot = 'termin_seite_screenshot.png';
      terminInfo.terminSeiteGeladen = true;
      
      // Aktualisierte Informationen speichern
      fs.writeFileSync(terminInfoPath, JSON.stringify(terminInfo, null, 2), 'utf8');
      
      console.log(`    ✅ Termin-Seite gespeichert: ${terminHtmlPath}`);
      console.log(`    📸 Termin-Screenshot gespeichert: ${terminScreenshotPath}`);
      console.log(`    🌐 Termin-Seite URL: ${terminCurrentUrl}`);
      
      // 🔍 Dokumente herunterladen
      await this.documentDownloader.downloadDocuments(terminOrdner, terminInfo.ordnerName);
      
    } catch (error) {
      console.log(`    ⚠️ Fehler beim Herunterladen der Termin-Seite: ${error.message}`);
      
      // Fehler-Informationen speichern
      terminInfo.terminSeiteGeladen = false;
      terminInfo.fehlermeldung = error.message;
      fs.writeFileSync(terminInfoPath, JSON.stringify(terminInfo, null, 2), 'utf8');
      
      // Fehler protokollieren
      console.log(`    ❌ Termin-Fehler: ${error.message}`);
    }
  }

  async processTopPoints(termin, terminOrdner, terminOrdnerName) {
    console.log(`    📋 Suche nach Tagesordnungspunkten...`);
    
    try {
      // Prüfe zuerst, ob wir auf einer Tagesordnungs-Seite sind (si0057.asp)
      const currentUrl = this.page.url();
      const isTagesordnungPage = currentUrl.includes('si0057.asp');
      
      if (!isTagesordnungPage) {
        console.log(`    ℹ️ Keine Tagesordnungs-Seite (${currentUrl}) - keine TOP-Links erwartet`);
        return;
      }
      
      console.log(`    🔍 Suche nach TOP-Links auf Tagesordnungs-Seite...`);
      
      // Suche nach TOP-Links in der Tagesordnungstabelle
      let topLinks = [];
      
      // Hauptselektor für TOP-Links
      try {
        topLinks = await this.page.locator('table tr .tolink a[href*="to0050.asp"], table tr .tolink a[href*="vo0050.asp"]').all();
        console.log(`    📊 Hauptselektor: ${topLinks.length} Tagesordnungspunkte gefunden`);
      } catch (e) {
        console.log(`    ⚠️ Hauptselektor fehlgeschlagen: ${e.message}`);
      }
      
      if (topLinks.length === 0) {
        // Alternative Suche nach TOP-Links mit verschiedenen Selektoren
        console.log(`    🔍 Alternative Suche nach TOP-Links...`);
        
        const alternativeSelectors = [
          'a[href*="to0050.asp"], a[href*="vo0050.asp"]',
          'table tr a[href*="to0050.asp"], table tr a[href*="vo0050.asp"]',
          '.tolink a[href*="to0050.asp"], .tolink a[href*="vo0050.asp"]',
          'a.smc_datatype_to[href*="to0050.asp"], a.smc_datatype_to[href*="vo0050.asp"]',
          'table a[href*="to0050.asp"], table a[href*="vo0050.asp"]',
          'tr a[href*="to0050.asp"], tr a[href*="vo0050.asp"]'
        ];
        
        for (const selector of alternativeSelectors) {
          try {
            const links = await this.page.locator(selector).all();
            if (links.length > 0) {
              topLinks = links;
              console.log(`    📊 Alternative Suche mit Selektor "${selector}": ${links.length} TOP-Links gefunden`);
              break;
            }
          } catch (e) {
            console.log(`    ⚠️ Fehler mit Selektor "${selector}": ${e.message}`);
          }
        }
      }
      
      if (topLinks.length === 0) {
        console.log(`    ℹ️ Keine TOP-Links gefunden - Termin hat keine Tagesordnungspunkte`);
        return;
      }
      
      console.log(`    ✅ ${topLinks.length} Tagesordnungspunkte gefunden - verarbeite...`);
      
      for (let i = 0; i < topLinks.length; i++) {
        try {
          const topLink = topLinks[i];
          const topName = await topLink.textContent();
          const topUrl = await topLink.getAttribute('href');
          
          console.log(`    🔗 TOP ${i + 1}: ${topName} -> ${topUrl}`);
          
          if (topName && topUrl) {
            await this.processSingleTop(topName, topUrl, i, terminOrdner, terminOrdnerName);
          }
        } catch (e) {
          console.log(`        ⚠️ Fehler bei TOP ${i + 1}: ${e.message}`);
        }
      }
    } catch (error) {
      console.log(`    ⚠️ Fehler beim Herunterladen der Tagesordnungspunkte: ${error.message}`);
    }
  }

  async processSingleTop(topName, topUrl, topIndex, terminOrdner, terminOrdnerName) {
    const cleanTopName = topName.trim().replace(/[<>:"/\\|?*]/g, '_').replace(/\s+/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '').substring(0, 100);
    const topOrdner = path.join(terminOrdner, `TOP_${topIndex + 1}_${cleanTopName}`);
    
    // Prüfen ob der TOP bereits vollständig geladen ist (direkt über Dateisystem)
    const topVollständigGeladen = fs.existsSync(path.join(topOrdner, 'top_vollstaendig.txt'));
    if (topVollständigGeladen) {
      console.log(`        ⏭️ TOP ${topIndex + 1}: ${topName} (bereits vollständig geladen)`);
      return;
    }
    
    if (!fs.existsSync(topOrdner)) {
      fs.mkdirSync(topOrdner, { recursive: true });
    }
    
    console.log(`      🔗 Lade Tagesordnungspunkt: ${topName}`);
    
    // Auf TOP-Seite navigieren
    const fullTopUrl = topUrl.startsWith('http') ? topUrl : new URL(topUrl, this.page.url()).href;
    await this.page.goto(fullTopUrl);
    await this.page.waitForTimeout(2000);
    
    // TOP-Seite HTML speichern
    const topHtml = await this.page.content();
    const topHtmlPath = path.join(topOrdner, 'top_seite.html');
    fs.writeFileSync(topHtmlPath, topHtml, 'utf8');
    
    // TOP-Seite Screenshot
    const topScreenshotPath = path.join(topOrdner, 'top_seite_screenshot.png');
    await this.page.screenshot({ path: topScreenshotPath, fullPage: true });
    
    // 🔍 Dokumente auf der TOP-Seite herunterladen
    await this.documentDownloader.downloadTopDocuments(topOrdner, terminOrdnerName, topIndex + 1, topName);
    
    // TOP-Informationen speichern
    const topInfo = {
      nummer: topIndex + 1,
      name: topName.trim(),
      url: fullTopUrl,
      htmlDatei: 'top_seite.html',
      screenshot: 'top_seite_screenshot.png',
      erstelltAm: new Date().toISOString()
    };
    
    const topInfoPath = path.join(topOrdner, 'top_info.json');
    fs.writeFileSync(topInfoPath, JSON.stringify(topInfo, null, 2), 'utf8');
    
    console.log(`        ✅ TOP-Seite gespeichert: ${topHtmlPath}`);
    console.log(`        📸 TOP-Screenshot gespeichert: ${topScreenshotPath}`);
    
    // TOP-Markierungsdatei erstellen, dass der TOP vollständig geladen ist
    const topVollständigDatei = path.join(topOrdner, 'top_vollstaendig.txt');
    const topVollständigInfo = `TOP vollständig geladen: ${new Date().toISOString()}\n`;
    fs.writeFileSync(topVollständigDatei, topVollständigInfo, 'utf8');
    
    // Zurück zur Termin-Seite
    await this.page.goBack();
    await this.page.waitForTimeout(1000);
  }
}

module.exports = TerminProcessor;

