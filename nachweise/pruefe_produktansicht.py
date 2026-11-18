"""T03: PHP-Ansicht ueber lokales HTTP und Vertragsbeispiel gegen SQLite pruefen."""

import csv
import hashlib
import json
import os
import platform
import shutil
import socket
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from uuid import uuid4


class TabellenLeser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.zeilen = []
        self.zeile = []
        self.zelle = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.zeile = []
        if tag == "td":
            self.zelle = ""

    def handle_data(self, data):
        if self.zelle is not None:
            self.zelle += data

    def handle_endtag(self, tag):
        if tag == "td":
            self.zeile.append(self.zelle)
            self.zelle = None
        if tag == "tr" and self.zeile:
            self.zeilen.append(self.zeile)


def pruefen():
    projektordner = Path(__file__).resolve().parents[1]
    php = sys.argv[1] if len(sys.argv) > 1 else "php"
    original = projektordner / "beispieldaten/produkte.csv"
    originalinhalt = original.read_bytes()
    assert len(list(csv.reader(originalinhalt.decode("utf-8").splitlines()))) == 8
    pruefordner = projektordner / "ausgabe" / ("P09-T03-" + uuid4().hex)
    pruefordner.mkdir()
    datenbankpfad = pruefordner / "katalog.sqlite"
    befehl = [php, "src/importieren.php", str(original), str(datenbankpfad)]
    lauf = subprocess.run(befehl, cwd=projektordner, capture_output=True, text=True, encoding="utf-8", check=True)
    importergebnis = json.loads(lauf.stdout)
    assert importergebnis == {"laufnummer": 1, "gelesen": 7, "angelegt": 5, "aktualisiert": 0, "abgelehnt": 2}
    beispiel = json.loads((projektordner / "nachweise/P09-T03-vertragsbeispiel.json").read_text(encoding="utf-8"))
    with sqlite3.connect(datenbankpfad) as datenbank:
        datenbank.row_factory = sqlite3.Row
        produkte = [dict(zeile) for zeile in datenbank.execute("SELECT * FROM produkte ORDER BY artikelnummer")]
    assert beispiel == {"vertragsversion": 1, "waehrung": None, "steuerbezug": "ungeklaert", "produkte": produkte}, "Vertragsbeispiel weicht von Importdaten ab."
    datenbankinhalt = datenbankpfad.read_bytes()
    http_ergebnisse = []
    serverbefehle = []

    def abrufen(datenbank, name):
        with socket.socket() as verbindung:
            verbindung.bind(("127.0.0.1", 0))
            port = verbindung.getsockname()[1]
        serverbefehl = [php, "-S", f"127.0.0.1:{port}", "-t", "oeffentlich"]
        serverbefehle.append({"befehl": serverbefehl, "KATALOG_DATENBANK": str(datenbank.relative_to(projektordner))})
        umgebung = {**os.environ, "KATALOG_DATENBANK": str(datenbank)}
        with (pruefordner / f"{name}-server.txt").open("w", encoding="utf-8") as protokoll:
            server = subprocess.Popen(serverbefehl, cwd=projektordner, env=umgebung, stdout=protokoll, stderr=protokoll,
                                      creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            try:
                frist = time.monotonic() + 5
                while True:
                    try:
                        antwort = urlopen(f"http://127.0.0.1:{port}/", timeout=1)
                        break
                    except HTTPError as fehler:
                        antwort = fehler
                        break
                    except URLError:
                        if server.poll() is not None or time.monotonic() >= frist:
                            raise
                        time.sleep(0.05)  # Nur auf die tatsaechliche Serverbereitschaft warten.
                with antwort:
                    status = antwort.code
                    inhalt = antwort.read().decode("utf-8")
                    assert antwort.headers["Content-Type"] == "text/html; charset=UTF-8"
                    assert antwort.headers["Cache-Control"] == "no-store"
                (pruefordner / f"{name}.html").write_text(inhalt, encoding="utf-8")
                http_ergebnisse.append({"szenario": name, "status": status, "html": (pruefordner / f"{name}.html").relative_to(projektordner).as_posix()})
                return status, inhalt
            finally:
                server.terminate()
                server.wait(timeout=5)

    status, inhalt = abrufen(datenbankpfad, "katalog")
    assert status == 200
    leser = TabellenLeser()
    leser.feed(inhalt)
    assert leser.zeilen == [
        ["P01", "Demokabel", "5,50", "10"], ["P02", "Demosensor", "12,00", "4"],
        ["P03", "Demogehaeuse", "8,90", "8"], ["P04", "Demostecker", "2,50", "30"],
        ["P05", "Demohalterung", "6,00", "15"],
    ], "Produkte oder sichtbare Preise stimmen nicht."
    assert 'lang="de"' in inhalt and 'scope="col"' in inhalt
    assert "CSV-Zeile 7: Artikelnummer in dieser Datei doppelt; erstmals CSV-Zeile 2." in inhalt
    assert "CSV-Zeile 8: Preis fehlt" in inhalt
    assert "Währung und Steuerbezug sind noch nicht festgelegt" in inhalt
    assert datenbankpfad.read_bytes() == datenbankinhalt, "Ansicht hat die Datenbank veraendert."

    fehlender_pfad = pruefordner / "fehlt.sqlite"
    status, inhalt = abrufen(fehlender_pfad, "fehlende-datenbank")
    assert status == 503 and "Bitte CSV-Import und SQLite-Datenbank prüfen" in inhalt
    assert not fehlender_pfad.exists(), "Ansicht hat eine fehlende Datenbank angelegt."

    # Gesonderte Kopie: HTML-Auszeichnung bleibt Text; Nullpreis und Nullbestand sind sichtbar.
    pruefkopie = pruefordner / "sonderzeichen.sqlite"
    shutil.copyfile(datenbankpfad, pruefkopie)
    with sqlite3.connect(pruefkopie) as datenbank:
        datenbank.execute("UPDATE produkte SET bezeichnung=?, preis_cent=0, bestand=0 WHERE artikelnummer='P01'", ('<script>alert("Prüfung")</script> & Zubehör',))
        datenbank.execute("UPDATE abgelehnte_zeilen SET fehler_json=? WHERE csv_zeile=7", (json.dumps(['Fehler <script> & "Text"']),))
    status, inhalt = abrufen(pruefkopie, "sonderzeichen")
    assert status == 200 and "<script>" not in inhalt
    assert "&lt;script&gt;" in inhalt and "&amp;" in inhalt
    leser = TabellenLeser()
    leser.feed(inhalt)
    assert leser.zeilen[0] == ["P01", '<script>alert("Prüfung")</script> & Zubehör', "0,00", "0"]
    assert "Fehler &lt;script&gt; &amp; &quot;Text&quot;" in inhalt
    assert original.read_bytes() == originalinhalt
    assert datenbankpfad.read_bytes() == datenbankinhalt
    bericht = {
        "projekt": "P09", "ticket": "P09-T03", "erwartung_erfuellt": True,
        "geprueft_am_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "php_version": subprocess.run([php, "-v"], capture_output=True, text=True, check=True).stdout.splitlines()[0],
        "original_sha256": hashlib.sha256(originalinhalt).hexdigest(), "anzahl_originaldatensaetze": 7,
        "importbefehl": befehl, "importergebnis": importergebnis,
        "serverbefehle": serverbefehle, "http_ergebnisse": http_ergebnisse,
        "sichtbare_produkte": 5, "sichtbare_importfehler": 2,
        "vertragsbeispiel_entspricht_datenbank": True, "sonderzeichen_und_nullwerte_geprueft": True,
        "ansicht_ohne_datenveraenderung": True,
        "pruefordner": pruefordner.relative_to(projektordner).as_posix(),
        "grenze": "HTTP-Inhalt und Tabellenstruktur lokal geprueft; keine visuelle Browserabnahme, keine laufende JSON-API, kein Shopware/Pimcore, keine T04-Abnahme."
    }
    (projektordner / "nachweise/P09-T03-pruefung.json").write_text(json.dumps(bericht, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(bericht, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    pruefen()
