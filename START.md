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

## Technische Quellen

- [Python-CSV-Modul](https://docs.python.org/3/library/csv.html)

Vor dem Einbinden eines Frameworks dessen aktuelle offizielle Anleitung lesen.
