# Projet « FlexiStaff » : guide de labellisation

|  |  |
| --- | --- |
| **Version** | 1.0 (brouillon) |
| **Date** | 16/11/2026 |
| **Rédigé par** | \[à compléter : noms de l'équipe\] |
| **Outil** | CVAT, organisation *FlexiStaff*, projet `team-aqua` |
| **Format d'export** | Ultralytics YOLO Detection 1.0 |

## 1. Objectif

FlexiStaff, agence d'intérim, reçoit des photos de plannings d'employés. Le modèle doit **localiser les zones utiles** de chaque planning (entreprise, semaine, employé, jours et horaires) afin que leur contenu soit ensuite lu et structuré automatiquement.

Une zone oubliée est une donnée perdue : en cas de doute sur la **présence** d'une zone, **on l'annote** (le rappel prime sur la précision). En cas de doute sur sa **classe**, on suit les règles de la section 6.

## 2. Données

- **Source** : \[à compléter : nombre d'images, origine des photos\]
- **Conditions variées** : photos prises au smartphone, plannings imprimés ou affichés, cadrage oblique, reflets, flou, éclairage inégal, formats de planning différents selon les entreprises.
- **Taille** : \[à compléter\]. Aucun redimensionnement avant l'annotation.

## 3. Les classes

| ID | Classe | Définition | Exemples | Contre-exemples |
| --- | --- | --- | --- | --- |
| 0 | `Planning` | Page ou document complet. Sa présence valide que l'image est bien un planning. | Feuille imprimée entière, tableau affiché sur un panneau | Photo sans planning, document d'un autre type (facture, contrat) |
| 1 | `Entreprise` | Nom de l'entreprise pour laquelle le planning est établi. | Nom ou logo texte en en-tête | Nom de l'agence d'intérim, nom d'un lieu ou d'un site |
| 2 | `ref_semaine_planning` | Indication de la semaine considérée. Selon les cas : numéro de semaine, mois + semaine, ou les 7 jours de la semaine (début le lundi). | « Semaine 46 », « Novembre, semaine 3 », bandeau Lun → Dim avec les dates | Date d'impression ou de mise à jour du document |
| 3 | `employe_poste` | Nom et prénom de l'employé s'ils sont présents, sinon le poste. | « Dupont Marie », « Cariste » | Nom du responsable, nom de l'entreprise |
| 4 | `horaire_lieu_jour_tache` | Zone quotidienne regroupant le jour, l'horaire, le lieu et la tâche. | Case « Lundi 08h-16h, Entrepôt B, préparation de commandes » | Case de légende, ligne de total d'heures |
| 5 | `semaine_employe` | Englobe le nom-prénom de l'employé et toutes ses tâches de la semaine. | Ligne complète d'un employé dans un tableau | Tableau entier (c'est `Planning`) |

> **ID** = index de classe YOLO, donné par l'ordre des labels dans le projet CVAT (et non par l'identifiant interne de CVAT). À vérifier dans le `data.yaml` de l'export.

> **Pourquoi ces classes ?** Chacune correspond à une information à extraire. `Planning` valide le type de document, `semaine_employe` regroupe ce qui appartient à un même employé pour la même semaine, et `horaire_lieu_jour_tache` découpe cette semaine en journées.

## 4. Règles générales de tracé

1. **Rectangles uniquement** (pas de polygones), alignés sur les axes de l'image. Si le planning est photographié de travers, on trace le plus petit rectangle qui l'englobe.
2. **Boîte serrée** : le rectangle englobe la zone en entier, avec une **marge de 2 à 5 px** au maximum.
3. **Une zone = une boîte.** Deux employés : deux boîtes `semaine_employe`.
4. **Imbrication attendue** : `employe_poste` et les `horaire_lieu_jour_tache` d'un employé sont **à l'intérieur** de sa boîte `semaine_employe`, elle-même à l'intérieur de `Planning`. Les chevauchements sont normaux.
5. **Zone partiellement visible** (coupée par le bord de l'image ou masquée) : on l'annote si **au moins la moitié du texte utile est lisible** \[seuil à confirmer en équipe\]. La boîte couvre uniquement la partie visible.
6. **Flou ou reflet** : on annote si un humain peut lire la zone. Sinon, on n'annote pas.

## 5. Règles par classe

#### `Planning`

- Une seule boîte par document planning visible. Elle couvre toute la page, titre et légende compris.
- Si plusieurs plannings sont visibles sur l'image : une boîte par planning.

#### `Entreprise`

- On encadre le nom seul, sans le texte voisin (adresse, slogan).
- Si le nom apparaît plusieurs fois, on annote \[première occurrence / toutes : à décider\].

#### `ref_semaine_planning`

- La boîte couvre l'indication de semaine **en entier** : pour une semaine exprimée en 7 jours, on encadre la rangée de dates du lundi au dimanche d'un seul tenant.
- Mois et numéro de semaine séparés dans le document : une seule boîte qui les englobe si c'est possible, sinon une boîte par élément \[à confirmer\].

#### `employe_poste`

- Nom et prénom présents : on encadre les deux ensemble.
- Nom absent : on encadre le poste.
- Les deux présents : une seule boîte qui englobe nom et poste s'ils sont voisins.

#### `horaire_lieu_jour_tache`

- **Une boîte par jour** : on englobe tout ce qui concerne ce jour (jour, horaire, lieu, tâche).
- Jour sans information (repos, case vide) : on annote la case comme n'importe quel autre jour, avec la même classe.

#### `semaine_employe`

- La boîte englobe le nom-prénom de l'employé **et** toutes les zones quotidiennes de sa semaine.
- Elle ne déborde pas sur la ligne ou la colonne de l'employé voisin.

## 6. Cas limites (décisions prises en équipe)

| Situation | Décision | Date |
| --- | --- | --- |
| Planning sans nom d'employé (seulement un poste) | `employe_poste` sur le poste ; `semaine_employe` englobe le poste et les tâches. | \[à valider\] |
| Planning d'une seule personne | Une seule `semaine_employe`, qui peut être presque aussi grande que `Planning`. | \[à valider\] |
| Plusieurs semaines sur la même page | Une `ref_semaine_planning` par semaine et les `semaine_employe` correspondantes. | \[à valider\] |
| Image qui n'est pas un planning | **Aucune annotation**, image conservée : le modèle doit aussi apprendre à reconnaître ce cas. | \[à valider\] |
| Image entièrement floue, trop sombre ou illisible | Image **rejetée** (tag `rejetee`). | \[à valider\] |

> Toute nouvelle situation ambiguë est signalée sur le canal de l'équipe. **On ne décide pas seul** : la décision est ajoutée à ce tableau et s'applique à tout le monde.

## 7. Ce qu'on n'annote pas

- Les éléments décoratifs : logo de l'agence, bordures, couleurs de fond.
- Les mentions administratives : date d'impression, pied de page, numéro de page.
- Les légendes et codes couleur, sauf s'ils font partie d'une zone quotidienne.
- Les annotations manuscrites sans lien avec le planning.
- Les zones visibles à moins de la moitié, ou illisibles.

## 8. Exemple annoté

```
┌───────────────────────────────────────────────────────┐
│ [Planning]                                            │
│  ┌──────────────┐        ┌──────────────────────────┐ │
│  │ [Entreprise] │        │ [ref_semaine_planning]   │ │
│  └──────────────┘        └──────────────────────────┘ │
│                                                       │
│  ┌─ [semaine_employe] ────────────────────────────┐   │
│  │ ┌──────────────┐ ┌────────┐ ┌────────┐ ┌─────┐ │   │
│  │ │[employe_poste]│ │[h_l_j_t]│ │[h_l_j_t]│ │ ... │ │   │
│  │ └──────────────┘ │  Lundi │ │ Mardi  │ └─────┘ │   │
│  │                  └────────┘ └────────┘         │   │
│  └────────────────────────────────────────────────┘   │
│  ┌─ [semaine_employe] ────────────────────────────┐   │
│  │ ... (employé suivant)                          │   │
│  └────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────┘
  h_l_j_t = horaire_lieu_jour_tache
  Les boîtes sont imbriquées : employe_poste et les zones quotidiennes
  sont dans semaine_employe, elle-même dans Planning.
```

## 9. Contrôle qualité

- **Double annotation** : 10 % des images, tirées au hasard, sont annotées par deux personnes. Chaque désaccord est discuté et, si besoin, ajouté aux cas limites (section 6).
- **Revue croisée** : chaque job terminé est relu par un autre membre de l'équipe avant validation.
- **Vérifications avant export** :
  - toute image avec un planning contient une boîte `Planning` ;
  - chaque `semaine_employe` contient exactement un `employe_poste` ;
  - chaque `ref_semaine_planning` et chaque `Entreprise` visibles sont annotées ;
  - aucune boîte minuscule (moins de 5 px de côté) ;
  - répartition des classes vérifiée : si une classe est très rare, on le signale.

## 10. Répartition du travail

| Membre | Images | Relecture de |
| --- | --- | --- |
| \[à compléter\] |  |  |

## 11. Historique des versions

| Version | Date | Modification |
| --- | --- | --- |
| 1.0 | 16/11/2026 | Première version : 6 classes, règles générales, cas limites à valider. |
