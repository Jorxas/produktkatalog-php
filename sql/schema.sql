CREATE TABLE IF NOT EXISTS produkte (
    artikelnummer TEXT PRIMARY KEY NOT NULL,
    bezeichnung TEXT NOT NULL,
    preis_cent INTEGER NOT NULL CHECK(typeof(preis_cent) = 'integer' AND preis_cent BETWEEN 0 AND 99999999999),
    bestand INTEGER NOT NULL CHECK(typeof(bestand) = 'integer' AND bestand BETWEEN 0 AND 2147483647)
);

CREATE TABLE IF NOT EXISTS importlaeufe (
    laufnummer INTEGER PRIMARY KEY,
    eingabe TEXT NOT NULL,
    begonnen_am_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS abgelehnte_zeilen (
    laufnummer INTEGER NOT NULL REFERENCES importlaeufe(laufnummer),
    csv_zeile INTEGER NOT NULL,
    originalzeile BLOB NOT NULL,
    fehler_json TEXT NOT NULL,
    PRIMARY KEY (laufnummer, csv_zeile)
);
