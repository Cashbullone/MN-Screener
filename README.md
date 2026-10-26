# Minervini-Screener mit automatischen Kursdaten

GitHub holt jeden Börsentag nach US-Börsenschluss die Kurse von **S&P 500, Nasdaq-100 und Russell 2000**
und veröffentlicht sie zusammen mit der App als Webseite. Du öffnest nur den Link, die App lädt die
aktuellen Daten selbst. Eine Excel-Tabelle ist nicht mehr nötig (sie funktioniert aber weiter).

## Einrichtung (einmalig, ca. 10 Minuten)

1. **Konto anlegen:** auf github.com ein kostenloses Konto erstellen.
2. **Repository anlegen:** oben rechts „+“ → „New repository“. Name zum Beispiel `minervini-screener`,
   Sichtbarkeit **Public** (nur dann ist GitHub Pages kostenlos). Auf „Create repository“ klicken.
3. **Veröffentlichung einschalten (vor dem Hochladen):** im Repository „Settings“ → „Pages“ →
   bei „Source“ **GitHub Actions** wählen.
4. **Dateien hochladen:** ZIP entpacken. Im Repository „Add file“ → „Upload files“ und die Ordner
   `scripts`, `site`, `universe` sowie die Dateien `.gitignore` und `README.md` hineinziehen,
   dann „Commit changes“.
5. **Automatik-Datei anlegen:** der Ordner `.github` ist unsichtbar und lässt sich oft nicht hochladen.
   Deshalb: „Add file“ → „Create new file“, als Dateiname `.github/workflows/update.yml` eintippen
   (die Schrägstriche legen die Ordner an) und den Inhalt der mitgelieferten Datei `update.yml` einfügen.
   „Commit changes“.
6. **Ersten Lauf starten:** Reiter „Actions“ → „Kurse aktualisieren und Seite veröffentlichen“ →
   „Run workflow“. Der erste Lauf dauert etwa 10 bis 25 Minuten. Danach läuft die Automatik
   Montag bis Freitag von selbst (22:30 UTC, also 23:30 oder 00:30 Uhr österreichischer Zeit).
7. **App öffnen:** Adresse `https://DEIN-NAME.github.io/minervini-screener/`. Auf dem Handy kannst du die Seite
   über das Teilen-Menü zum Home-Bildschirm hinzufügen.

## Was wo gespeichert wird

- Im Repository liegen nur die App und das Skript. Die Kursdaten entstehen bei jedem Lauf neu und gehen
  direkt auf die Webseite, sie füllen das Repository also nicht.
- Dein Depot, deine Einstellungen und manuell eingetragene RS-Ratings bleiben **nur in deinem Browser**.
  Auf einem zweiten Gerät übertragst du sie mit „Depot exportieren“ und „Depot importieren“.
- Die Webseite ist öffentlich erreichbar, wer den Link kennt, sieht die Kurse (aber nicht dein Depot).
  Die Kursdaten stammen von Yahoo Finance und sind für den privaten Gebrauch gedacht. Gib den Link
  deshalb nicht weiter.

## Einstellungen

In `update.yml` unter „Kursdaten holen“ kannst du die auskommentierten Zeilen aktivieren:

- `MIN_PRICE` Mindestkurs in USD (Standard 5)
- `MIN_AVG_VOL` Mindest-Durchschnittsvolumen der letzten 50 Tage in Aktien (Standard 100000)
- `INDEXES` zum Beispiel `SP500,NDX`, wenn du den Russell 2000 nicht brauchst (der Abruf wird dann viel schneller)

Welche Indizes gescreent werden, wählst du außerdem direkt in der App über die Häkchen.

## Wenn etwas nicht klappt

- **Lauf schlägt fehl (roter Haken unter „Actions“):** den Lauf öffnen und die Meldung bei „Kursdaten holen“
  ansehen. Der Lauf bricht absichtlich ab, wenn weniger als 300 Aktien herauskommen. Die Seite zeigt dann
  weiter die Daten vom letzten erfolgreichen Lauf.
- **Yahoo blockiert Abrufe:** passiert gelegentlich. Einfach „Run workflow“ erneut starten.
- **Russell-2000-Liste nicht lesbar:** das Skript nutzt dann `universe/russell2000.txt`, falls du die Datei angelegt hast.
- **Nach 60 Tagen ohne Änderung im Repository** pausiert GitHub geplante Läufe. Dann unter „Actions“ wieder aktivieren.
- **Firmennamen und Wechselkurs** (USD je EUR) kommen mit den täglichen Daten. Namen stammen aus den Indexlisten, der Kurs von Yahoo (EURUSD=X). Ist der Kurs einmal nicht abrufbar, gilt der Wert, der in der App steht.
- **KGV** gibt es in der automatischen Variante nicht, die Anzeige zeigt dann „nicht verfügbar“.
- Der Russell 2000 stammt aus den Beständen des iShares-ETFs IWM und entspricht dem Index nahezu vollständig.
