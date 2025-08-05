# Guide d'extension du tableau de bord

Ce document explique comment personnaliser `launcher/dashboard.py` et ajouter de
nouvelles fonctionnalités au simulateur.

## Principe général

Le tableau de bord repose sur [Panel](https://panel.holoviz.org/) pour
l'affichage et sur `plotly` pour les graphiques. Les options utilisateur sont
désormais déclarées via des widgets Panel au début de
`launcher/dashboard.py`.

## Ajouter un paramètre au tableau de bord

1. Créez un nouveau widget `pn.widgets.*` dans `launcher/dashboard.py`.
2. Passez sa valeur au constructeur de `Simulator` dans `setup_simulation`.
3. Mettez à jour les fonctions d'affichage (par exemple `metrics_col` ou
   `update_histogram`) pour afficher la métrique associée.

Les fonctions existantes illustrent chaque étape en détail.

## Intégrer un module personnalisé

Vous pouvez remplacer les classes du simulateur pour tester d'autres
comportements :

```python
from simulateur_lora_sfrd.launcher import Simulator, PathMobility

class MyMobility(PathMobility):
    def step(self, node, dt):
        # Implémentation spécifique
        super().step(node, dt)

sim = Simulator(mobility_model=MyMobility(...))
```

Les fichiers `gateway.py`, `node.py` et `server.py` peuvent être hérités pour
ajouter de nouvelles logiques.

## Conseils aux contributeurs

Avant de proposer une pull request, vérifiez que `pytest` s'exécute sans échec et ajoutez des tests lorsque c'est pertinent.
