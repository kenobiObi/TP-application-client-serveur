# TP1 : Le modèle client-serveur

**Université Cheikh Anta Diop de Dakar, École Supérieure Polytechnique de Dakar, Département Génie Informatique**

- **Étudiants :** El hadji Amadou DIOP & Serigne Mourtalla NDONGO
- **Classe :** DUT2 TR
- **Module :** Application client/serveur
- **Professeur :** Dr Keba GUEYE
- **Année académique :** 2026 - 2027

Le rapport complet avec les captures d'écran est dans `rapport_TP1.docx`. Ce fichier contient les réponses aux questions du TP.

---

## Partie 1 : Préparer le serveur (VM1)

Base créée avec `scolarite.sql`, puis requêtes en session locale (`sudo mariadb`).

### Q1. Contenu de la base et schéma

| Table | Nombre de lignes | Détail |
|---|---|---|
| etudiant | 30 | 18 en II, 12 en RT |
| ec | 6 | ACSW, RES, SE1, BDD, MAT, ANG |
| note | 180 | 30 étudiants × 6 EC |

Schéma des quatre tables (la clé étrangère de etudiant est la colonne filiere) :

- **Clés primaires :** filiere.code, etudiant.matricule, ec.code, note.id
- **Clés étrangères :** etudiant.filiere → filiere.code ; note.matricule → etudiant.matricule ; note.ec → ec.code
- note relie les étudiants aux EC ; UNIQUE (matricule, ec) interdit deux notes pour le même étudiant et le même EC.

### Q2. Client et serveur : le même programme ?

**Non.** Ce sont deux programmes différents. `mariadb` est le programme client qui permet d'envoyer des requêtes SQL. `mariadbd` est le programme serveur qui reçoit les requêtes, gère la base de données et renvoie les résultats.

---

## Partie 2 : Ouvrir le service au réseau

### Q3. Le code d'erreur 10061

- **10061 = connexion refusée.** Windows a contacté 192.168.56.11:3306 et la machine a rejeté la connexion : aucun programme n'écoutait sur cette adresse et ce port.
- **VM1 était joignable :** un refus est une réponse (machine éteinte ou injoignable : pas de réponse, code 10060).
- **MariaDB fonctionnait,** mais il n'écoutait que sur 127.0.0.1, donc seulement pour VM1 elle-même.

### Q4. 127.0.0.1 ou 0.0.0.0

| Adresse d'écoute | Signification |
|---|---|
| 127.0.0.1 | Boucle locale : seules les connexions venant de la machine elle-même sont acceptées. |
| 0.0.0.0 | Toutes les interfaces : les connexions venant du réseau sont acceptées. |

**Pourquoi 127.0.0.1 par défaut :** par sécurité. La base n'est pas exposée au réseau tant que l'administrateur ne l'ouvre pas volontairement.

### Q5. USER() et CURRENT_USER()

- `USER()` = etudiant@192.168.56.1 : identité annoncée par le client (nom saisi + adresse réelle de Windows).
- `CURRENT_USER()` = etudiant@192.168.56.% : compte retenu par le serveur pour vérifier le mot de passe et attribuer les droits.

Un compte MariaDB est défini par un nom et un hôte autorisé. 192.168.56.% est un motif qui désigne tous les clients du réseau 192.168.56.0/24 (et non l'adresse du serveur) ; l'adresse 192.168.56.1 correspond à ce motif.

### Q6. Connexion en root depuis le réseau

- **Résultat :** `ERROR 1045 Access denied for user 'root'@'192.168.56.1'`. Il n'est pas possible de se connecter en root depuis le réseau.
- **Explication :** le compte root est limité à localhost et s'authentifie par le système (unix_socket, comme avec `sudo mariadb` sur VM1). Aucun root n'existe pour 192.168.56.1, quel que soit le mot de passe.
- **Pourquoi c'est bien :** root a tous les droits ; s'il était joignable par le réseau, deviner ou intercepter son mot de passe suffirait pour contrôler le serveur. Moindre privilège : les clients distants ont des comptes limités, l'administration se fait en local.

---

## Partie 3 : Plusieurs clients, un seul serveur

### Q7. PROCESSLIST et ss

`information_schema.PROCESSLIST` sur VM1 :

| Client | Compte | Adresse IP | Port source |
|---|---|---|---|
| Windows | etudiant | 192.168.56.1 | 51148 |
| VM2 | secretariat | 192.168.56.12 | 48512 |

- **Qui a choisi ces ports :** le système d'exploitation de chaque client, qui attribue un port éphémère à chaque nouvelle connexion.
- **Pourquoi pas 3306 :** 3306 est le port fixe du serveur ; chaque client en tire un différent. Il identifie la connexion (IP source, port source, IP destination, port destination) et permet d'acheminer chaque réponse au bon client.

### Q8. Droits d'accès

| Requête | Compte | Résultat |
|---|---|---|
| UPDATE note ... valeur = 20 | etudiant | Refusé : ERROR 1142 (42000), UPDATE command denied |
| UPDATE note ... valeur = 12 | secretariat | Accepté : Query OK, 1 row affected |
| DELETE FROM note ... | secretariat | Refusé : ERROR 1142 (42000), DELETE command denied |

- **Où sont les droits :** sur le serveur, dans les tables système de MariaDB (base mysql).
- **Qui les vérifie :** le serveur, à chaque requête, pas le client.
- **Conclusion :** le contrôle d'accès est centralisé et ne peut pas être contourné depuis un poste client (principe du moindre privilège) ; toute la sécurité repose sur la bonne configuration du serveur.

### Q9. Cohérence des données

**Oui, immédiatement :** Windows lit 12.00, la valeur écrite par secretariat depuis VM2 (la note d'origine était 9,25). Les données n'existent qu'en un seul exemplaire, sur le serveur ; les clients n'en gardent aucune copie, donc toute modification validée est visible par tous à la requête suivante. La centralisation garantit la cohérence.

---

## Partie 4 : Un deuxième service, le serveur web

### Q10. Requête et réponse HTTP

Dans la sortie de `curl -v`, le symbole `>` désigne les informations envoyées par le client et le symbole `<` celles reçues du serveur. La requête commence par `GET / HTTP/1.1` : GET est la méthode, `/` est la ressource demandée et HTTP/1.1 est la version du protocole. Les lignes suivantes sont les en-têtes de requête. La réponse commence par `HTTP/1.1 200 OK` : 200 indique que la demande a réussi. Les autres lignes sont les en-têtes de réponse, par exemple Server et Content-Type.

Une ligne vide sépare les en-têtes du corps de la réponse (le code HTML de la page).

### Q11. Ce que le serveur enregistre dans access.log

Pour chaque client, Apache enregistre :

- l'adresse IP du client (192.168.56.1 pour Windows, 192.168.56.12 pour VM2) ;
- la date et l'heure, la requête (`GET / HTTP/1.1`), le code de réponse (200) et la taille envoyée ;
- le User-Agent, qui distingue le navigateur (Mozilla/5.0 ...) de curl/8.5.0.

### Q12. Deux serveurs sur VM1

- **Remise du segment :** le système lit le port de destination du segment TCP et le remet au programme qui écoute sur ce port (3306 : MariaDB, 80 : Apache). L'IP désigne la machine, le port désigne le service.
- **Adresse ET port :** c'est le client qui prend l'initiative. Sans l'adresse, il ne sait pas quelle machine contacter ; sans le port, il ne sait pas quel service de cette machine viser.

### Q13. Connexion persistante ou requêtes indépendantes

| | Avantage | Inconvénient |
|---|---|---|
| **MariaDB** (connexion persistante) | Authentification faite une seule fois ; le serveur garde l'état de la session (base courante, transactions) ; échanges rapides. | Chaque connexion ouverte consomme des ressources même inactive (Sleep) : nombre de clients simultanés limité. |
| **HTTP** (requête-réponse) | Le serveur ne garde aucun état : il économise ses ressources et peut servir un très grand nombre de clients. | Le serveur ne reconnaît pas le client d'une requête à l'autre : le contexte doit être renvoyé à chaque fois. |

**Comment un site « se souvient » d'un utilisateur :** après la connexion, le serveur crée une session et envoie au navigateur un identifiant de session dans un cookie ; le navigateur le renvoie à chaque requête et le serveur retrouve ainsi l'utilisateur.

---

## Partie 5 : Les limites du modèle

### 5.1 Le serveur s'arrête

### Q14. Arrêt du serveur

| Client | Message obtenu |
|---|---|
| Windows | ERROR 2002 (HY000): Can't connect to server on '192.168.56.11' (10061) |
| VM2 | ERROR 2002 (HY000): Can't connect to server on '192.168.56.11' (115) |

- **Clients affectés :** tous (Windows et VM2) : plus aucune requête vers la base n'est possible.
- **Nom du défaut :** point unique de défaillance (SPOF) : tout est centralisé sur un seul serveur, sa panne bloque tous les clients.

### 5.2 Ce qui circule sur le réseau

### Q15. Contenu de la capture

- **Requête :** le texte SQL « SELECT nom, valeur FROM note JOIN etudiant USING(matricule) WHERE matricule = 'ESP260011' » est lisible en clair.
- **Réponse :** la base (scolarite), les tables (etudiant, note), les colonnes (nom, valeur) et les données (SECK, 9.50, 16.50, 15.50, 7.50, 11.75, 14.75) sont lisibles en clair.
- **Mot de passe :** non, il n'est pas envoyé en clair : MariaDB utilise un défi-réponse (une valeur aléatoire du serveur et un condensat calculé par le client).
- **Solution :** chiffrer les échanges avec TLS/SSL (certificat et clé sur MariaDB, comptes en REQUIRE SSL), ou passer par un VPN ou un tunnel SSH ; HTTPS pour le serveur web.

### Synthèse

| Caractéristique | MariaDB | Apache (HTTP) |
|---|---|---|
| Machine et port du serveur | VM1 (192.168.56.11), port 3306 | VM1 (192.168.56.11), port 80 |
| Logiciel client utilisé | Client mariadb (Windows et VM2) | Navigateur (Windows) et curl (VM2) |
| Qui prend l'initiative ? | Le client | Le client |
| Durée de vie d'une connexion | Longue : ouverte pendant toute la session (Sleep dans PROCESSLIST) | Courte : une requête, une réponse |
| Où sont vérifiés les droits ? | Sur le serveur (comptes et privilèges de la base mysql) | Sur le serveur (configuration d'Apache, droits sur les fichiers) ; ici page publique |
| Effet d'un arrêt du serveur | Connexion impossible pour tous les clients (10061 / 115) | Site inaccessible ; l'arrêt de MariaDB n'affecte pas Apache |

### Q16. Le modèle client-serveur

Le modèle client-serveur repose sur un serveur, programme qui attend des demandes sur un port connu d'une machine connue, et des clients qui prennent l'initiative de s'y connecter, envoient une requête et attendent la réponse. Dans ce TP, MariaDB (port 3306) et Apache (port 80) tournent sur VM1 ; Windows et VM2 ouvrent les connexions, chacun avec un port source éphémère choisi par son système. Le serveur centralise les données (un seul exemplaire de la base, visible à jour par tous les clients) et les règles d'accès (les droits sont vérifiés par le serveur, pas par le client). Les clients ne communiquent jamais entre eux : tout passe par le serveur. Un même serveur peut héberger plusieurs services, distingués par leur port, et servir plusieurs clients en même temps. Pour être joignable, le service doit écouter sur une adresse réseau (bind-address) et son port doit être ouvert dans le pare-feu.

**Deux avantages**

- Données et sécurité centralisées : un seul exemplaire cohérent pour tous, et des droits d'accès contrôlés en un seul endroit.
- Service partagé et administration simple : plusieurs clients différents l'utilisent en même temps, et la gestion, la sauvegarde et les mises à jour se font sur une seule machine.

**Deux inconvénients**

- Point unique de défaillance : si le serveur s'arrête, tous les clients perdent le service.
- Trafic en clair et goulot d'étranglement : sans TLS, requêtes et données sont lisibles sur le réseau ; le serveur peut être saturé quand le nombre de clients augmente.
