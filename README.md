# MN-Screener mit automatischen Kursdaten

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

## Trend-Momentum-Regeln

Die App setzt zusätzlich die Regeln aus dem Doc „Trend-Momentum-Strategie für Aktien“ um. Alle Werte sind unter „Momentum-Strategie“ einstellbar, die Momentum-Regeln und die Marktsperre lassen sich abschalten (dann rechnet die App wie vorher).

- **Indexfilter:** Das Skript holt täglich S&P 500 (`^GSPC`) und VIX (`^VIX`). Neukäufe sind gesperrt, wenn der S&P 500 unter seiner 200-Tage-Linie schließt oder zum letzten Monatsende unter dem 10-Monats-Durchschnitt lag. Bei Rot werden Kaufkandidaten gesperrt (die Karte nennt den Grund).
- **Investitionsgrad:** bis 100 %, bei Monatssignal unter dem Durchschnitt bis 50 %. Volatilitätsbremse: Markt mehr als 10 % unter dem Hoch und VIX über 30 halbiert den Grad, danach Wiedereinstieg in Drittel pro Woche. Die Schwellen sind Annahmen.
- **Momentum-Score:** Durchschnitt der Prozentränge von 12-1-Monats-Rendite und Clenow-Wert (annualisierte exponentielle Steigung über 90 Tage × R²). Kauf nur aus den besten 20 %, Ausstieg bei Rang schlechter als Top 30 %. Zusätzlich: Kurs über der 100-Tage-Linie, keine Tagesbewegung über 15 % in 90 Tagen, Kurs mindestens 10 $, Tagesumsatz mindestens 20 Mio. $.
- **Positionsgröße:** Stück = Depot × r ÷ ATR(20), Standard r = 0,25 %, Obergrenze 15 % je Position. Das Skript berechnet die ATR(20) aus Hoch, Tief und Schluss und legt sie in `prices.json` ab. Wahlweise bleibt die bisherige Rechnung nach Stop-Loss.
- **Frog in the Pan:** Gleichmäßigkeit des Anstiegs (Gewinn- gegen Verlusttage im 12-1-Fenster). Als Filter nutzbar, indem du unter „Momentum-Strategie“ einen Prozentwert einträgst (Gray/Vogel: 50). Standard 0 = aus, der Wert steht aber immer auf der Karte.
- **Sektor:** Steht oben auf jeder Karte und in der Depotliste, die Liste lässt sich danach sortieren. Das Skript liest ihn aus den Indexlisten. Fehlt er dort (etwa bei Nasdaq-Werten ohne S&P-500-Mitgliedschaft), ergänzt es ihn aus `universe/sectors.csv` und sonst von Yahoo. Was danach noch fehlt, nennt der Lauf als Hinweis. Trage es dann in `universe/sectors.csv` ein (Zeile `TICKER,Sektor`).
- **Sektorgrenze:** Das Skript liest den Sektor aus den Indexlisten. Ab der eingestellten Zahl an Positionen je Sektor (Standard 3) warnt die Karte, die Kandidatensumme überspringt den Titel. Fehlt der Sektor, greift die Grenze dort nicht.
- **Depot-Ampel:** Zusätzlich Rot bei Kurs unter der 100-Tage-Linie, Rang schlechter als Top 30 % oder Kurslücke über 15 % im 90-Tage-Fenster.
- Konnten S&P 500 oder VIX nicht geladen werden, läuft der Rest weiter. Die App zeigt dann nur die Marktbreite deiner Liste, und es gibt keine Marktsperre.
- Die Rechenwege stehen in der App unter „So rechnet die App“. Das ist ein Regelwerk aus der Literatur und keine Anlageberatung. Backtests mit den heutigen Indexmitgliedern sind durch Survivorship Bias zu optimistisch.

## Ranglisten

Oben in der App (Bereich „Ranglisten“) stehen zwei getrennte Top-15-Listen über alle geladenen Aktien:

- **Rangliste nach Minervini:** nur Aktien mit voll erfülltem Trend Template (Kriterien 1 bis 7 und RS-Rating mindestens wie eingestellt, egal ob neu oder schon länger erfüllt), sortiert nach dem Stärke-Score (60 % RS-Rating, 40 % Nähe zum 52-Wochen-Hoch).
- **Rangliste nach Trendstärke:** alle Aktien nach dem Momentum-Score (Durchschnitt der Prozentränge von 12-1-Monats-Rendite und Clenow-Wert), auch wenn sie das Template nicht erfüllen.

Jede Zeile zeigt Sektor, die wichtigsten Kennzahlen, den Rang in der jeweils anderen Liste und den Kaufstatus (Marktfilter und Momentum-Regeln wie bei den Kandidaten). Ein Tipp auf die Zeile öffnet unten alle Daten der Aktie. Die Listen folgen den abgewählten Indizes und sind eine Rangfolge, keine Kaufempfehlung.

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
