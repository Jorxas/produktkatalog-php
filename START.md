# Technischer Einstieg — P09

## P09-T01 lokal prüfen

Im Projektordner ausführen:

~~~powershell
uv run --offline --python 3.12 python -X utf8 nachweise/pruefe_beispieldaten.py
~~~

Verwendet die vorhandene Python-Laufzeit ohne zusätzliche Pakete. Tatsächlich ausgeführt mit Python 3.12.14. Der Check liest die sieben Originaldatensätze und gibt einen JSON-Bericht mit Zeitpunkt, Python-Version, Eingabe-Prüfsumme und Befunden aus. Er prüft Kopfzeile, Feldformate und die erwarteten Fehler. Regeln und Abgrenzung: [P09-T01](tickets/P09-T01.md).

Erwartet: `artikelnummer_doppelt` für `P01` in CSV-Zeile 7 (erstmals Zeile 2) und `preis_fehlt` in Zeile 8. Die Kopfzeile zählt mit. Exitcode 0 bestätigt genau diese Erwartung bei sieben Datensätzen, Exitcode 1 eine Abweichung. Die Originaldaten bleiben unverändert. Kein Datenbankimport und keine Produktansicht.

So wurde der Nachweis mit PowerShell gesichert:

~~~powershell
uv run --offline --python 3.12 python -X utf8 nachweise/pruefe_beispieldaten.py | Set-Content -LiteralPath nachweise\P09-T01-pruefung.json -Encoding UTF8
$pruefExitcode = $LASTEXITCODE
Get-Content -LiteralPath nachweise\P09-T01-pruefung.json -Encoding UTF8
Write-Output "Pruef-Exitcode: $pruefExitcode"
exit $pruefExitcode
~~~

Der letzte Befehl beendet die Shell mit dem Prüfstatus; den Block in einer eigenen PowerShell ausführen. Gesichertes Ergebnis: [P09-T01-pruefung.json](nachweise/P09-T01-pruefung.json). Dateien unter `nachweise/` können von Git ausgeschlossen sein; der übergeordnete Dienst muss den Nachweis beim Sichern des Arbeitsstands ausdrücklich übernehmen.

## PHP-Import P09-T02 lokal ausführen

Voraussetzung: 64-Bit-PHP mit PDO SQLite. Tatsächlich vorhanden: `C:\xampp\php\php.exe`, PHP 8.2.12, PDO SQLite mit SQLite 3.39.2. PHP steht hier nicht im PATH. Keine weiteren Pakete erforderlich. Im Projektordner ausführen:

~~~powershell
& C:\xampp\php\php.exe src/importieren.php
~~~

Standard: `beispieldaten/produkte.csv` nach `ausgabe/katalog.sqlite`. Optional beide Pfade angeben: `& C:\xampp\php\php.exe src/importieren.php eingabe.csv ausgabe/mein-katalog.sqlite`. Das Ausgabe-Verzeichnis muss vorhanden sein. Neue Datenbankdateien werden angelegt; eine Migration älterer Datenbankschemata gehört nicht zu T02.

CSV: UTF-8 ohne BOM, Komma, exakt die Kopfzeile `artikelnummer,bezeichnung,preis,bestand`. Feldregeln aus T01 gelten; zusätzlich höchstens `999999999.99` für Preis und `2147483647` für Bestand. Preise werden ohne Gleitkommazahl als `preis_cent` gespeichert. Die erste Artikelnummer innerhalb einer Datei reserviert die Nummer auch bei einer ungültigen Zeile; weitere Vorkommen werden abgelehnt. Ein neuer Importlauf darf gültige Werte vorhandener Artikel aktualisieren.

JSON-Ausgabe zählt gelesene, angelegte, aktualisierte und abgelehnte Datensätze. Exitcode 0 bedeutet technisch abgeschlossenen Import, auch bei fachlichen Ablehnungen; Exitcode 1 technischen Fehler oder falsche Kopfzeile. Ein technischer Fehler innerhalb der Transaktion rollt den Lauf zurück. Ablehnungen stehen in `abgelehnte_zeilen` mit `laufnummer`, `csv_zeile`, unverändertem `originalzeile`-Inhalt und `fehler_json`; frühere Ablehnungen bleiben erhalten. `csv_zeile` zählt logische CSV-Datensätze einschließlich Kopfzeile, bei mehrzeiligen Feldern keine physischen Textzeilen.

## Reproduzierbare lokale T02-Abnahme

~~~powershell
& C:\xampp\php\php.exe -l src/importieren.php
uv run --offline --python 3.12 python -X utf8 nachweise/pruefe_php_import.py C:/xampp/php/php.exe
~~~

Die Abnahme startet echte PHP-CLI-Prozesse und liest die gespeicherte SQLite-Datei unabhängig mit Python 3.12.14/SQLite 3.53.1. Jeder Aufruf erhält einen neuen Unterordner in `ausgabe/`; keine Originaldaten werden ersetzt. Zwei Importe prüfen Anlage, Preisaktualisierung ohne doppeltes P01, Schutz bestehender Produkte, Nullwerte, ungültige Formate, Feldzahl und Zahlenbereiche. Alle elf Ablehnungen werden mit dem ursprünglichen CSV-Text verglichen. Eine falsche Kopfzeile wird mit Exitcode 1 ohne Datenänderung abgewiesen. Das Prüfprogramm endet bei erfüllter Erwartung mit Exitcode 0 und schreibt `nachweise/P09-T02-pruefung.json` selbst als UTF-8.

Die konkreten Befehle und der geprüfte Datenbankpfad stehen im Bericht. Nachweise und die dort genannte Datenbank samt erzeugter Prüfeingaben müssen vom übergeordneten Dienst ausdrücklich gesichert werden; `nachweise/` und `ausgabe/` können von Git ausgeschlossen sein. Fertigstellung und Zeitmessung: [Abschlussnachweis](nachweise/P09-T02-abschluss.md). Veröffentlichung bleibt ausstehend. Shopansicht, Idempotenz-Gesamtabnahme und Plattformadapter gehören zu gesonderten Phasen.

## Produktansicht und Vertragsprüfung P09-T03

Voraussetzung bleibt PHP mit PDO SQLite, keine weiteren Pakete. Die HTML-Ansicht nutzt standardmäßig `ausgabe/katalog.sqlite`. Im Projektordner:

~~~powershell
& C:\xampp\php\php.exe src/importieren.php
& C:\xampp\php\php.exe -S 127.0.0.1:8099 -t oeffentlich
~~~

Danach `http://127.0.0.1:8099/` öffnen; Server mit Strg+C beenden. Nur `oeffentlich/` ausliefern, damit CSV, Datenbank und Importskript nicht im Webverzeichnis liegen. Kein Import beim Seitenaufruf. Optional vor dem Serverstart `$env:KATALOG_DATENBANK = (Resolve-Path 'ausgabe/mein-katalog.sqlite').Path` setzen; anschließend mit `Remove-Item Env:KATALOG_DATENBANK` zurücksetzen. Keine HTTP-Auswahl des Datenbankpfads.

Die Seite zeigt Produkte und ausschließlich Ablehnungen des letzten Importlaufs. Ohne Importlauf erscheint ein entsprechender Hinweis, ohne Produkte eine leere Tabelle. Fehlende/nicht lesbare Datenbank: HTTP 503 und verständliche Meldung. Keine Datei wird dafür angelegt. Preise bleiben lokale Preiseinheiten, da Währung und Steuerbezug ungeklärt sind.

Kleinste automatisierte T03-Abnahme:

~~~powershell
& C:\xampp\php\php.exe -l oeffentlich/index.php
uv run --offline --python 3.12 python -X utf8 nachweise/pruefe_produktansicht.py C:/xampp/php/php.exe
~~~

Erwartet: beide Exitcode 0. Das Prüfskript importiert die sieben unveränderten Originalzeilen einmal in eine neue Datenbank unter `ausgabe/P09-T03-…/`. Es startet PHP ausschließlich an `127.0.0.1` auf freien Ports und beendet jeden Server selbst. Geprüft werden tatsächlich ausgelieferte HTML-Tabellenwerte (fünf Produkte), beide Fehler, Antwort-Header, fehlende Datenbank (503, keine Dateianlage), maskierte Sonderzeichen und Nullwerte in einer separaten Kopie sowie unveränderte Originaldaten und Katalogdatenbank. Der JSON-Vertragsentwurf wird anhand seines vollständigen Beispiels mit den importierten Werten verglichen. Kein wiederholter Import, keine T04-Abnahme und keine visuelle Browserprüfung.

Ergebnis wird als UTF-8 nach `nachweise/P09-T03-pruefung.json` geschrieben. Der Bericht nennt genaue Prozessbefehle, Laufzeitenversionen und den Ausgabeordner mit HTML-Antworten, Serverprotokollen und Datenbanken. Zur Wiederholung erforderlich: `nachweise/pruefe_produktansicht.py`, `nachweise/P09-T03-vertragsbeispiel.json`, `oeffentlich/index.php`, `src/importieren.php`, `sql/schema.sql` und `beispieldaten/produkte.csv` sowie diese Anleitung und [T03-Vertrag](tickets/P09-T03.md). Diese Dateien, Berichte und Ausgabeordner ausdrücklich durch den übergeordneten Dienst mitsichern; ignorierte Nachweise werden nicht automatisch veröffentlicht.

Die geplante Route `/api/katalog` ist nicht implementiert. Der Adapter zur echten Shopware Admin API ist beschrieben und ungefertigt; vor seiner Ausführung sind Plattformzugang, Version, Rechte, Währung und Steuern zu klären. Keine Simulation ersetzt Shopware oder Pimcore.

## Identischen Import wiederholen — P09-T04

Im Projektordner mit der vorhandenen PHP-/Python-Laufzeit ausführen:

~~~powershell
uv run --offline --python 3.12 python -X utf8 nachweise/pruefe_idempotenz.py C:/xampp/php/php.exe
~~~

Erwartet: Exitcode 0. Keine zusätzlichen Pakete, Konten oder Server nötig. Das Skript startet zweimal `C:/xampp/php/php.exe src/importieren.php` mit derselben Original-CSV und derselben neuen Datenbank in einem eigenen Ausgabeunterordner. Es liest SQLite unabhängig mit Python und vergleicht alle vier Produktfelder, die fünf eindeutigen Artikelnummern, beide Importzähler und die originalgetreuen Ablehnungen samt Gründen. Die sieben vorhandenen Beispielzeilen bleiben unverändert; eine feste SHA256-Prüfsumme schützt ihren Ausgangsstand.

Erster Lauf: fünf angelegt, null aktualisiert, zwei abgelehnt. Zweiter Lauf: null angelegt, fünf aktualisiert, zwei abgelehnt. Produktbestand unverändert, P01 weiterhin 550 Cent. Die Gesamtdatenbank wächst auf zwei Importläufe und vier Ablehnungen; `aktualisiert` zählt auch das erneute Setzen gleicher Werte. Keine globale Idempotenz der Importhistorie behauptet. Kein Shopware-Plugin oder Plattformtest; Einzelheiten und fehlende Plattformvoraussetzungen in [P09-T04](tickets/P09-T04.md).

Das Skript schreibt `nachweise/P09-T04-pruefung.json` als UTF-8 mit tatsächlichen Befehlen, Exitcodes und beiden vollständigen Datenständen. Jeder Aufruf erstellt eine neue Datenbank; vorhandene Ausgaben bleiben erhalten. Zur Wiederholung erforderlich sind ausschließlich diese regulären Projektdateien: `nachweise/pruefe_idempotenz.py`, `src/importieren.php`, `sql/schema.sql` und `beispieldaten/produkte.csv`; Anleitung und Abnahmeumfang stehen in `START.md` und `tickets/P09-T04.md`. Keine T01–T03-Prüfskripte oder Vertragsbeispiele erforderlich.

Der Bericht nennt die tatsächlich geprüfte SQLite-Datei. Diese Datei, Prüfskript, Prüfbericht, `nachweise/P09-T04-abschluss.md`, `nachweise/P09-T04-dateistand.json`, `nachweise/P09-T04-diff-pruefung.txt` sowie die erforderlichen Projektdateien ausdrücklich durch den übergeordneten Dienst mitsichern. Ignorierte Nachweise werden nicht automatisch veröffentlicht. Gesamtabnahme und echte Plattformvarianten bleiben offen; nach diesem Endpunkt keine weiteren Arbeiten.

## Technische Quellen

- [Python-CSV-Modul](https://docs.python.org/3/library/csv.html)

Vor dem Einbinden eines Frameworks dessen aktuelle offizielle Anleitung lesen.
