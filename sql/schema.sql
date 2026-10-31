CREATE TABLE IF NOT EXISTS produkte (artikelnummer TEXT PRIMARY KEY, bezeichnung TEXT NOT NULL, preis NUMERIC NOT NULL CHECK(preis >= 0), bestand INTEGER NOT NULL CHECK(bestand >= 0));
