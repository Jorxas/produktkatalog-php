# Produktkatalog und Datenaustausch im E-Commerce

Stand: 13. November 2026 — **P09-T04 lokal erledigt: identischen Import wiederholt und Produktbestand verglichen; Gesamtabnahme offen**. Veröffentlichung und Commit durch den übergeordneten Dienst stehen aus. Ursprüngliches Basisziel 7./8. November verfehlt; Fortsetzung gemäß Einzelphasenfreigabe. Geschätzter Basisaufwand: 4 Stunden ohne Einrichtung und Erweiterungen.

Ein kleiner Laden möchte einen Katalog importieren, ohne Preise zu verlieren oder Duplikate anzulegen.

Ergebnis: CSV-Import mit PHP und Synchronisationsvertrag; Shopware und Pimcore als eigene Adaptervarianten.

Vorgesehene Technologien: PHP/Symfony, MySQL/MariaDB, Shopware, Pimcore, JavaScript/TypeScript, HTML/CSS. Eine Nennung ist kein Nachweis einer Umsetzung.

## Einstieg

1. [Lastenheft](LASTENHEFT.md) lesen.
2. [Erstes Ticket](tickets/P09-T01.md) öffnen.
3. [Technischen Einstieg](START.md) prüfen und ein Ticket nach dem anderen bearbeiten.
4. [Arbeitsjournal](ARBEITSJOURNAL.md) und echte Nachweise aktualisieren.

Abhängigkeiten: keine weiteren Projekte.

## Geprüfter Endpunkt P09-T01

Der [Datenvertrag im Ticket](tickets/P09-T01.md) beschreibt Artikelnummer, Bezeichnung, Preis und Bestand. Ein lokaler Python-Check mit Python 3.12.14 bestätigt sieben unveränderte synthetische Beispielzeilen: `P01` ist in CSV-Zeile 7 gegenüber Zeile 2 doppelt, bei `P06` fehlt in Zeile 8 der Preis. Genau diese zwei Befunde werden erwartet; ein erfolgreicher Check erklärt die Eingabe nicht für fehlerfrei.

Ausführung: [Startanleitung](START.md). Ergebnis: [Prüfprotokoll](nachweise/P09-T01-pruefung.json). Der T01-Check importiert und speichert nichts; PHP wurde erst in T02 ausgeführt.

## Geprüfter Endpunkt P09-T02

[PHP-Import](src/importieren.php) validiert vor der Speicherung, speichert Preise als ganze Cent und aktualisiert über die eindeutige Artikelnummer. Spätere Vorkommen innerhalb derselben Datei werden abgelehnt. SQLite bewahrt Originalzeile, Fehlergrund und Importlauf dauerhaft auf. Die sieben Originaldatensätze bleiben unverändert.

Tatsächlich ausgeführt: PHP 8.2.12 mit PDO SQLite 3.39.2. Erster Import: fünf Produkte, zwei Ablehnungen. Zweiter gezielter Import: P01 von 550 auf 600 Cent aktualisiert, ein gültiges Nullwertprodukt angelegt, neun fehlerhafte Zeilen abgelehnt; bestehende Werte geschützt. [Abnahmebericht](nachweise/P09-T02-pruefung.json) und [Abschlussnachweis](nachweise/P09-T02-abschluss.md). A1/A2 wurden für dieses lokale Szenario geprüft; die übergreifenden Lastenheftkriterien bleiben bis zur gesonderten Gesamtabnahme unverändert offen. Keine Shopansicht, keine Ausführung von Symfony, Shopware oder Pimcore. Folgephasen wurden nicht begonnen.

## Geprüfter Endpunkt P09-T03

Die [PHP-Produktansicht](oeffentlich/index.php) zeigt die fünf gültigen Produkte und die zwei verständlichen Fehler des letzten Imports aus den sieben unveränderten Beispielzeilen. Preise erscheinen mit zwei Nachkommastellen; Währung und Steuerbezug sind ausdrücklich ungeklärt. Die Seite liest nur, importiert nichts und maskiert gespeicherte Texte für HTML.

Der [API-Vertrag mit Shopware-Zuordnung](tickets/P09-T03.md) beschreibt einen späteren JSON-Lesezugriff und den Adapter zur echten Admin API. Das [Vertragsbeispiel](nachweise/P09-T03-vertragsbeispiel.json) wurde gegen SQLite geprüft. Keine laufende JSON-API, kein Plattformadapter und kein praktischer Shopware-/Pimcore-Nachweis. Echter Austausch bleibt ohne Instanz, Zugang und Preisdefinition blockiert; T03 ist auf Ansicht und Vertrag begrenzt.

Tatsächlich geprüft über lokale PHP-HTTP-Prozesse: fünf Tabellenzeilen und zwei Fehler, HTTP 503 bei fehlender Datenbank, maskierte Sonderzeichen und sichtbare Nullwerte. [Prüfbericht](nachweise/P09-T03-pruefung.json), [Abschluss und Zeitmessung](nachweise/P09-T03-abschluss.md), Wiederholung in [START.md](START.md). Keine visuelle Browserabnahme. T04 wurde gesondert am 13. November geprüft; die übergreifende Lastenheftabnahme bleibt offen.

## Geprüfter Endpunkt P09-T04

Zwei echte PHP-Importe derselben sieben unveränderten CSV-Datensätze in dieselbe neue SQLite-Datei ergeben jeweils genau dieselben fünf Produkte. Die Wiederholung legt keinen Artikel an; Bezeichnung, Preis und Bestand bleiben identisch. P01 bleibt bei 550 Cent. Beide Läufe lehnen CSV-Zeilen 7 und 8 ab. Idempotent ist der Produktbestand; die Importhistorie wächst auf zwei Läufe und vier Ablehnungen. Der Zähler `aktualisiert: 5` bedeutet hier vorhandene Artikel, keine fachliche Wertänderung.

Der eigene PHP-CLI-Import mit SQLite ist kein Shopware-Plugin. Weder der Vertragsentwurf noch dieser Test belegen Shopware oder Pimcore; echte Plattformvarianten bleiben ohne Zugang und Ausführung blockiert. [Ticket und Abgrenzung](tickets/P09-T04.md), [Prüfbericht](nachweise/P09-T04-pruefung.json), [Abschluss](nachweise/P09-T04-abschluss.md). Kleinste Wiederholungsprüfung in [START.md](START.md). Nur T04 lokal abgenommen, keine Gesamtabnahme oder Folgephase.

[Erweiterungen](VARIANTEN.md) haben einen eigenen Umsetzungsstand. Private Unternehmenszuordnungen sind nicht Teil dieses Arbeitsbaums.

## Projektsprache

Dokumentation, selbst gewählte Bezeichner, Kommentare, Meldungen und Beispieldaten werden auf Deutsch geschrieben. Festgelegte API-Schlüssel, Sprachsyntax und Produktnamen bleiben unverändert.
