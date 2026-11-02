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

## Späterer PHP-Einstiegspunkt (in T01 nicht ausgeführt)

Voraussetzungen: PHP mit PDO SQLite; MySQL oder MariaDB sowie die echte Plattform für entsprechende Varianten.

~~~powershell
php src/importieren.php
~~~

Das Startprogramm meldet den Initialisierungsstand. Fachfunktionen sind bewusst noch nicht implementiert und melden dies bei einem Aufruf. Fehlende Bibliotheken und Frameworks erst im passenden Ticket mit ihrer tatsächlichen Version ergänzen.

## Nächste gesonderte Phase

P09-T02: PHP-Import mit Eingabeprüfung und Speicherung. Erst nach eigener Freigabe beginnen. Die Lastenheft-Abnahme bleibt offen.

## Technische Quellen

- [Python-CSV-Modul](https://docs.python.org/3/library/csv.html)

Vor dem Einbinden eines Frameworks dessen aktuelle offizielle Anleitung lesen.
