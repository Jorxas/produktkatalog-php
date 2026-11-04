# Produktkatalog und Datenaustausch im E-Commerce

Stand: 3. November 2026 — **P09-T02 lokal erledigt: PHP-Import mit SQLite geprüft; Shopansicht und Gesamtabnahme offen**. Veröffentlichung und Commit durch den übergeordneten Dienst stehen aus. Geplanter Abschluss der Basis: 2026-11-07, spätestens 8. November 2026. Geschätzter Basisaufwand: 4 Stunden ohne Einrichtung und Erweiterungen.

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

[Erweiterungen](VARIANTEN.md) haben einen eigenen Umsetzungsstand. [Private Unternehmenszuordnung](UNTERNEHMEN.lokal.md) bleibt außerhalb der Git-Verwaltung.

## Projektsprache

Dokumentation, selbst gewählte Bezeichner, Kommentare, Meldungen und Beispieldaten werden auf Deutsch geschrieben. Festgelegte API-Schlüssel, Sprachsyntax und Produktnamen bleiben unverändert.
