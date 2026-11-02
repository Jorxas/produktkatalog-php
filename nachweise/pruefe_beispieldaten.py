"""Prueft ausschliesslich den synthetischen Datenvertrag von P09-T01."""

import csv
import hashlib
import io
import json
import platform
import re
from datetime import datetime, timezone
from pathlib import Path


def pruefen():
    datei = Path(__file__).resolve().parents[1] / "beispieldaten" / "produkte.csv"
    inhalt = datei.read_bytes()
    leser = csv.DictReader(io.StringIO(inhalt.decode("utf-8-sig"), newline=""))
    zeilen = list(leser)
    befunde = []
    erste_zeilen = {}
    struktur_gueltig = leser.fieldnames == [
        "artikelnummer", "bezeichnung", "preis", "bestand"
    ]
    for csv_zeile, zeile in enumerate(zeilen, start=2):
        if None in zeile or any(wert is None for wert in zeile.values()):
            struktur_gueltig = False
        for feld, muster in (
            ("artikelnummer", r"P[0-9]{2}"),
            ("bezeichnung", r"\S(?:.*\S)?"),
            ("preis", r"[0-9]+\.[0-9]{2}"),
            ("bestand", r"[0-9]+"),
        ):
            wert = zeile.get(feld) or ""
            if feld == "preis" and wert == "":
                befunde.append({"art": "preis_fehlt", "csv_zeile": csv_zeile})
            elif not re.fullmatch(muster, wert):
                befunde.append({
                    "art": "feld_ungueltig", "csv_zeile": csv_zeile, "feld": feld
                })
        artikelnummer = zeile.get("artikelnummer")
        if artikelnummer in erste_zeilen:
            befunde.append({
                "art": "artikelnummer_doppelt",
                "artikelnummer": artikelnummer,
                "csv_zeile": csv_zeile,
                "erste_csv_zeile": erste_zeilen[artikelnummer],
            })
        else:
            erste_zeilen[artikelnummer] = csv_zeile

    erwartete_befunde = [
        {"art": "artikelnummer_doppelt", "artikelnummer": "P01",
         "csv_zeile": 7, "erste_csv_zeile": 2},
        {"art": "preis_fehlt", "csv_zeile": 8},
    ]
    erfolgreich = struktur_gueltig and len(zeilen) == 7 and befunde == erwartete_befunde
    print(json.dumps({
        "projekt": "P09",
        "ticket": "P09-T01",
        "geprueft_am_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "eingabe": "beispieldaten/produkte.csv",
        "eingabe_sha256": hashlib.sha256(inhalt).hexdigest(),
        "anzahl_beispielzeilen": len(zeilen),
        "struktur_gueltig": struktur_gueltig,
        "befunde": befunde,
        "erwartung_erfuellt": erfolgreich,
        "grenze": "Lokale Datenpruefung; kein Import und keine Speicherung.",
    }, ensure_ascii=False, indent=2))
    return 0 if erfolgreich else 1


if __name__ == "__main__":
    raise SystemExit(pruefen())
