# MN-Screener (Minervini) mit automatischen Kursdaten

GitHub holt jeden Börsentag nach US-Börsenschluss die Kurse von **S&P 500 und Nasdaq-100** (jede Aktie nur einmal, der Russell 2000 ist optional)
und veröffentlicht sie zusammen mit der App als Webseite. Du öffnest nur den Link, die App lädt die
aktuellen Daten selbst. Eine Excel-Tabelle ist nicht mehr nötig (sie funktioniert aber weiter).

## Einrichtung (einmalig, ca. 10 Minuten)

1. **Konto anlegen:** auf github.com ein kostenloses Konto erstellen.
2. **Repository anlegen:** oben rechts „+“ → „New repository“. Name zum Beispiel `MN-Screener`,
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
7. **App öffnen:** Adresse `https://DEIN-NAME.github.io/MN-Screener/`. Auf dem Handy kannst du die Seite
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
- `INDEXES` Standard ist `SP500,NDX`. Mit `SP500,NDX,R2000` kommt der Russell 2000 dazu (der Abruf dauert dann deutlich länger)

Welche Indizes gescreent werden, wählst du außerdem direkt in der App über die Häkchen. Aktien, die in beiden Indizes stehen, zählen zum S&P 500 und erscheinen nicht doppelt.

## Was die App zeigt

Der MN-Screener enthält **nur die Minervini-Strategie**. Die Turtle-Regeln stehen im TU-Screener, die reine Momentum-Strategie im MO-Screener, jeder ist ein eigenständiger Screener mit eigenem Repository.

- **Trend Template:** die acht Kriterien (Kurs über 150- und 200-Tage-Linie, 150 über 200, 200-Tage-Linie steigt seit einem Monat, 50 über 150 und 200, Kurs über 50, mindestens 30 % über dem 52-Wochen-Tief, höchstens 25 % unter dem 52-Wochen-Hoch, RS-Rating mindestens 80). Das RS-Rating rechnet die App selbst unter allen geladenen Aktien.
- **Orderzettel:** siehe unten.
- **Depot:** Ampel je Position (Rot: Template verletzt, Stop-Loss oder letzte Verkaufsstufe erreicht, Gelb: Teilverkauf fällig), Verkaufsstufen, Stop-Methoden (fest, Trailing, 50-Tage-Linie), Tausch-Hinweis, Live-Kurse über Finnhub (optional).
- **Rangliste:** die 15 stärksten Aktien mit erfülltem Trend Template, sortiert nach dem Stärke-Score (60 % RS-Rating, 40 % Nähe zum 52-Wochen-Hoch). Ein Tipp auf die Zeile öffnet unten alle Daten der Aktie. Das ist eine Rangfolge, keine Kaufempfehlung.
- **Marktampel:** Marktbreite deiner geladenen Liste (Anteil über der 200- und 50-Tage-Linie). Sie warnt nur und sperrt nichts.
- **Positionsgröße:** Stück = Depot × Risiko % ÷ (Einstieg × Stop-Loss %), begrenzt auf die maximale Position.
- **Sektor:** steht auf jeder Karte, im Orderzettel und in der Depotliste, die Liste lässt sich danach sortieren. Das Skript liest ihn aus den Indexlisten. Fehlt er dort (etwa bei Nasdaq-Werten ohne S&P-500-Mitgliedschaft), ergänzt es ihn aus `universe/sectors.csv` und sonst von Yahoo. Was danach noch fehlt, nennt der Lauf als Hinweis (Zeile `TICKER,Sektor` in die Datei eintragen).

## Orderzettel

Der Bereich „Orderzettel“ steht ganz oben und zeigt, was beim nächsten Handelstag zu tun ist. Jede Zeile nennt Ticker, Firmenname und Sektor, den Kurs, die Stückzahl und einen Hinweis.

- **Verkaufen:** Positionen mit erreichtem Stop-Loss, verletztem Trend Template oder erreichter letzter Verkaufsstufe. Verkauft wird die gesamte Restposition.
- **Teilverkauf:** eine Verkaufsstufe (zum Beispiel +25 % → 10 % der Position) ist erreicht, die Stückzahl steht in der Zeile.
- **Kaufen:** die Kaufkandidaten (Template neu erfüllt, RS ab Mindestwert) in der Reihenfolge des Stärke-Scores, mit Stückzahl aus der Positionsgröße und der Stop-Loss-Marke. Die Käufe rechnen mit den freien Plätzen („Max. Positionen“) und dem freien Geld, das die Verkäufe freigeben. Passt der nächste Kandidat nicht mehr, nennt die App den Grund.
- **Aufträge für deine offenen Positionen:** je Position die Stop-Order (Marke nach deiner Stop-Methode) und die nächste Verkaufsstufe als Limit-Order.
- **„Verkauf erledigt“ / „Kauf erledigt“:** trägt die Ausführung ins Depot ein (verkaufte Stück beziehungsweise neue Position zum angezeigten Kurs). Den echten Einstiegskurs kannst du im Depot nachtragen.

Hinweis zu den Daten: Das Skript legt in `prices.json` weiterhin S&P 500, VIX und die ATR ab. Der MN-Screener nutzt sie nicht mehr.

Das ist ein Regelwerk aus der Literatur und keine Anlageberatung. Backtests mit den heutigen Indexmitgliedern sind durch Survivorship Bias zu optimistisch.

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
