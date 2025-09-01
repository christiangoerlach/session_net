const fs = require('fs');
const path = require('path');

class ConfigManager {
  constructor() {
    this.config = this.loadConfig();
  }

  loadConfig() {
    // Konfiguration aus config.env laden
    require('dotenv').config({ path: './config.env' });
    
    return {
      website: {
        url: process.env.WEBSITE_URL,
        username: process.env.WEBSITE_USERNAME,
        password: process.env.WEBSITE_PASSWORD
      },
      output: {
        directory: process.env.OUTPUT_DIRECTORY || 'pohlheim_geschuetzt',
        progressFile: 'download_fortschritt.txt',
        failedDownloadsFile: 'failed_downloads.txt'
      },
      browser: {
        headless: true,
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
      },
      download: {
        timeout: 30000,
        retryAttempts: 3,
        maxFileSize: 100 * 1024 * 1024 // 100MB
      },
      selectors: {
        login: {
          username: 'input[name="username"], input[name="user"], #username, input[type="text"]',
          password: 'input[name="password"], input[name="pass"], #password, input[type="password"]',
          submit: 'input[type="submit"], button[type="submit"], #loginButton, .login-button, button:has-text("Login"), button:has-text("Anmelden")'
        },
        calendar: [
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
        ],
        month: [
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
        ],
        termin: [
          'table tr td:nth-child(4)',
          'td[data-label="Sitzung"]',
          '.silink',
          '.smc-t-cl991.silink'
        ],
        document: 'a[title*="Dokument Download"], a[aria-label*="Dokument Download"]',
        top: 'table tr .tolink a[href*="to0050.asp"]'
      }
    };
  }

  get(key) {
    return key.split('.').reduce((obj, k) => obj && obj[k], this.config);
  }

  validate() {
    const required = ['website.url', 'website.username', 'website.password'];
    const missing = required.filter(key => !this.get(key));
    
    if (missing.length > 0) {
      throw new Error(`Fehlende Konfiguration: ${missing.join(', ')}`);
    }
    
    return true;
  }
}

module.exports = ConfigManager;
