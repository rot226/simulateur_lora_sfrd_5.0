# Guide d'extension du tableau de bord

Ce document explique comment personnaliser `launcher/dashboard.py` et ajouter de
nouvelles fonctionnalit\u00e9s au simulateur.

## Principe g\u00e9n\u00e9ral

Le tableau de bord repose sur [Panel](https://panel.holoviz.org/) pour
l'affichage et sur `plotly` pour les graphiques. Les options utilisateur sont
d\u00e9finies dans la classe `SimulatorUI`.

## Ajouter un param\u00e8tre au tableau de bord

1. D\u00e9clarez le nouveau champ dans `SimulatorUI.__init__`.
2. Passez la valeur au constructeur de `Simulator` dans `launch_sim`.
3. Mettez \u00e0 jour `update_metrics` pour afficher la m\u00e9trique associ\u00e9e.

Les fonctions existantes illustrent chaque \u00e9tape en d\u00e9tail.

## Int\u00e9grer un module personnalis\u00e9

Vous pouvez remplacer les classes du simulateur pour tester d'autres
comportements :

```python
from launcher import Simulator, PathMobility

class MyMobility(PathMobility):
    def step(self, node, dt):
        # Impl\u00e9mentation sp\u00e9cifique
        super().step(node, dt)

sim = Simulator(mobility_model=MyMobility(...))
```

Les fichiers `gateway.py`, `node.py` et `server.py` peuvent \u00eatre h\u00e9rit\u00e9s pour
ajouter de nouvelles logiques.

## Conseils aux contributeurs

Avant de proposer une pull request, v\u00e9rifiez que `pytest` s'ex\u00e9cute sans
\u00e9chec et ajoutez des tests lorsque c'est pertinent.
