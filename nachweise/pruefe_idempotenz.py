"""T04: dieselbe CSV zweimal mit echtem PHP importieren und SQLite vergleichen."""

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
    eingabe = projektordner / "beispieldaten/produkte.csv"
    original = eingabe.read_bytes()
    pruefsumme = hashlib.sha256(original).hexdigest()
    assert pruefsumme == "a85cc8c878b5e8f3b996c8db1121cc9292fde70ae5f527811844bfb4ebe7ef71", "Originaldaten weichen ab."
    zeilen = list(csv.reader(io.StringIO(original.decode("utf-8"), newline="")))
    assert len(zeilen) == 8, "Kopfzeile und sieben Originaldatensaetze erwartet."
    originalzeilen = original.decode("utf-8").splitlines(keepends=True)
    pruefordner = projektordner / "ausgabe" / ("P09-T04-" + uuid4().hex)
    pruefordner.mkdir(parents=True)
    datenbankpfad = pruefordner / "katalog.sqlite"
    befehle = []
    staende = []
    ergebnisse = []
    erwartete_produkte = [
        ("P01", "Demokabel", 550, 10),
        ("P02", "Demosensor", 1200, 4),
        ("P03", "Demogehaeuse", 890, 8),
        ("P04", "Demostecker", 250, 30),
        ("P05", "Demohalterung", 600, 15),
    ]

    for laufnummer in (1, 2):
        befehl = [php, "src/importieren.php", str(eingabe), str(datenbankpfad)]
        lauf = subprocess.run(befehl, cwd=projektordner, capture_output=True,
                              text=True, encoding="utf-8", timeout=30)
        befehle.append({"befehl": befehl, "exitcode": lauf.returncode,
                        "ausgabe": lauf.stdout, "fehlerausgabe": lauf.stderr})
        assert lauf.returncode == 0, "PHP-Import fehlgeschlagen: " + lauf.stderr
        ergebnis = json.loads(lauf.stdout)
        assert ergebnis == {
            "laufnummer": laufnummer, "gelesen": 7,
            "angelegt": 5 if laufnummer == 1 else 0,
            "aktualisiert": 0 if laufnummer == 1 else 5, "abgelehnt": 2,
        }, "Unerwartete Importzaehler."
        ergebnisse.append(ergebnis)
        with sqlite3.connect(datenbankpfad) as datenbank:
            produkte = datenbank.execute(
                "SELECT artikelnummer, bezeichnung, preis_cent, bestand FROM produkte ORDER BY artikelnummer"
            ).fetchall()
            assert produkte == erwartete_produkte, "Produktwerte oder Produktanzahl weichen ab."
            assert datenbank.execute(
                "SELECT COUNT(DISTINCT artikelnummer) FROM produkte"
            ).fetchone()[0] == 5, "Artikelnummern sind nicht eindeutig."
            laeufe = datenbank.execute(
                "SELECT laufnummer, eingabe FROM importlaeufe ORDER BY laufnummer"
            ).fetchall()
            assert laeufe == [(nummer, str(eingabe)) for nummer in range(1, laufnummer + 1)]
            ablehnungen = datenbank.execute(
                "SELECT laufnummer, csv_zeile, originalzeile, fehler_json "
                "FROM abgelehnte_zeilen ORDER BY laufnummer, csv_zeile"
            ).fetchall()
            assert len(ablehnungen) == 2 * laufnummer
            for nummer in range(1, laufnummer + 1):
                aktuelle = [zeile for zeile in ablehnungen if zeile[0] == nummer]
                assert [zeile[1] for zeile in aktuelle] == [7, 8]
                for _, csv_zeile, rohtext, fehler in aktuelle:
                    assert rohtext == originalzeilen[csv_zeile - 1], "Ablehnung veraendert Originaltext."
                    erwarteter_fehler = (
                        "Artikelnummer in dieser Datei doppelt; erstmals CSV-Zeile 2."
                        if csv_zeile == 7 else
                        "Preis fehlt oder ist kein nicht negativer Betrag mit zwei Nachkommastellen."
                    )
                    assert json.loads(fehler) == [erwarteter_fehler]
            if staende:
                assert produkte == staende[0]["produkte"], "Wiederholung veraendert Produktbestand."
                assert ablehnungen[:2] == staende[0]["ablehnungen"], "Fruehere Ablehnungen wurden veraendert."
                assert ablehnungen[2:][0][1:] == ablehnungen[0][1:]
                assert ablehnungen[2:][1][1:] == ablehnungen[1][1:]
            staende.append({"produkte": produkte, "importlaeufe": laeufe, "ablehnungen": ablehnungen})

    assert eingabe.read_bytes() == original, "Originaldatei wurde veraendert."
    versionsbefehl = [php, "-v"]
    version = subprocess.run(versionsbefehl, capture_output=True, text=True,
                             encoding="utf-8", check=True, timeout=30)
    befehle.append({"befehl": versionsbefehl, "exitcode": version.returncode,
                    "ausgabe": version.stdout, "fehlerausgabe": version.stderr})
    bericht = {
        "projekt": "P09", "ticket": "P09-T04", "erwartung_erfuellt": True,
        "geprueft_am_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "sqlite_version_der_lesepruefung": sqlite3.sqlite_version,
        "php_version": version.stdout.splitlines()[0],
        "original_sha256": pruefsumme, "anzahl_originaldatensaetze": 7,
        "importe": ergebnisse, "staende": staende,
        "produktbestand_idempotent": True,
        "gesamtdatenbank_idempotent": False,
        "erklaerung": "Fuenf identische Produkte; zwei Importlaeufe und vier Ablehnungen. "
                       "Aktualisiert zaehlt vorhandene Artikel, auch bei unveraenderten Werten.",
        "grenze": "Eigener PHP-CLI-Import mit SQLite, kein Shopware-Plugin. "
                  "Keine praktische Ausfuehrung von Shopware, Pimcore, Symfony oder MySQL; keine Gesamtabnahme.",
        "datenbank": datenbankpfad.relative_to(projektordner).as_posix(),
        "befehle": befehle,
    }
    berichtspfad = projektordner / "nachweise/P09-T04-pruefung.json"
    berichtspfad.write_text(json.dumps(bericht, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(bericht, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    pruefen()
