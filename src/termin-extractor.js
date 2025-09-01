const fs = require('fs');
const path = require('path');

class TerminExtractor {
  constructor(page) {
    this.page = page;
  }

  async extractTermine(monthFolderPath) {
    console.log('📅 Extrahiere Termine des Monats...');
    
    // Prüfe ob bereits eine Cache-Datei mit Terminen existiert
    const cacheFilePath = path.join(monthFolderPath, 'extracted_termine.json');
    
    if (fs.existsSync(cacheFilePath)) {
      try {
        console.log('📋 Lade gecachte Termine aus Datei...');
        const cachedData = fs.readFileSync(cacheFilePath, 'utf8');
        const cachedTermine = JSON.parse(cachedData);
        
        // Prüfe ob die gecachten Daten gültig sind
        if (cachedTermine && cachedTermine.termine && Array.isArray(cachedTermine.termine) && cachedTermine.termine.length > 0) {
          console.log(`📊 ${cachedTermine.termine.length} gecachte Termine gefunden - verwende Cache`);
          return cachedTermine.termine;
        } else if (cachedTermine && Array.isArray(cachedTermine) && cachedTermine.length > 0) {
          // Fallback für alte Cache-Format
          console.log(`📊 ${cachedTermine.length} gecachte Termine gefunden (altes Format) - verwende Cache`);
          return cachedTermine;
        }
      } catch (error) {
        console.log('⚠️ Fehler beim Laden der gecachten Termine, extrahiere neu...');
        console.log(`   Fehler: ${error.message}`);
      }
    }
    
    console.log('🔄 Keine gecachten Termine gefunden - extrahiere Termine von der Webseite...');
    
    const terminSelectors = [
      'table tr td:nth-child(4)',  // 4. Spalte (Sitzung) der Tabelle
      'td[data-label="Sitzung"]', // Zellen mit data-label="Sitzung"
      '.silink',                   // Sitzungs-Link-Klassen
      '.smc-t-cl991.silink'       // Spezifische Sitzungs-Zellen
    ];
    
    let termine = [];
    
    // Durch alle Selektoren gehen und nach Terminen suchen
    for (const selector of terminSelectors) {
      try {
        const elements = await this.page.locator(selector).all();
        
        for (const element of elements) {
          try {
            const text = await element.textContent();
            if (text && text.trim()) {
              // Nach Termin-Links suchen (z.B. "Magistrat", "Ortsbeirat Grüningen")
              const terminLinks = await element.locator('a.smc_doc').all();
              
              for (const link of terminLinks) {
                try {
                  const linkText = await link.textContent();
                  if (linkText && linkText.trim()) {
                    // Den Tag aus der Zeile extrahieren (1. Spalte)
                    const row = await element.locator('xpath=..').first();
                    const dayCell = await row.locator('td:first-child span.weekday').first();
                    const dayText = await dayCell.textContent();
                    
                    if (dayText && dayText.match(/^\d{1,2}$/)) {
                      const tag = dayText.padStart(2, '0');
                      const terminName = linkText.trim();
                      
                      // Nur hinzufügen wenn es ein gültiger Termin ist
                      if (terminName.length > 2 && !terminName.match(/^\d+$/)) {
                        termine.push({ 
                          tag, 
                          terminName, 
                          originalText: linkText.trim(),
                          linkUrl: await link.getAttribute('href')
                        });
                      }
                    }
                  }
                } catch (e) {
                  // Link überspringen falls Fehler
                }
              }
            }
          } catch (e) {
            // Element überspringen falls Fehler
          }
        }
        
        // Wenn Termine gefunden wurden, aufhören
        if (termine.length > 0) {
          console.log(`🎯 Termine gefunden mit Selektor: ${selector}`);
          break;
        }
        
      } catch (e) {
        // Weiter zum nächsten Selektor
      }
    }
    
    // Alternative Methode: Alle Tabellenzeilen durchsuchen
    if (termine.length === 0) {
      console.log('🔍 Versuche alternative Termin-Extraktion über Tabellenzeilen...');
      
      const tableRows = await this.page.locator('table tr').all();
      for (const row of tableRows) {
        try {
          // Prüfe ob die Zeile einen Tag enthält
          const dayCell = await row.locator('td:first-child span.weekday').first();
          const dayText = await dayCell.textContent();
          
          if (dayText && dayText.match(/^\d{1,2}$/)) {
            // Suche nach Termin-Links in der 4. Spalte
            const sitzungCell = await row.locator('td:nth-child(4)').first();
            const terminLinks = await sitzungCell.locator('a.smc_doc').all();
            
            for (const link of terminLinks) {
              try {
                const linkText = await link.textContent();
                if (linkText && linkText.trim()) {
                  const tag = dayText.padStart(2, '0');
                  const terminName = linkText.trim();
                  
                  if (terminName.length > 2 && !terminName.match(/^\d+$/)) {
                    termine.push({ 
                      tag, 
                      terminName, 
                      originalText: linkText.trim(),
                      linkUrl: await link.getAttribute('href')
                    });
                  }
                }
              } catch (e) {
                // Link überspringen
              }
            }
          }
        } catch (e) {
          // Zeile überspringen
        }
      }
    }
    
    // Duplikate entfernen und sortieren
    const uniqueTermine = this.removeDuplicates(termine);
    
    console.log(`📊 ${uniqueTermine.length} eindeutige Termine gefunden:`);
    
    // Speichere die extrahierten Termine in einer Cache-Datei
    if (uniqueTermine.length > 0) {
      try {
        const cacheData = {
          extractedAt: new Date().toISOString(),
          monthFolder: path.basename(monthFolderPath),
          terminCount: uniqueTermine.length,
          termine: uniqueTermine
        };
        
        const cacheFilePath = path.join(monthFolderPath, 'extracted_termine.json');
        fs.writeFileSync(cacheFilePath, JSON.stringify(cacheData, null, 2), 'utf8');
        console.log(`💾 Termine in Cache-Datei gespeichert: ${cacheFilePath}`);
      } catch (error) {
        console.log(`⚠️ Fehler beim Speichern der Cache-Datei: ${error.message}`);
      }
    }
    
    return uniqueTermine;
  }

  removeDuplicates(termine) {
    const uniqueTermine = [];
    const seen = new Set();
    
    for (const termin of termine) {
      const key = `${termin.tag}_${termin.terminName}`;
      if (!seen.has(key)) {
        seen.add(key);
        uniqueTermine.push(termin);
      }
    }
    
    // Nach Tag sortieren
    uniqueTermine.sort((a, b) => parseInt(a.tag) - parseInt(b.tag));
    
    return uniqueTermine;
  }

  createTerminFolderName(termin) {
    return `${termin.tag}_${termin.terminName.replace(/[<>:"/\\|?*]/g, '_').replace(/\s+/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '')}`;
  }
}

module.exports = TerminExtractor;
