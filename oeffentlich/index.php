<?php
declare(strict_types=1);

function htmlText(string $text): string
{
    return htmlspecialchars($text, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function preisAnzeigen(int $cent): string
{
    return intdiv($cent, 100) . ',' . str_pad((string) ($cent % 100), 2, '0', STR_PAD_LEFT);
}

header('Content-Type: text/html; charset=UTF-8');
header('Cache-Control: no-store');
$produkte = [];
$ablehnungen = [];
$laufnummer = null;
$hinweis = null;
try {
    // Nur lokale Konfiguration; kein Datenbankpfad aus einer HTTP-Anfrage.
    $datenbankpfad = getenv('KATALOG_DATENBANK') ?: __DIR__ . '/../ausgabe/katalog.sqlite';
    if (!is_file($datenbankpfad)) {
        throw new RuntimeException('Der Katalog fehlt.');
    }
    $datenbank = new PDO('sqlite:' . $datenbankpfad, null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $datenbank->exec('PRAGMA query_only = ON');
    $datenbank->beginTransaction();
    $produkte = $datenbank->query('SELECT artikelnummer, bezeichnung, preis_cent, bestand FROM produkte ORDER BY artikelnummer')->fetchAll(PDO::FETCH_ASSOC);
    $laufnummer = $datenbank->query('SELECT MAX(laufnummer) FROM importlaeufe')->fetchColumn();
    if ($laufnummer !== null) {
        $abfrage = $datenbank->prepare('SELECT csv_zeile, fehler_json FROM abgelehnte_zeilen WHERE laufnummer = ? ORDER BY csv_zeile');
        $abfrage->execute([$laufnummer]);
        foreach ($abfrage as $zeile) {
            $ablehnungen[] = ['csv_zeile' => $zeile['csv_zeile'], 'gruende' => json_decode($zeile['fehler_json'], true, 512, JSON_THROW_ON_ERROR)];
        }
    }
    $datenbank->commit();
} catch (Throwable $fehler) {
    http_response_code(503);
    $produkte = [];
    $ablehnungen = [];
    $hinweis = 'Der Katalog ist nicht verfügbar. Bitte CSV-Import und SQLite-Datenbank prüfen.';
}
?>
<!doctype html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Produktkatalog</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 64rem; margin: 2rem auto; padding: 0 1rem; color: #172c35; }
        table { border-collapse: collapse; width: 100%; }
        th, td { text-align: left; border-bottom: 1px solid #a5b7bd; padding: .7rem .4rem; overflow-wrap: anywhere; }
        caption { text-align: left; padding: 1rem 0; font-weight: bold; }
        .tabelle { overflow-x: auto; }
        .hinweis { padding: 1rem; border-left: .3rem solid #9b4400; background: #fff3e6; }
    </style>
</head>
<body>
<h1>Produktkatalog</h1>
<p>Lokale Eigenentwicklung mit synthetischen Daten. Kein Shopware- oder Pimcore-Shop.</p>
<p>Preise in lokalen Preiseinheiten; Währung und Steuerbezug sind noch nicht festgelegt.</p>
<?php if ($hinweis !== null): ?>
<p class="hinweis" role="alert"><?= htmlText($hinweis) ?></p>
<?php else: ?>
<div class="tabelle">
<table>
    <caption>Gespeicherte Produkte (<?= count($produkte) ?>)</caption>
    <thead><tr><th scope="col">Artikelnummer</th><th scope="col">Bezeichnung</th><th scope="col">Preis</th><th scope="col">Bestand</th></tr></thead>
    <tbody>
    <?php foreach ($produkte as $produkt): ?>
    <tr><td><?= htmlText($produkt['artikelnummer']) ?></td><td><?= htmlText($produkt['bezeichnung']) ?></td><td><?= preisAnzeigen((int) $produkt['preis_cent']) ?></td><td><?= (int) $produkt['bestand'] ?></td></tr>
    <?php endforeach; ?>
    </tbody>
</table>
</div>
<?php if ($produkte === []): ?><p>Keine Produkte gespeichert.</p><?php endif; ?>
<h2>Importfehler des letzten Laufs</h2>
<?php if ($laufnummer === null): ?>
<p>Noch kein Importlauf vorhanden.</p>
<?php elseif ($ablehnungen === []): ?>
<p>Importlauf <?= (int) $laufnummer ?>: keine abgelehnten Zeilen.</p>
<?php else: ?>
<p>Importlauf <?= (int) $laufnummer ?>: <?= count($ablehnungen) ?> abgelehnte Zeilen. Frühere Ablehnungen bleiben in der Datenbank gespeichert.</p>
<ul>
<?php foreach ($ablehnungen as $ablehnung): ?>
    <li>CSV-Zeile <?= (int) $ablehnung['csv_zeile'] ?>: <?= htmlText(implode(' ', $ablehnung['gruende'])) ?></li>
<?php endforeach; ?>
</ul>
<?php endif; ?>
<?php endif; ?>
</body>
</html>
