<?php
declare(strict_types=1);

function zeilePruefen(array $felder): array
{
    if (count($felder) !== 4) {
        return ['Die Zeile muss genau vier Felder enthalten.'];
    }
    [$artikelnummer, $bezeichnung, $preis, $bestand] = $felder;
    $fehler = [];
    if (preg_match('/\AP[0-9]{2}\z/', $artikelnummer ?? '') !== 1) {
        $fehler[] = 'Artikelnummer muss aus P und zwei Ziffern bestehen.';
    }
    if (preg_match('/\A\S(?:.*\S)?\z/us', $bezeichnung ?? '') !== 1) {
        $fehler[] = 'Bezeichnung fehlt, ist kein UTF-8 oder hat aeussere Leerzeichen.';
    }
    if (preg_match('/\A[0-9]+\.[0-9]{2}\z/', $preis ?? '') !== 1) {
        $fehler[] = 'Preis fehlt oder ist kein nicht negativer Betrag mit zwei Nachkommastellen.';
    } elseif (strlen(ltrim(str_replace('.', '', $preis), '0')) > 11) {
        $fehler[] = 'Preis darf hoechstens 999999999.99 betragen.';
    }
    $bestandOhneNullen = ltrim($bestand ?? '', '0');
    if (preg_match('/\A[0-9]+\z/', $bestand ?? '') !== 1
        || strlen($bestandOhneNullen) > 10
        || (strlen($bestandOhneNullen) === 10 && strcmp($bestandOhneNullen, '2147483647') > 0)) {
        $fehler[] = 'Bestand muss eine ganze Zahl zwischen 0 und 2147483647 sein.';
    }
    return $fehler;
}

function produkteImportieren(string $eingabepfad, string $datenbankpfad): array
{
    if (!in_array('sqlite', PDO::getAvailableDrivers(), true) || PHP_INT_SIZE < 8) {
        throw new RuntimeException('PHP mit PDO SQLite und 64-Bit-Ganzzahlen ist erforderlich.');
    }
    $eingabe = fopen($eingabepfad, 'rb');
    if ($eingabe === false) {
        throw new RuntimeException('Die Eingabedatei konnte nicht geoeffnet werden.');
    }
    $datenbank = null;
    try {
        $kopf = fgetcsv($eingabe, 0, ',', '"', '');
        if ($kopf !== ['artikelnummer', 'bezeichnung', 'preis', 'bestand']) {
            throw new RuntimeException('Die CSV-Kopfzeile entspricht nicht dem Datenvertrag.');
        }
        $schema = file_get_contents(__DIR__ . '/../sql/schema.sql');
        if ($schema === false) {
            throw new RuntimeException('Das Datenbankschema konnte nicht gelesen werden.');
        }
        $datenbank = new PDO('sqlite:' . $datenbankpfad, null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
        $datenbank->exec('PRAGMA foreign_keys = ON');
        $datenbank->beginTransaction();
        $datenbank->exec($schema);
        $laufSpeichern = $datenbank->prepare('INSERT INTO importlaeufe (eingabe, begonnen_am_utc) VALUES (?, ?)');
        $laufSpeichern->execute([$eingabepfad, gmdate('Y-m-d\TH:i:s\Z')]);
        $laufnummer = (int) $datenbank->lastInsertId();
        $suchen = $datenbank->prepare('SELECT 1 FROM produkte WHERE artikelnummer = ?');
        $speichern = $datenbank->prepare('INSERT INTO produkte (artikelnummer, bezeichnung, preis_cent, bestand)
            VALUES (?, ?, ?, ?) ON CONFLICT(artikelnummer) DO UPDATE SET
            bezeichnung = excluded.bezeichnung, preis_cent = excluded.preis_cent, bestand = excluded.bestand');
        $ablehnen = $datenbank->prepare('INSERT INTO abgelehnte_zeilen
            (laufnummer, csv_zeile, originalzeile, fehler_json) VALUES (?, ?, ?, ?)');
        $ergebnis = ['laufnummer' => $laufnummer, 'gelesen' => 0, 'angelegt' => 0, 'aktualisiert' => 0, 'abgelehnt' => 0];
        $ersteZeilen = [];
        $csvZeile = 1;
        while (true) {
            $anfang = ftell($eingabe);
            $felder = fgetcsv($eingabe, 0, ',', '"', '');
            if ($felder === false) {
                if (!feof($eingabe)) {
                    throw new RuntimeException('Die CSV-Datei konnte nicht vollstaendig gelesen werden.');
                }
                break;
            }
            $csvZeile++;
            $ergebnis['gelesen']++;
            $fehler = zeilePruefen($felder);
            $artikelnummer = $felder[0] ?? '';
            if (isset($ersteZeilen[$artikelnummer])) {
                $fehler[] = 'Artikelnummer in dieser Datei doppelt; erstmals CSV-Zeile ' . $ersteZeilen[$artikelnummer] . '.';
            } else {
                $ersteZeilen[$artikelnummer] = $csvZeile;
            }
            if ($fehler !== []) {
                $ende = ftell($eingabe);
                fseek($eingabe, $anfang);
                $originalzeile = fread($eingabe, $ende - $anfang);
                $ablehnen->execute([$laufnummer, $csvZeile, $originalzeile, json_encode($fehler, JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE)]);
                $ergebnis['abgelehnt']++;
                continue;
            }
            $suchen->execute([$artikelnummer]);
            $vorhanden = $suchen->fetchColumn() !== false;
            // Ganze Cent vermeiden Rundungsfehler durch Gleitkommazahlen.
            $preisCent = (int) str_replace('.', '', $felder[2]);
            $speichern->execute([$artikelnummer, $felder[1], $preisCent, (int) $felder[3]]);
            $ergebnis[$vorhanden ? 'aktualisiert' : 'angelegt']++;
        }
        $datenbank->commit();
        return $ergebnis;
    } catch (Throwable $fehler) {
        if ($datenbank !== null && $datenbank->inTransaction()) {
            $datenbank->rollBack();
        }
        throw $fehler;
    } finally {
        fclose($eingabe);
    }
}

try {
    if ($argc > 3) {
        throw new RuntimeException('Aufruf: php src/importieren.php [CSV-Datei] [SQLite-Datei]');
    }
    $ergebnis = produkteImportieren($argv[1] ?? __DIR__ . '/../beispieldaten/produkte.csv', $argv[2] ?? __DIR__ . '/../ausgabe/katalog.sqlite');
    echo json_encode($ergebnis, JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT), PHP_EOL;
    // Fachlich abgelehnte Zeilen werden berichtet; technische Fehler liefern Exitcode 1.
    exit(0);
} catch (Throwable $fehler) {
    fwrite(STDERR, 'Import fehlgeschlagen: ' . $fehler->getMessage() . PHP_EOL);
    exit(1);
}
