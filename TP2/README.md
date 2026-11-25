# TP2 : Architectures 2-tiers et 3-tiers comparées

* **Établissement :** Université Cheikh Anta Diop de Dakar (UCAD) — École Supérieure Polytechnique (ESP), Département Génie Informatique
* **Matière :** Applications Client-Serveur et Web (ACSW) — Licence 2 Réseaux et Télécommunications
* **Enseignant :** Dr Keba GUEYE
* **Étudiants :** Serigne Mouralla Ndongo & El Hadji Amadou Diop

---

## 📋 Présentation et Objectifs

Ce dépôt présente les travaux pratiques sur la comparaison entre une **architecture 2-tiers (client lourd)** et une **architecture 3-tiers (application web)**. 

Une application logicielle se décompose en trois couches logiques :
1. **La présentation :** ce que l'utilisateur voit et saisit.
2. **La logique métier :** les règles de gestion (calcul de moyenne pondérée, décision d'admission).
3. **Les données :** le stockage et l'accès aux informations via le SGBD (MariaDB).

L'objectif est de déployer la même application de gestion de scolarité selon ces deux modèles et de les évaluer sur quatre critères : **le déploiement d'une évolution, la cohérence des règles, le volume réseau et la sécurité**.

### Architecture Matérielle et Réseau

| Machine | Nom d'hôte | Adresse IP (`192.168.56.0/24`) | Rôle dans le TP |
| :--- | :--- | :--- | :--- |
| **Poste Hôte (Linux)** | `funnyvalentine` | `192.168.56.1` | **Tier 1 :** Exécute `client_lourd.py` (2-tiers), puis le navigateur web (3-tiers) |
| **VM1 (Linux)** | `charlexavier` | `192.168.56.11` | **Serveur de données :** Héberge le SGBD MariaDB (`scolarite`) |
| **VM2 (Linux)** | `hankmccoy` | `192.168.56.12` | **Serveur d'application :** Apache + PHP (3-tiers), et second poste client (2-tiers) |

---

## 🖥️ Partie 1 : L'application en 2-tiers (Client lourd)

### Mise en œuvre
* Installation du connecteur MySQL pour Python (`sudo apt install python3-pymysql`) sur le poste hôte et sur VM2.
* Exécution du script `client_lourd.py` sur les deux machines pour interroger directement MariaDB (`192.168.56.11:3306`).

### Réponses aux questions

#### **Q1. Où sont la présentation, la logique métier et l'accès aux données ? Sur quelle machine s'exécutent-elles toutes ?**
* **Présentation :** Tous les appels aux fonctions `print()` et `input()` (affichage du menu, de la liste des étudiants, du relevé de notes et du classement).
* **Logique métier :** La constante `SEUIL_VALIDATION` ($10$), la fonction `moyenne()` qui calcule la moyenne pondérée par les crédits, la décision `VALIDÉ` / `NON VALIDÉ`, le tri des résultats et le décompte des admis.
* **Accès aux données :** La fonction `connexion()` et l'exécution des requêtes SQL via `cur.execute()`.
* **Localisation :** **Toutes ces couches s'exécutent sur la même machine : le poste client.** Le serveur MariaDB ne fait que stocker et renvoyer les données brutes.

#### **Q2. Que découvre un étudiant qui récupère `client_lourd.py` ? Que peut-il faire avec, en dehors du programme ?**
En lisant le code source en clair du fichier `client_lourd.py`, l'étudiant découvre :
* L'adresse IP du serveur de base de données (`192.168.56.11`) et son port (`3306`).
* Le nom d'utilisateur, le mot de passe en clair et le nom de la base (`scolarite`).

**Conséquences :** Il peut contourner l'application et se connecter directement au serveur MariaDB depuis n'importe quel client SQL (terminal `mariadb`, DBeaver, script personnel) pour exécuter ses propres requêtes : consulter les notes de tous les étudiants, voire modifier ou supprimer des données si le compte dispose de droits d'écriture.

#### **Q3. Qu'aurait-il fallu installer sur les 300 postes d'une salle informatique pour déployer cette application ?**
Sur chacun des 300 postes, il aurait fallu :
1. Installer l'interpréteur **Python 3** et la bibliothèque **`pymysql`**.
2. Copier le fichier **`client_lourd.py`**.
3. Configurer le réseau/pare-feu pour autoriser les 300 adresses IP à joindre le port `3306` de VM1.
4. Répéter l'opération manuellement sur les 300 machines à chaque mise à jour du programme.

---

## 🌐 Partie 2 : La même application en 3-tiers (Web)

### Mise en œuvre
* Installation de la pile LAMP sur VM2 (`apache2`, `php`, `libapache2-mod-php`, `php-mysql`) et déploiement dans `/var/www/html/scolarite`.
* Création sur VM1 d'un compte dédié `app_scolarite` restreint uniquement à l'IP de VM2 (`192.168.56.12`).

### Réponses aux questions

#### **Q4. Les deux architectures donnent-elles la même moyenne pour `ESP260001` et le même nombre d'admis ? Pourquoi est-ce indispensable ?**
* **Oui :** La moyenne pondérée de `ESP260001` (Rokhaya SY) est de **$11,23 / 20$** (`VALIDÉ`) et le nombre total d'admis est de **$18 / 30$** dans les deux architectures.
* **Importance :** C'est indispensable sur le plan méthodologique. Pour comparer objectivement les performances, le trafic réseau et le comportement des deux architectures, les données de départ et les algorithmes de calcul doivent être strictement identiques. Sinon, tout écart mesuré pourrait être imputé à une différence de code plutôt qu'à l'architecture.

#### **Q5. Qu'a dû installer le poste client pour utiliser la version 3-tiers ? Comparaison avec Q3.**
* **Rien du tout.** Un simple navigateur web (déjà présent sur tout système d'exploitation) suffit.
* **Comparaison avec Q3 :** Contrairement au 2-tiers qui exige un déploiement lourd et un maintien sur 300 postes, le déploiement en 3-tiers a un coût d'installation nul côté client.

#### **Q6. Que renvoie la requête vers `config.php` ? Expliquez pourquoi le mot de passe n'est jamais envoyé au navigateur.**
* La commande `curl.exe -i http://192.168.56.12/scolarite/inc/config.php` renvoie un code **`HTTP/1.1 200 OK`** avec un corps vide (**`Content-Length: 0`**).
* **Explication :** Le serveur web Apache ne sert pas les fichiers `.php` comme du texte brut. Il les transmet à l'interpréteur PHP côté serveur (VM2). Comme `config.php` ne contient que des déclarations de constantes et aucune instruction d'affichage (`echo`/`print`), PHP exécute le fichier et génère une sortie HTML vide. Les identifiants restent confinés sur VM2 et ne transitent jamais sur le réseau vers le client.

#### **Q7. Combien de comptes MariaDB faut-il en 3-tiers, quel que soit le nombre d'utilisateurs ? Et en 2-tiers ?**
* **En 3-tiers :** **1 seul compte** (`app_scolarite`@`192.168.56.12`) suffit, qu'il y ait $10$ ou $10\,000$ utilisateurs. C'est le serveur d'application qui centralise les connexions au SGBD.
* **En 2-tiers :** Il faut théoriquement **autant de comptes MariaDB que d'utilisateurs** (des centaines) pour assurer la traçabilité et gérer finement les droits d'accès de chacun.

#### **Q8. Que voit-on dans le code source de la page dans le navigateur (`Ctrl+U`) ?**
On ne trouve **aucune trace de code PHP, de requêtes SQL, ni de formule de calcul**. Le navigateur reçoit uniquement le document **HTML statique généré** (accompagné de sa feuille de style CSS), c'est-à-dire le résultat final prêt à être affiché.

---

## 🔄 Partie 3 : Faire évoluer une règle métier (Version 1.1)

**Nouvelle règle :** Une note strictement inférieure à $8/20$ (`NOTE_ELIMINATOIRE = 8.0`) dans un Élément Constitutif (EC) entraîne l'ajournement (`NON VALIDÉ`), quelle que soit la moyenne générale.

### Réponses aux questions

#### **Q9. Quelle décision pour `ESP260011` et combien d'admis sur chaque poste en 2-tiers ? Quelles conséquences ?**
L'étudiant `ESP260011` (Yacine SECK) possède une moyenne générale de **$12,55 / 20$**, mais a obtenu **$7,50 / 20$** en Mathématiques discrètes (`MAT`).

| Indicateur | Poste Hôte (v1.0 non à jour) | VM2 (v1.1 mise à jour) |
| :--- | :---: | :---: |
| **Moyenne de `ESP260011`** | $12,55 / 20$ | $12,55 / 20$ |
| **Décision pour `ESP260011`** | **VALIDÉ** | **NON VALIDÉ** |
| **Nombre total d'admis** | **$18 / 30$** | **$16 / 30$** |

* **Conséquences réelles :** C'est critique pour un service de scolarité. Deux agents utilisant deux postes différents obtiennent des résultats contradictoires pour le même étudiant. Cela entraîne une perte d'intégrité des données, des injustices, des contestations administratives et invalide la valeur officielle des relevés de notes.

#### **Q10. Combien de fichiers et de machines avez-vous modifiés en 3-tiers ? Qui a profité de la règle, et quand ?**
* **Modifications :** **1 seul fichier** (`inc/metier.php`) sur **1 seule machine** (le serveur d'application VM2).
* **Diffusion :** **100 % des utilisateurs** ont bénéficié de la nouvelle règle **instantanément**, dès le rechargement de la page web dans leur navigateur, sans aucune intervention sur leurs postes.

#### **Q11. Où avez-vous dû intervenir pour la règle éliminatoire dans chaque cas ?**
* **En 2-tiers :** Il faut modifier le code Python dans chaque copie de `client_lourd.py` sur tous les postes clients, à deux endroits : dans la fonction `releve()` (pour l'affichage individuel) et dans la fonction `classement()` (pour le comptage global des admis).
* **En 3-tiers :** On intervient uniquement dans `inc/metier.php` sur VM2 :
  * En **PHP** (boucle sur les notes) pour la décision individuelle du relevé.
  * Directement dans la **requête SQL** (ajout de `MIN(n.valeur) >= ?`) pour le classement, car le calcul d'agrégation est délégué au SGBD.

---

## 📊 Partie 4 : Volume de données et réseau

Test de montée en charge par injection de **$20\,000$ étudiants fictifs** et **$120\,000$ notes** supplémentaires (`volume.sql`).

### Réponses aux questions

#### **Q12. Tableau comparatif, origine de l'écart et impact sur un réseau contraint**

| Mesure | Architecture 2-tiers | Architecture 3-tiers |
| :--- | :--- | :--- |
| **Lignes ou octets reçus par le client** | **$120\,180$ lignes** ($\approx 2\,407,3\text{ Kio}$) | **$10$ lignes** (page HTML de quelques $\text{Kio}$) |
| **Temps de calcul du classement** | $685\text{ ms}$ (hôte) à $939\text{ ms}$ (VM2) | $\approx 10\text{ ms}$ à $19\text{ ms}$ (côté SGBD) |
| **Machine qui effectue le calcul** | **Le poste client** (en Python) | **VM1 (le serveur MariaDB)** (en SQL) |

* **Origine de l'écart :** En 2-tiers, le client rapatrié l'intégralité de la table des notes sur le réseau pour effectuer les moyennes et le tri en mémoire vive. En 3-tiers, le SGBD effectue l'agrégation et le tri (`GROUP BY`, `ORDER BY`, `LIMIT 10`) localement et ne transmet au serveur web que le Top 10, qui renvoie ensuite une légère page HTML au navigateur.
* **Simulation avec 300 postes sur une liaison à $10\text{ Mbit/s}$ ou connexion mobile :**
  * $300 \times 2,4\text{ Mio} \approx 720\text{ Mio}$ ($\approx 5,76\text{ Gbits}$) à transférer simultanément. Sur un lien partagé à $10\text{ Mbit/s}$, le réseau serait saturé pendant près de **10 minutes** ($576\text{ secondes}$), rendant l'application inutilisable. Sur une connexion mobile, cela consommerait inutilement le forfait data de l'étudiant et subirait une forte latence.

#### **Q13. Que mesure `Bytes_sent` ? Pourquoi est-ce une mesure honnête ?**
* **Définition :** `Bytes_sent` est une variable d'état interne de MariaDB qui comptabilise le nombre exact d'octets envoyés par le serveur au client sur la connexion active. En relevant sa valeur juste avant et juste après la requête, la différence mesure précisément le volume réseau généré par l'opération.
* **Honnêteté de la mesure :** Elle est objective et isolée car elle est mesurée à la source par le SGBD lui-même et **uniquement pour la session courante** (`SHOW SESSION STATUS`), sans être biaisée par le trafic des autres utilisateurs connectés simultanément.

---

## 🔒 Partie 5 : Sécurité et cloisonnement réseau

Activation du pare-feu `ufw` sur VM1 pour restreindre l'accès au port `3306` (MariaDB) uniquement à l'adresse IP du serveur d'application VM2 (`192.168.56.12`).

### Réponses aux questions

#### **Q14. Que se passe-t-il pour chaque architecture ? Pourquoi ne peut-on pas appliquer cette protection en 2-tiers ?**
* **En 2-tiers :** Le client lourd sur le poste hôte (`192.168.56.1`) échoue avec l'erreur : `Connexion impossible au serveur de base de données : (2003, "Can't connect to MySQL server on '192.168.56.11' (timed out)")`.
* **En 3-tiers :** L'application web **continue de fonctionner normalement** depuis le navigateur du poste hôte, car la requête HTTP transite par VM2 (`192.168.56.12`), qui est autorisée à interroger MariaDB.
* **Impossibilité en 2-tiers :** Dans une architecture 2-tiers, chaque poste client doit dialoguer directement avec le SGBD. Appliquer ce filtrage bloquerait tous les utilisateurs ; ouvrir le port `3306` à tous les postes annulerait la protection.

#### **Q15. Deux autres risques de sécurité propres au client lourd, et comment le 3-tiers les réduit.**
1. **Exposition des secrets de connexion :** En 2-tiers, les identifiants de la base sont stockés dans le code distribué sur les postes clients (facilement extractibles). *En 3-tiers, les identifiants restent confinés sur le serveur d'application (inaccessibles aux utilisateurs).*
2. **Surface d'attaque SQL illimitée :** En 2-tiers, l'utilisateur dispose d'un accès direct au port SQL et peut forger n'importe quelle requête ad hoc. *En 3-tiers, le serveur d'application expose uniquement des fonctionnalités encadrées (requêtes préparées) avec un compte SGBD aux privilèges strictement limités (`SELECT` uniquement).*

---

## 📝 Synthèse et Conclusion

### Tableau récapitulatif

| Critère | Architecture 2-tiers | Architecture 3-tiers |
| :--- | :--- | :--- |
| **Logiciel à installer sur chaque poste** | Python 3, `pymysql` et le script client | Un navigateur web uniquement |
| **Déploiement d'une nouvelle règle** | À refaire manuellement sur chaque poste | 1 seul fichier sur 1 serveur central |
| **Cohérence entre utilisateurs** | Risque élevé de désynchronisation des versions | Règle unique et immédiate pour tous |
| **Trafic réseau côté client** | Élevé (rapatriement des données brutes) | Très faible (pages HTML légères) |
| **Exposition du SGBD et des mots de passe** | Forte (port `3306` ouvert, secrets dans le code) | Faible (SGBD cloisonné par pare-feu) |
| **Charge de calcul** | Supportée par les postes clients | Supportée par les serveurs (SGBD / Web) |
| **Simplicité de développement** | Simple (un seul programme monolithique) | Plus complexe (séparation en 3 couches) |

#### **Q16. Quand le 2-tiers est-il acceptable ? Pourquoi choisir le 3-tiers pour la scolarité de toute l'université ?**
* **Conditions d'acceptabilité du 2-tiers :** Il reste pertinent pour un nombre très restreint d'utilisateurs de confiance, opérant sur un réseau local privé et sécurisé, avec des règles métier stables et de faibles volumes de données (ex. : caisse enregistreuse d'une boutique, poste de saisie d'un laboratoire, outil d'administration SGBD).
* **Justification du 3-tiers pour l'université :**
  * **Passage à l'échelle :** Des milliers d'étudiants et d'agents se connectent depuis des terminaux variés (PC, smartphones) sans installation préalable.
  * **Intégrité et équité :** Garantit que la même règle pédagogique s'applique simultanément à tous.
  * **Maintenabilité :** Centralise les mises à jour métier sur un serveur unique.
  * **Sécurité :** Isole la base de données critique derrière un serveur applicatif et un pare-feu strict.
  * **Performance réseau :** Préserve la bande passante en ne transmettant que les résultats formatés.