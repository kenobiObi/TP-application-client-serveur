"""
client_lourd.py — Application de scolarité en architecture 2-TIERS (TP2).

Tier 1 (ce programme, sur le poste client) : présentation + LOGIQUE MÉTIER.
Tier 2 (VM1) : serveur MariaDB, qui ne fait que stocker et renvoyer des données.

Le client se connecte DIRECTEMENT à la base de données (port 3306) : il doit
donc connaître l'adresse du serveur, un compte et son mot de passe.

Installation : Windows  ->  py -m pip install pymysql
               Linux    ->  sudo apt install python3-pymysql
Usage        : python client_lourd.py
"""
import sys
import time

import pymysql

# --------------------------------------------------------------------------
# Paramètres de connexion : ils sont DANS le programme distribué aux clients.
# --------------------------------------------------------------------------
SERVEUR_BDD = "192.168.56.11"
PORT_BDD = 3306
UTILISATEUR = "etudiant"
MOT_DE_PASSE = "Etudiant@2026"
BASE = "scolarite"

VERSION = "1.1"
SEUIL_VALIDATION = 10.0          # règle métier n°1 : une moyenne >= 10 valide
NOTE_ELIMINATOIRE = 8.0          # règle métier n°3 : une note < 8 dans un EC empêche la validation
# règle métier n°2 : moyenne PONDÉRÉE par les crédits des EC (voir moyenne())


def connexion():
    return pymysql.connect(host=SERVEUR_BDD, port=PORT_BDD, user=UTILISATEUR,
                           password=MOT_DE_PASSE, database=BASE, charset="utf8mb4",
                           connect_timeout=5)


def moyenne(notes):
    """notes = [(valeur, credits), ...] -> moyenne pondérée (logique métier)."""
    total_credits = sum(c for _, c in notes)
    return sum(float(v) * c for v, c in notes) / total_credits if total_credits else 0.0


def est_valide(notes):
    """True si moyenne >= SEUIL_VALIDATION et aucune note < NOTE_ELIMINATOIRE."""
    return moyenne(notes) >= SEUIL_VALIDATION and not any(float(v) < NOTE_ELIMINATOIRE for v, _ in notes)


def octets_recus(cur):
    """Octets envoyés par le serveur sur CETTE connexion depuis son ouverture."""
    cur.execute("SHOW SESSION STATUS LIKE 'Bytes_sent'")
    return int(cur.fetchone()[1])


def lister_etudiants(cur):
    cur.execute("SELECT matricule, prenom, nom, filiere FROM etudiant ORDER BY nom, prenom")
    for mat, pre, nom, fil in cur.fetchall():
        print(f"  {mat}  {nom:<8} {pre:<10} {fil}")


def releve(cur, matricule):
    cur.execute("SELECT prenom, nom FROM etudiant WHERE matricule = %s", (matricule,))
    ligne = cur.fetchone()
    if not ligne:
        print("  matricule inconnu")
        return
    print(f"  Relevé de {ligne[0]} {ligne[1]} ({matricule})")
    cur.execute("""SELECT e.code, e.intitule, e.credits, n.valeur
                   FROM note n JOIN ec e ON e.code = n.ec
                   WHERE n.matricule = %s ORDER BY e.code""", (matricule,))
    notes = []
    for code, intitule, credits, valeur in cur.fetchall():
        print(f"    {code:<5} {intitule:<36} {credits} cr.  {valeur:>5}")
        notes.append((valeur, credits))
    m = moyenne(notes)
    decision = "VALIDÉ" if est_valide(notes) else "NON VALIDÉ"
    print(f"  Moyenne pondérée : {m:.2f} / 20  ->  {decision}")


def classement(cur):
    """Calculé ENTIÈREMENT sur le client : il rapatrie TOUTES les notes."""
    octets_avant = octets_recus(cur)
    debut = time.perf_counter()
    cur.execute("""SELECT n.matricule, n.valeur, e.credits
                   FROM note n JOIN ec e ON e.code = n.ec""")
    lignes = cur.fetchall()
    duree = time.perf_counter() - debut
    volume = octets_recus(cur) - octets_avant
    par_etudiant = {}
    for mat, valeur, credits in lignes:
        par_etudiant.setdefault(mat, []).append((valeur, credits))
    rang = sorted(((moyenne(n), mat) for mat, n in par_etudiant.items()), reverse=True)
    print(f"  {len(lignes)} lignes rapatriées du serveur en {duree * 1000:.0f} ms ({volume / 1024:.1f} Kio)")
    for i, (m, mat) in enumerate(rang[:10], 1):
        print(f"  {i:>2}. {mat}  {m:.2f}")
    admis = sum(1 for n in par_etudiant.values() if est_valide(n))
    print(f"  Admis : {admis} / {len(rang)}")


def main():
    print(f"Scolarité — client lourd v{VERSION} — serveur {SERVEUR_BDD}:{PORT_BDD}")
    try:
        cnx = connexion()
    except pymysql.MySQLError as e:
        sys.exit(f"Connexion impossible au serveur de base de données : {e}")
    with cnx, cnx.cursor() as cur:
        while True:
            print("\n1. Liste des étudiants   2. Relevé de notes   3. Classement   0. Quitter")
            choix = input("> ").strip()
            if choix == "1":
                lister_etudiants(cur)
            elif choix == "2":
                releve(cur, input("  Matricule : ").strip())
            elif choix == "3":
                classement(cur)
            elif choix == "0":
                break


if __name__ == "__main__":
    main()
