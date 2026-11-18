"""Lokale T02-Abnahme: echter PHP-Prozess, anschliessend SQLite unabhaengig lesen."""

import csv
import hashlib
import io
import json
import platform
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def pruefen():
    projektordner = Path(__file__).resolve().parents[1]
    php = sys.argv[1] if len(sys.argv) > 1 else "php"
    original = projektordner / "beispieldaten/produkte.csv"
    originalinhalt = original.read_bytes()
    zeilen = list(csv.reader(io.StringIO(originalinhalt.decode("utf-8"), newline="")))
    assert len(zeilen) == 8, "Sieben Originaldatensaetze erwartet."
    pruefordner = projektordner / "ausgabe" / ("P09-T02-" + uuid4().hex)
    pruefordner.mkdir()
    datenbankpfad = pruefordner / "katalog.sqlite"
    befehle = []

    def ausfuehren(eingabe, erwarteter_exitcode=0):
        befehl = [php, "src/importieren.php", str(eingabe), str(datenbankpfad)]
        lauf = subprocess.run(befehl, cwd=projektordner, capture_output=True, text=True, encoding="utf-8")
        befehle.append({"befehl": befehl, "exitcode": lauf.returncode,
                        "ausgabe": lauf.stdout.strip(), "fehlerausgabe": lauf.stderr.strip()})
        assert lauf.returncode == erwarteter_exitcode, lauf.stderr
        return json.loads(lauf.stdout) if erwarteter_exitcode == 0 else None

    erster_import = ausfuehren(original)
    assert erster_import == {"laufnummer": 1, "gelesen": 7, "angelegt": 5, "aktualisiert": 0, "abgelehnt": 2}
    with sqlite3.connect(datenbankpfad) as datenbank:
        assert datenbank.execute("SELECT COUNT(*) FROM produkte").fetchone()[0] == 5
        assert datenbank.execute("SELECT preis_cent FROM produkte WHERE artikelnummer='P01'").fetchone()[0] == 550
        ablehnungen = datenbank.execute("SELECT csv_zeile, originalzeile, fehler_json FROM abgelehnte_zeilen ORDER BY csv_zeile").fetchall()
        assert [zeile[0] for zeile in ablehnungen] == [7, 8]
        originalzeilen = originalinhalt.decode("utf-8").splitlines(keepends=True)
        for nummer, rohtext, fehler in ablehnungen:
            assert rohtext == originalzeilen[nummer - 1]
            assert json.loads(fehler)
        assert datenbank.execute("SELECT COUNT(*) FROM produkte WHERE artikelnummer='P06'").fetchone()[0] == 0

    # Bestehendes P01 mit der vorhandenen zweiten Preisversion aktualisieren.
    # Weitere synthetische Fehler pruefen den Schutz bestehender Werte und Zahlengrenzen.
    zweite_eingabe = pruefordner / "aktualisierung.csv"
    fehlerzeilen = [
        ["P02", "Preis fehlt", "", "4"],
        ["P03", "Negativer Preis", "-1.00", "8"],
        ["P04", "Falsches Preisformat", "2,50", "30"],
        ["P05", "Ungueltiger Bestand", "6.00", "-1"],
        ["P06", " Zu viel Leerraum", "1.00", "3"],
        ["falsch", "Ungueltige Nummer", "1.00", "3"],
        ["P07", "Preis zu gross", "1000000000.00", "1"],
        ["P08", "Bestand zu gross", "1.00", "2147483648"],
        ["P09", "Feld fehlt", "1.00"],
        ["P10", "Erlaubte Nullwerte", "0.00", "0"],
    ]
    with zweite_eingabe.open("w", encoding="utf-8", newline="") as ausgabe:
        csv.writer(ausgabe).writerows([zeilen[0], zeilen[6], *fehlerzeilen])
    zweiter_import = ausfuehren(zweite_eingabe)
    assert zweiter_import == {"laufnummer": 2, "gelesen": 11, "angelegt": 1, "aktualisiert": 1, "abgelehnt": 9}
    with sqlite3.connect(datenbankpfad) as datenbank:
        produkte = datenbank.execute("SELECT * FROM produkte ORDER BY artikelnummer").fetchall()
        assert produkte == [
            ("P01", "Demokabel neuer Preis", 600, 10),
            ("P02", "Demosensor", 1200, 4),
            ("P03", "Demogehaeuse", 890, 8),
            ("P04", "Demostecker", 250, 30),
            ("P05", "Demohalterung", 600, 15),
            ("P10", "Erlaubte Nullwerte", 0, 0),
        ], "Aktualisierung oder Schutz bestehender Produkte fehlgeschlagen."
        assert datenbank.execute("SELECT COUNT(*) FROM abgelehnte_zeilen").fetchone()[0] == 11
        zweite_originalzeilen = zweite_eingabe.read_bytes().decode("utf-8").splitlines(keepends=True)
        for nummer, rohtext, fehler in datenbank.execute("SELECT csv_zeile, originalzeile, fehler_json FROM abgelehnte_zeilen WHERE laufnummer=2"):
            assert rohtext == zweite_originalzeilen[nummer - 1]
            assert json.loads(fehler)

    falscher_kopf = pruefordner / "falscher_kopf.csv"
    falscher_kopf.write_text("artikelnummer,preis\nP01,0.00\n", encoding="utf-8")
    ausfuehren(falscher_kopf, 1)
    with sqlite3.connect(datenbankpfad) as datenbank:
        assert datenbank.execute("SELECT COUNT(*) FROM importlaeufe").fetchone()[0] == 2
        assert datenbank.execute("SELECT * FROM produkte ORDER BY artikelnummer").fetchall() == produkte
        sqlite_version = datenbank.execute("SELECT sqlite_version()").fetchone()[0]
    assert original.read_bytes() == originalinhalt, "Originaldaten wurden veraendert."
    php_version = subprocess.run([php, "-v"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    bericht = {
        "projekt": "P09", "ticket": "P09-T02", "erwartung_erfuellt": True,
        "geprueft_am_utc": datetime.now(timezone.utc).isoformat(),
        "php_version": php_version, "python_version": platform.python_version(),
        "sqlite_version_der_unabhaengigen_lesepruefung": sqlite_version,
        "original_sha256": hashlib.sha256(originalinhalt).hexdigest(),
        "anzahl_originaldatensaetze": 7,
        "erster_import": erster_import, "zweiter_import": zweiter_import,
        "produkte_nach_zweitem_import": produkte,
        "ablehnungen_dauerhaft_und_originalgetreu": 11,
        "falsche_kopfzeile_ohne_datenveraenderung_abgewiesen": True,
        "pruefordner": pruefordner.relative_to(projektordner).as_posix(),
        "befehle": befehle,
        "grenze": "Nur PHP-CLI und SQLite; keine Shopansicht oder Plattformadapter, keine T04-Gesamtabnahme.",
    }
    berichtspfad = projektordner / "nachweise/P09-T02-pruefung.json"
    berichtspfad.write_text(json.dumps(bericht, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(bericht, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    pruefen()
