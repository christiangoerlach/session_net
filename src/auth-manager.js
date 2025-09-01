class AuthManager {
  constructor(page) {
    this.page = page;
  }

  async login(websiteUrl, username, password) {
    console.log('📱 Öffne Login-Seite...');
    await this.page.goto(websiteUrl);

    // ⏳ Kurz warten, bis die Seite geladen ist
    await this.page.waitForTimeout(2000);

    // 🧑‍💻 Login-Daten eingeben
    console.log('🔑 Führe Login durch...');
    
    // Benutzername eingeben
    await this.page.fill('input[name="username"], input[name="user"], #username, input[type="text"]', username);
    
    // Passwort eingeben
    await this.page.fill('input[name="password"], input[name="pass"], #password, input[type="password"]', password);
    
    // Login-Button klicken (versuche verschiedene Selektoren)
    const loginButton = await this.page.locator('input[type="submit"], button[type="submit"], #loginButton, .login-button, button:has-text("Login"), button:has-text("Anmelden")').first();
    await loginButton.click();

    // ⏳ Warten bis Weiterleitung abgeschlossen ist
    console.log('⏳ Warte auf Weiterleitung...');
    await this.page.waitForTimeout(3000);

    console.log('✅ Login erfolgreich abgeschlossen');
  }

  async isLoggedIn() {
    // Prüfe ob wir auf einer authentifizierten Seite sind
    const currentUrl = this.page.url();
    return !currentUrl.includes('login') && !currentUrl.includes('auth');
  }
}

module.exports = AuthManager;
