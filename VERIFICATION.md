# Vérification approfondie — HealthNet (Django 1.6.5)

Date : 2026-07-18
Environnement de test : Python 3.11.2 + Django 1.6.5 + zombie-imp (venv local)
Rapport basé sur une reproduction réelle de l'erreur et des tests d'exécution.

---

## 1. Résumé exécutif

L'application **ne démarre pas** avec la configuration fournie, mais **ce n'est pas une seule erreur** :
c'est une cascade de trois problèmes, le premier étant celui que vous avez collé (traceback `DatabaseFeatures`).

| # | Problème | Gravité | État |
|---|----------|---------|------|
| 1 | `DatabaseFeatures()` / `BaseDatabaseValidation()` appelés sans `connection` dans `json_database/base.py` | Bug réel | **Corrigé** |
| 2 | Le backend `json_database` est **fondamentalement incomplet** (pas de `Database`, `get_new_connection`, `create_cursor`, `get_autocommit`, `is_usable`…) → il ne peut pas exécuter de requêtes | Critique | Non corrigible tel quel (voir §4) |
| 3 | Les « shims » de `manage.py` ne patchent pas `DistutilsMetaFinder` → `AttributeError` sur **chaque requête** même avec un vrai backend | Bug réel | **Corrigé** |

**Résultat après corrections** : l'application **fonctionne de bout en bout** sur Python 3.11
avec le backend **SQLite natif** (qui contient déjà les données : `db.sqlite3`).

> ⚠️ Vous étiez sur **Python 3.14** (d'après le traceback : `Python314`). Le README recommande
> **Python 3.11.x**. Le 3.14 est non testé ici ; les mêmes correctifs s'appliquent, mais
> Django 1.6.5 (2014) n'est officiellement supporté sur **aucun** Python ≥ 3.5.

---

## 2. Reproduction de l'erreur que vous avez collée

Commande : `python manage.py syncdb --noinput`

```
File ".../json_database/base.py", line 145, in __init__
    self.features = DatabaseFeatures()
TypeError: BaseDatabaseFeatures.__init__() missing 1 required positional argument: 'connection'
```

Dans Django 1.6.5, `BaseDatabaseFeatures.__init__(self, connection)` **exige** `connection`.
La classe `DatabaseWrapper` du backend custom l'instancie sans argument → crash immédiat dès
qu'une connexion est créée (chargement de `django.contrib.auth` au démarrage).

**Cause racine** : `json_database/base.py` lignes 145 & 150 :
```python
self.features = DatabaseFeatures()          # ← manque self
self.validation = BaseDatabaseValidation()  # ← manque self
```
Toutes les autres sous-classes (`DatabaseOperations`, `DatabaseClient`, `DatabaseCreation`,
`DatabaseIntrospection`) reçoivent bien `self` — seules ces deux-là ont été oubliées.

**Correction appliquée** :
```python
self.features = DatabaseFeatures(self)
self.validation = BaseDatabaseValidation(self)
```

---

## 3. Le deuxième mur : le backend `json_database` est incomplet

Même après le correctif ci-dessus, `syncdb` échoue encore :
```
AttributeError: 'DatabaseWrapper' object has no attribute 'Database'
```

`BaseDatabaseWrapper` exige que la sous-classe implémente (abstraites, lèvent
`NotImplementedError`) :
- `Database` (le module DB-API, ex. `sqlite3`)
- `get_connection_params()`, `get_new_connection()`, `init_connection_state()`
- `create_cursor()`, `is_usable()`, `get_autocommit()`

Le backend `json_database` **n'implémente aucune** de ces méthodes. Son `JSONCursor` fait un
« parser SQL » naïf (extrait le nom de table par `split()`, filtre `WHERE` de façon factice,
renvoie `True` pour la plupart des paramètres). **Il ne peut pas soutenir l'ORM Django réel.**

De plus, `convert_sqlite_to_json.py` + `db.json` montrent que ce backend JSON est une
**expérience annexe** : l'application d'origine utilisait **SQLite** (`db.sqlite3` existe et
contient les vraies données). Le README ne mentionne `json_database` **nulle part**.

**Décision** : basculer `DATABASES` sur le backend SQLite natif (déjà présent et peuplé).
C'est la configuration d'origine et la seule fonctionnelle.

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
```

---

## 4. Le troisième mur : les « shims » de manage.py sont incomplets

Avec SQLite, `syncdb` réussit et les modèles se chargent. Mais le serveur renvoyait
**HTTP 500 sur chaque page** :
```
AttributeError: 'DistutilsMetaFinder' object has no attribute 'find_module'
  django/utils/module_loading.py in module_has_submodule, line 50
```

Django 1.6 appelle `finder.find_module(...)` sur **chaque** entrée de `sys.meta_path`.
Les shims de `manage.py` patchent `BuiltinImporter`/`FrozenImporter`/`PathFinder`/`FileFinder`,
mais **oublient `_distutils_hack.DistutilsMetaFinder`** (injecté par setuptools). D'où le crash
à chaque résolution d'app / templatetag.

**Correction appliquée** dans `manage.py` (bloc 4b) : on patche `find_module` sur **tous**
les finders présents dans `sys.meta_path` (pas seulement les classes connues), en déléguant à
`find_spec()` (PEP 451), avec repli si `find_spec` ne prend qu'un argument.

---

## 5. Vérification d'exécution (preuves)

Après les 3 correctifs + backend SQLite, sur Python 3.11 :

**a) syncdb**
```
Creating tables ...
Installing custom SQL ...
Installing indexes ...
Installed 0 object(s) from 0 fixture(s)   # tables déjà présentes → OK
```

**b) Requêtes ORM sur les données existantes**
```
Profiles: 7   Hospitals: 2   Accounts: 7   MedicalTests: 0   Messages: 1
Sample hospital: Strong
→ la couche modèle/requêtes fonctionne parfaitement
```

**c) Serveur de dev (`manage.py runserver`) — pages réelles**
```
200  /                       (Healthnet Login)
200  /register/
302  /logout/                (redirige vers login → auth OK)
302  /error/denied/
302  /appointment/list/      (302 = redirigé vers login car non authentifié → logique correcte)
302  /profile/
302  /medtest/list/
302  /admission/list/
302  /prescription/list/
302  /medicalinfo/list/
302  /message/list/
200  /admin/                 (interface admin Django)
```

Toutes les pages protégées renvoient **302 → login** (comportement attendu sans session),
et les pages publiques/l'admin renvoient **200**. L'application tourne.

---

## 6. Changements appliqués

| Fichier | Changement |
|---------|-----------|
| `json_database/base.py` | `DatabaseFeatures()` → `DatabaseFeatures(self)` ; `BaseDatabaseValidation()` → `BaseDatabaseValidation(self)` |
| `manage.py` | Bloc 4b : patch `find_module` sur **tous** les `sys.meta_path` (couvre `DistutilsMetaFinder`) |
| `prototype/settings.py` | `ENGINE: 'json_database'` → `'django.db.backends.sqlite3'`, `NAME: db.json` → `db.sqlite3` |

> Si vous tenez absolument au stockage JSON, il faut **réimplémenter entièrement** le backend
> (connexion, transactions, `create_cursor`, `is_usable`…) ou utiliser une vraie base
> compatible JSON — le parser SQL actuel ne suffit pas. SQLite reste la solution immédiate.

---

## 7. Recommandations

1. **Court terme (pour faire tourner l'app maintenant)**
   - Utiliser **Python 3.11** (recommandé par le README), pas 3.14.
   - Laisser le backend sur **SQLite** (corrections déjà appliquées).
   - Lancer : `pip install -r requirements.txt` → `python manage.py syncdb --noinput` → `python manage.py runserver`.

2. **À moyen terme (robustesse)**
   - Les 3 correctifs ci-dessus sont des rustines sur Django 1.6.5 (EOL depuis 2015).
     Elles fonctionnent mais restent fragiles (toute MAJ de setuptools/Python peut casser un shard).

3. **Long terme (vraie solution)**
   - **Migrer vers une Django supporté** (4.2 LTS ou 5.x) + Python 3.11/3.12.
     Travaux nécessaires : `urlpatterns = patterns(...)` → `path()`/`re_path()` ;
     `MIDDLEWARE_CLASSES` → `MIDDLEWARE` ; `class Admin:` → `@admin.register` ;
     `transaction.commit_on_success_unless_managed` → API `atomic()` ;
     templates & settings 1.6→moderne. C'est un chantier, mais c'est le seul chemin durable.

4. **Bugs applicatifs connus** (listés dans le README, non bloquants) :
   rendez-vous qui se chevauchent, emails en double selon la casse, rôle admin modifiable,
   assurance requise pour les employés, pas d'images sur les tests médicaux, stats non affichées.

---

## 8. Pour tester vous-même

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install "Django==1.6.5" zombie-imp
python manage.py syncdb --noinput
python manage.py runserver
# Ouvrir http://127.0.0.1:8000
```

Identifiants de démo (README) :
- Admin Django : `admin` / `password`
- Admin HealthNet : `admina@test.com` / `a`
- Docteur : `doctora@test.com` / `a`
