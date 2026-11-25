<?php
// inc/metier.php — LOGIQUE MÉTIER de l'application (tier 2, serveur d'application).
// Une seule copie pour tous les clients : modifier une règle ici la change pour tout le monde.
require_once __DIR__ . '/config.php';

const VERSION_APPLI = '1.1';
const SEUIL_VALIDATION = 10.0;   // règle métier n°1
const NOTE_ELIMINATOIRE = 8.0;   // règle métier n°3 : une note < 8 dans un EC empêche la validation

function bdd(): PDO {
    static $pdo = null;
    if ($pdo === null) {
        $dsn = 'mysql:host=' . BDD_HOTE . ';dbname=' . BDD_BASE . ';charset=utf8mb4';
        $pdo = new PDO($dsn, BDD_UTILISATEUR, BDD_MOT_DE_PASSE, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_TIMEOUT => 5,
        ]);
    }
    return $pdo;
}

// Règle métier n°2 : moyenne pondérée par les crédits, calculée PAR LE SGBD.
const SQL_MOYENNE = 'SUM(n.valeur * e.credits) / SUM(e.credits)';

function etudiants(?string $filiere): array {
    $sql = 'SELECT matricule, prenom, nom, filiere FROM etudiant';
    $params = [];
    if ($filiere) { $sql .= ' WHERE filiere = ?'; $params[] = $filiere; }
    $req = bdd()->prepare($sql . ' ORDER BY nom, prenom LIMIT 200');
    $req->execute($params);
    return $req->fetchAll();
}

function releve(string $matricule): ?array {
    $req = bdd()->prepare('SELECT matricule, prenom, nom, filiere FROM etudiant WHERE matricule = ?');
    $req->execute([$matricule]);
    $etu = $req->fetch();
    if (!$etu) return null;
    $req = bdd()->prepare('SELECT e.code, e.intitule, e.credits, n.valeur
                           FROM note n JOIN ec e ON e.code = n.ec
                           WHERE n.matricule = ? ORDER BY e.code');
    $req->execute([$matricule]);
    $etu['notes'] = $req->fetchAll();
    $req = bdd()->prepare('SELECT ' . SQL_MOYENNE . ' AS moyenne
                           FROM note n JOIN ec e ON e.code = n.ec WHERE n.matricule = ?');
    $req->execute([$matricule]);
    $etu['moyenne'] = (float) $req->fetchColumn();

    $aNoteEliminatoire = false;
    foreach ($etu['notes'] as $note) {
        if ((float) $note['valeur'] < NOTE_ELIMINATOIRE) {
            $aNoteEliminatoire = true;
            break;
        }
    }
    $etu['decision'] = (!$aNoteEliminatoire && $etu['moyenne'] >= SEUIL_VALIDATION) ? 'VALIDÉ' : 'NON VALIDÉ';
    return $etu;
}

function classement(int $n = 10): array {
    // Seules les n premières lignes quittent le serveur de base de données.
    $req = bdd()->prepare('SELECT n.matricule, ' . SQL_MOYENNE . ' AS moyenne
                           FROM note n JOIN ec e ON e.code = n.ec
                           GROUP BY n.matricule ORDER BY moyenne DESC LIMIT ' . (int) $n);
    $req->execute();
    $top = $req->fetchAll();
    $req = bdd()->prepare('SELECT COUNT(*) AS total, SUM(m >= ? AND min_note >= ?) AS admis FROM
                           (SELECT ' . SQL_MOYENNE . ' AS m, MIN(n.valeur) AS min_note
                            FROM note n JOIN ec e ON e.code = n.ec
                            GROUP BY n.matricule) t');
    $req->execute([SEUIL_VALIDATION, NOTE_ELIMINATOIRE]);
    return ['top' => $top, 'bilan' => $req->fetch()];
}

function h(?string $s): string { return htmlspecialchars((string) $s, ENT_QUOTES, 'UTF-8'); }
