# Simulateur Réseau LoRa (Python 3.10+)

Bienvenue ! Ce projet est un **simulateur complet de réseau LoRa**, inspiré du fonctionnement de FLoRa sous OMNeT++, codé entièrement en Python.
Pour un apercu des differences avec FLoRa, consultez docs/lorawan_features.md.
Les principales équations sont décrites dans docs/equations_flora.md.
## 🛠️ Installation

1. **Clonez ou téléchargez** le projet.
2. **Créez un environnement virtuel et installez le projet :**
   ```bash
   python3 -m venv env
   source env/bin/activate  # Sous Windows : env\Scripts\activate
   pip install -e .
   # ou avec les dépendances de développement :
   pip install -e .[dev]
   ```
   Cette commande compile également la bibliothèque native `libflora_phy.so`
   qui permet d'utiliser par défaut le calcul de BER exact.
3. **Lancez le tableau de bord :**
```bash
panel serve launcher/dashboard.py --show
```
Définissez la valeur du champ **Graine** pour réutiliser le même placement de
nœuds et la même suite d'intervalles pseudo‑aléatoires d'une simulation à
l'autre. Le champ **Nombre de runs** permet quant à lui d'enchaîner
automatiquement plusieurs simulations identiques (la graine est incrémentée à
chaque run).
Activez l'option **Positions manuelles** pour saisir les coordonnées exactes de
certains nœuds ou passerelles ; chaque ligne suit par exemple `node,id=3,x=120,y=40`
ou `gw,id=1,x=10,y=80`. Cela permet notamment de reprendre les positions
fournies dans l'INI de FLoRa.
4. **Exécutez des simulations en ligne de commande :**
   ```bash
   python run.py --nodes 30 --gateways 1 --mode Random --interval 10 --steps 100 --output résultats.csv
   python run.py --nodes 20 --mode Random --interval 15 --first-interval 5
   python run.py --nodes 5 --mode Periodic --interval 10
   ```
    Ajoutez l'option `--seed` pour reproduire exactement le placement des nœuds
    et l'ordre statistique des intervalles.
    Utilisez `--runs <n>` pour exécuter plusieurs simulations d'affilée et
    obtenir une moyenne des métriques.

5. **Démarrez l'API REST/WebSocket (optionnelle) :**
   ```bash
   uvicorn launcher.web_api:app --reload
   ```
   L'endpoint `POST /simulations/start` accepte un JSON
   `{"command": "start_sim", "params": {...}}` pour lancer une simulation.
   Les métriques en temps réel sont diffusées sur le WebSocket `/ws` sous la
   forme `{"event": "metrics", "data": {...}}`.

## Exemples d'utilisation avancés

Quelques commandes pour tester des scénarios plus complexes :

```bash
# Simulation multi-canaux avec mobilité
python run.py --nodes 50 --gateways 2 --channels 3 \
  --mobility --steps 500 --output advanced.csv

# Démonstration LoRaWAN avec downlinks
python run.py --lorawan-demo --steps 100 --output lorawan.csv
```

### Exemples classes B et C

Utilisez l'API Python pour tester les modes B et C :

```python
from simulateur_lora_sfrd.launcher import Simulator

# Nœuds en classe B avec slots réguliers
sim_b = Simulator(num_nodes=10, node_class="B", beacon_interval=128,
                  ping_slot_interval=1.0)
sim_b.run(1000)

# Nœuds en classe C à écoute quasi continue
sim_c = Simulator(num_nodes=5, node_class="C", class_c_rx_interval=0.5)
sim_c.run(500)

```

### Scénario de mobilité réaliste

Les déplacements peuvent être rendus plus doux en ajustant la plage de vitesses :

```python
from simulateur_lora_sfrd.launcher import Simulator

sim = Simulator(num_nodes=20, num_gateways=3, area_size=2000.0, mobility=True,
                mobility_speed=(1.0, 5.0))
sim.run(1000)
```

## Duty cycle

Le simulateur applique par défaut un duty cycle de 1 % pour se rapprocher des
contraintes LoRa réelles. Le gestionnaire de duty cycle situé dans
`duty_cycle.py` peut être configuré en passant un autre paramètre `duty_cycle`
à `Simulator` (par exemple `0.02` pour 2 %). Transmettre `None` désactive ce
mécanisme. Les transmissions sont automatiquement retardées pour respecter ce
pourcentage.

## Mobilité optionnelle

La mobilité des nœuds peut désormais être activée ou désactivée lors de la
création du `Simulator` grâce au paramètre `mobility` (booléen). Dans le
`dashboard`, cette option correspond à la case « Activer la mobilité des
nœuds ». Si elle est décochée, les positions des nœuds restent fixes pendant
la simulation.
Lorsque la mobilité est active, les déplacements sont progressifs et suivent
des trajectoires lissées par interpolation de Bézier. La vitesse des nœuds est
tirée aléatoirement dans la plage spécifiée (par défaut 2 à 10 m/s) et peut être
modifiée via le paramètre `mobility_speed` du `Simulator`. Les mouvements sont
donc continus et sans téléportation.
Un modèle `PathMobility` permet également de suivre des chemins définis sur une
grille en évitant les obstacles et peut prendre en compte un relief ainsi que
des hauteurs de bâtiments. L'altitude du nœud est alors mise à jour à chaque
déplacement pour un calcul radio plus réaliste. Ce modèle peut désormais lire
une **carte d'obstacles dynamiques** (fichier JSON) listant les positions,
rayons et vitesses des objets à éviter.
Deux champs « Vitesse min » et « Vitesse max » sont disponibles dans le
`dashboard` pour définir cette plage avant de lancer la simulation.
Plusieurs schémas supplémentaires peuvent être utilisés :
- `RandomWaypoint` gère les déplacements aléatoires en s'appuyant sur une carte
  de terrain et sur des obstacles dynamiques optionnels.
- `PlannedRandomWaypoint` applique la même logique mais choisit un point d'arrivée
  aléatoire puis planifie un chemin en A* pour contourner un relief 3D ou des
  obstacles fixes. Une option `slope_limit` permet d'éviter les pentes trop fortes.
- `TerrainMapMobility` permet désormais de suivre une carte rasterisée en
  pondérant la vitesse par cellule et en tenant compte d'obstacles 3D.
- `PathMobility` et le planificateur A* acceptent également un `slope_limit`
  pour ignorer les transitions dépassant une inclinaison donnée.
- `GaussMarkov` et les traces GPS restent disponibles pour modéliser des
  mouvements plus spécifiques.
- `Trace3DMobility` lit une trace temporelle et suit le relief 3D en bloquant
  les passages au-dessus d'une hauteur maximale.

## Multi-canaux

Le simulateur permet d'utiliser plusieurs canaux radio. Passez une instance
`MultiChannel` ou une liste de fréquences à `Simulator` via les paramètres
`channels` et `channel_distribution`. Dans le `dashboard`, réglez **Nb
sous-canaux** et **Répartition canaux** pour tester un partage Round‑robin ou
aléatoire des fréquences entre les nœuds.

## Durée et accélération de la simulation

Le tableau de bord permet maintenant de fixer une **durée réelle maximale** en secondes. Par défaut cette limite vaut `86400` s (24 h). Lorsque cette limite est atteinte, la simulation s'arrête automatiquement. Un bouton « Accélérer jusqu'à la fin » lance l'exécution rapide pour obtenir aussitôt les métriques finales.
**Attention :** cette accélération ne fonctionne que si un nombre fini de paquets est défini. Si le champ *Nombre de paquets* vaut 0 (infini), la simulation ne se termine jamais et l'export reste impossible.
Depuis la version 4.0.1, une fois toutes les transmissions envoyées, l'accélération désactive la mobilité des nœuds restants afin d'éviter un blocage du simulateur.

## Suivi de batterie

Chaque nœud peut être doté d'une capacité d'énergie (en joules) grâce au paramètre `battery_capacity_j` du `Simulator`. La consommation est calculée selon le profil d'énergie FLoRa (courants typiques en veille, réception, etc.) puis retranchée de cette réserve. Le champ `battery_remaining_j` indique l'autonomie restante.
Un champ **Capacité batterie (J)** est disponible dans le tableau de bord pour
saisir facilement cette valeur. Indiquez `0` pour une capacité illimitée : ce
nombre est automatiquement converti en `None`, valeur attendue par le simulateur.

## Paramètres du simulateur

Le constructeur `Simulator` accepte de nombreux arguments afin de reproduire les
scénarios FLoRa. Voici la liste complète des options :

- `num_nodes` : nombre de nœuds à créer lorsque aucun fichier INI n'est fourni.
- `num_gateways` : nombre de passerelles générées automatiquement.
- `area_size` : dimension (m) du carré dans lequel sont placés nœuds et
  passerelles.
- `transmission_mode` : `Random` (émissions Poisson) ou `Periodic`.
- `packet_interval` : moyenne ou période fixe entre transmissions (s).
  La valeur par défaut est `100` s.
- `first_packet_interval` : moyenne exponentielle appliquée uniquement au
  premier envoi (`None` pour reprendre `packet_interval`). Par défaut `100` s.
- `interval_variation`: coefficient de jitter appliqué multiplicativement
  à l'intervalle exponentiel (0 par défaut pour coller au comportement FLoRa). L'intervalle est multiplié par `1 ± U` avec `U` échantillonné dans `[-interval_variation, interval_variation]`.
 - Les instants de transmission suivent strictement une loi exponentielle de
   moyenne `packet_interval` lorsque le mode `Random` est sélectionné.
- Tous les échantillons sont conservés ; si une transmission est encore en
  cours, la date tirée est simplement repoussée après son terme. Cette logique
  est implémentée par `ensure_poisson_arrivals` et `schedule_event` à partir de
  la valeur extraite via `parse_flora_interval`.
- Les intervalles restent indépendants des collisions et du duty cycle : le
  prochain tirage Poisson est basé sur le début réel de la dernière émission
  (`last_tx_time`).
- `packets_to_send` : nombre de paquets émis **par nœud** avant arrêt (0 = infini).
- `lock_step_poisson` : pré-génère une séquence Poisson réutilisée entre exécutions (nécessite `packets_to_send`).
- `adr_node` / `adr_server` : active l'ADR côté nœud ou serveur.
- `duty_cycle` : quota d'émission appliqué à chaque nœud (`None` pour désactiver).
- `mobility` : active la mobilité aléatoire selon `mobility_speed`.
- `channels` : instance de `MultiChannel` ou liste de fréquences/`Channel`.
- `channel_distribution` : méthode d'affectation des canaux (`round-robin` ou
  `random`).
- `mobility_speed` : couple *(min, max)* définissant la vitesse des nœuds
  mobiles (m/s).
- `fixed_sf` / `fixed_tx_power` : valeurs initiales communes de SF et puissance.
- `battery_capacity_j` : énergie disponible par nœud (`None` pour illimité ;
  la valeur `0` saisie dans le tableau de bord est convertie en `None`).
- `payload_size_bytes` : taille du payload utilisée pour calculer l'airtime.
- `node_class` : classe LoRaWAN de tous les nœuds (`A`, `B` ou `C`).
- `detection_threshold_dBm` : RSSI minimal pour qu'une réception soit valide.
- `min_interference_time` : durée de chevauchement minimale pour déclarer une
  collision (s). Deux transmissions sont en collision lorsqu'elles partagent la
  même fréquence et le même Spreading Factor tout en se superposant plus
  longtemps que cette valeur.
- `config_file` : chemin d'un fichier INI ou JSON décrivant
  positions, SF et puissance.
- `seed` : graine aléatoire utilisée pour reproduire le placement des nœuds et le même ordre statistique des intervalles.
- `class_c_rx_interval` : période de vérification des downlinks en classe C.
- `beacon_interval` : durée séparant deux beacons pour la classe B (s).
- `ping_slot_interval` : intervalle de base entre ping slots successifs (s).
- `ping_slot_offset` : délai après le beacon avant le premier ping slot (s).
- `dump_intervals` : conserve l'historique des dates Poisson et effectives.
  La méthode `dump_interval_logs()` écrit un fichier Parquet par nœud pour
  analyser la planification finale et vérifier empiriquement la loi exponentielle.
- `phase_noise_std_dB` : bruit de phase appliqué au SNR.
- `clock_jitter_std_s` : gigue d'horloge ajoutée à chaque calcul.
- `tx_start_delay_s` / `rx_start_delay_s` : délai d'activation de l'émetteur ou du récepteur.
- `pa_ramp_up_s` / `pa_ramp_down_s` : temps de montée et de descente du PA.

## Paramètres radio avancés

Le constructeur `Channel` accepte plusieurs options pour modéliser plus finement la
réception :

- `cable_loss` : pertes fixes (dB) entre le transceiver et l'antenne.
- `tx_antenna_gain_dB` : gain d'antenne de l'émetteur (dB).
- `rx_antenna_gain_dB` : gain d'antenne du récepteur (dB).
- `receiver_noise_floor` : bruit thermique de référence en dBm/Hz (par défaut
  `-174`). Cette valeur est utilisée directement par le modèle OMNeT++ pour le
  calcul du bruit de fond.
- `noise_figure` : facteur de bruit du récepteur en dB.
- `noise_floor_std` : écart-type de la variation aléatoire du bruit (dB).
- `fast_fading_std` : amplitude du fading multipath en dB.
- `multipath_taps` : nombre de trajets multipath simulés pour un
  fading plus réaliste.
- `fine_fading_std` : écart-type du fading fin corrélé.
- `variable_noise_std` : bruit thermique lentement variable (dB).
- `freq_drift_std_hz` et `clock_drift_std_s` : dérives de fréquence et
  d'horloge corrélées utilisées pour le calcul du SNR.
- `clock_jitter_std_s` : gigue d'horloge ajoutée à chaque calcul.
- `temperature_std_K` : variation de température pour le calcul du bruit.
- `humidity_percent` et `humidity_noise_coeff_dB` : ajoutent un bruit
  supplémentaire proportionnel à l'humidité relative. La variation temporelle
  peut être définie via `humidity_std_percent`.
- `pa_non_linearity_dB` / `pa_non_linearity_std_dB` : modélisent la
  non‑linéarité de l'amplificateur de puissance (par défaut `-1` dB ± 0,5 dB).
- `pa_non_linearity_curve` : triplet de coefficients polynomiaux pour
  définir une non‑linéarité personnalisée.
- `pa_distortion_std_dB` : variation aléatoire due aux imperfections du PA.
- `pa_ramp_up_s` / `pa_ramp_down_s` : temps de montée et de descente du PA
  influençant la puissance effective.
  Ces paramètres interagissent désormais avec le calcul OMNeT++ pour
  reproduire fidèlement la distorsion du signal.
- `impulsive_noise_prob` / `impulsive_noise_dB` : ajout de bruit impulsif selon
  une probabilité donnée.
- Ces phénomènes sont désormais pris en compte par le modèle OMNeT++ complet
  afin d'obtenir un PER très proche des simulations FLoRa.
- Les collisions partielles sont évaluées en fonction du recouvrement réel
  lorsque `phy_model="omnet_full"`, ce qui permet de reproduire le
  comportement observé dans FLoRa.
- `adjacent_interference_dB` : pénalité appliquée aux brouilleurs situés sur un
  canal adjacent.
- `phase_noise_std_dB` : bruit de phase ajouté au SNR.
- `oscillator_leakage_dB` / `oscillator_leakage_std_dB` : fuite
  d'oscillateur ajoutée au bruit.
- `rx_fault_std_dB` : défauts de réception aléatoires pénalisant le SNR.
- `capture_threshold_dB` : différence de puissance requise pour que le paquet
  le plus fort soit décodé malgré les interférences (≥ 6 dB par défaut).
- `orthogonal_sf` : lorsqu'il vaut `False`, les transmissions de SF différents
  peuvent entrer en collision comme celles du même SF.
- `freq_offset_std_hz` et `sync_offset_std_s` : variations du décalage
  fréquentiel et temporel prises en compte par le modèle OMNeT++.
- Ces offsets corrélés sont désormais appliqués à chaque transmission,
  affinant la synchronisation et rapprochant le PER du comportement FLoRa.
- `dev_frequency_offset_hz` / `dev_freq_offset_std_hz` : dérive propre à
  chaque émetteur.
- `band_interference` : liste de brouilleurs sélectifs sous la forme
 `(freq, bw, dB)` appliqués au calcul du bruit. Chaque entrée définit
 un niveau de bruit spécifique pour la bande concernée.
- `environment` : preset rapide pour le modèle de propagation
  (`urban`, `urban_dense`, `suburban`, `rural`, `indoor` ou `flora`).
- `phy_model` : "omnet", `"omnet_full"`, "flora", "flora_full" ou `"flora_cpp"` pour utiliser un modèle physique avancé reprenant les formules de FLoRa. Le mode `omnet_full` applique directement les équations du `LoRaAnalogModel` d'OMNeT++ avec bruit variable, sélectivité de canal et une gestion précise des collisions partielles. Le mode `flora_cpp` charge la bibliothèque C++ compilée depuis FLoRa pour une précision accrue.
- `use_flora_curves` : applique directement les équations FLoRa pour la
  puissance reçue et le taux d'erreur.

```python
from simulateur_lora_sfrd.launcher.channel import Channel
canal = Channel(environment="urban")
```

Ces valeurs influencent le calcul du RSSI et du SNR retournés par
`Channel.compute_rssi`.
Un module **`propagation_models.py`** regroupe désormais plusieurs modèles :
`LogDistanceShadowing` pour la perte de parcours classique, `multipath_fading_db`
pour générer un fading Rayleigh, et la nouvelle classe `CompletePropagation`
qui combine ces effets avec un bruit thermique calibré.
Il reprend les paramètres des fichiers INI de FLoRa, par exemple `sigma=3.57` pour le preset *flora*.

```python
from simulateur_lora_sfrd.launcher.propagation_models import CompletePropagation

model = CompletePropagation(environment="flora", multipath_taps=3, fast_fading_std=1.0)
loss = model.path_loss(1000)
fad = model.rssi(14, 1000)  # RSSI avec fading multipath
sense = model.sensitivity_table(125e3)
```


Depuis cette mise à jour, la largeur de bande (`bandwidth`) et le codage
(`coding_rate`) sont également configurables lors de la création d'un
`Channel`. On peut modéliser des interférences externes via `interference_dB`
et simuler un environnement multipath avec `fast_fading_std` et
`multipath_taps`. Des variations
aléatoires de puissance sont possibles grâce à `tx_power_std`. Un seuil de
détection peut être fixé via `detection_threshold_dBm` (par
exemple `-110` dBm comme dans FLoRa) pour ignorer les signaux trop faibles.
Le paramètre `min_interference_time` de `Simulator` permet de définir une durée
de chevauchement sous laquelle deux paquets ne sont pas considérés comme en
collision.

### Modélisation physique détaillée

 Un module optionnel `advanced_channel.py` introduit des modèles de
 propagation supplémentaires inspirés de la couche physique OMNeT++. Le
 mode `cost231` applique la formule Hata COST‑231 avec les hauteurs de
 stations paramétrables et un coefficient d'ajustement via
 `cost231_correction_dB`. Un mode `cost231_3d` tient compte de la distance
 3D réelle et des hauteurs renseignées dans `tx_pos`/`rx_pos`. Un mode
 `okumura_hata` reprend la variante d'origine (urbain, suburbain ou zone
 ouverte) avec un terme correctif `okumura_hata_correction_dB`. Un mode
 `itu_indoor` permet de simuler des environnements intérieurs. Le mode
 `3d` calcule simplement la distance réelle en 3D et les autres modèles
 peuvent également prendre en compte un dénivelé si `tx_pos` et `rx_pos`
 comportent une altitude. Il est également possible de simuler un fading
 `rayleigh`, `rician` ou désormais `nakagami` pour représenter des
multi-trajets plus réalistes. Des gains d'antenne et pertes de câble
peuvent être précisés, ainsi qu'une variation temporelle du bruit grâce
à `noise_floor_std`. Des pertes liées aux conditions météo peuvent être
ajoutées via `weather_loss_dB_per_km`. Cette perte peut varier au cours
du temps en utilisant `weather_loss_std_dB_per_km` et
`weather_correlation`. Un bruit supplémentaire dépendant
de l'humidité peut également être activé grâce aux paramètres
`humidity_percent` et `humidity_noise_coeff_dB`.

```python
from simulateur_lora_sfrd.launcher.advanced_channel import AdvancedChannel
ch = AdvancedChannel(
    propagation_model="cost231_3d",
    terrain="suburban",
    okumura_hata_correction_dB=2.0,
    weather_loss_dB_per_km=1.0,
    weather_loss_std_dB_per_km=0.5,
    fading="nakagami",  # modèle corrélé dans le temps
    obstacle_losses={"wall": 5.0, "building": 20.0},
    modem_snr_offsets={"lora": 0.0},
)
```

L'objet `AdvancedChannel` peut également introduire des offsets de
fréquence et de synchronisation variables au cours du temps pour se
rapprocher du comportement observé avec OMNeT++. Les paramètres
`freq_offset_std_hz` et `sync_offset_std_s` contrôlent l'amplitude de ces
variations corrélées et améliorent la précision du taux d'erreur.
Une non‑linéarité d'amplificateur peut être
spécifiée grâce aux paramètres `pa_non_linearity_dB`,
`pa_non_linearity_std_dB` et `pa_non_linearity_curve`. Le SNR peut en
outre être corrigé par modem à l'aide de `modem_snr_offsets`.

Les autres paramètres (fréquence, bruit, etc.) sont transmis au
constructeur de `Channel` classique et restent compatibles avec le
tableau de bord. Les modèles ``rayleigh`` et ``rician`` utilisent
désormais une corrélation temporelle pour reproduire le comportement de
FLoRa et un bruit variable peut être ajouté via ``variable_noise_std``.
Un paramètre ``clock_jitter_std_s`` modélise la gigue d'horloge sur le
temps de réception. Les dérives ``freq_drift_std_hz`` et ``clock_drift_std_s``
sont gérées en continu, et le démarrage/arrêt du PA peut être simulé via
``tx_start_delay_s``/``rx_start_delay_s`` et ``pa_ramp_*``. Les équations
d'atténuation et de PER de FLoRa peuvent être activées via ``use_flora_curves``
pour un rendu encore plus fidèle. Le capture effect reprend désormais la
logique exacte de la version C++ lorsque ``phy_model`` vaut ``flora``.
Une carte ``obstacle_height_map`` peut bloquer complètement un lien en
fonction de l'altitude parcourue et les différences de hauteur sont
prises en compte dans tous les modèles lorsque ``tx_pos`` et ``rx_pos``
indiquent une altitude.
Une ``obstacle_map`` peut désormais contenir des identifiants (par
exemple ``wall`` ou ``building``) associés à des pertes définies via le
paramètre ``obstacle_losses`` pour modéliser précisément les obstacles
traversés.
Un paramètre ``obstacle_variability_std_dB`` ajoute une variation
temporelle corrélée de cette absorption pour simuler un canal évolutif.
Il est désormais possible de modéliser la sélectivité du filtre RF grâce aux
paramètres ``frontend_filter_order`` et ``frontend_filter_bw``. Une valeur non
nulle applique une atténuation dépendante du décalage fréquentiel via un filtre
Butterworth de même ordre que celui employé dans la pile FLoRa d'OMNeT++.
Un filtre d'ordre 2 est activé par défaut pour reproduire la sélectivité
matérielle ; ``frontend_filter_bw`` vaut la bande LoRa si aucune valeur
supplémentaire n'est fournie.
La sensibilité calculée utilise désormais la largeur de bande du filtre,
si bien qu'un filtre plus étroit réduit le bruit thermique et améliore
automatiquement la portée.

Le tableau de bord propose désormais un bouton **Mode FLoRa complet**. Quand il
est activé, `detection_threshold_dBm` est automatiquement fixé à `-110` dBm et
`min_interference_time` à `5` s, valeurs tirées du fichier INI de FLoRa. Un
profil radio ``flora`` est aussi sélectionné pour appliquer l'exposant et la
variance de shadowing correspondants. Les champs restent modifiables si ce mode
est désactivé. Pour reproduire fidèlement les scénarios FLoRa d'origine, pensez
également à renseigner les positions des nœuds telles qu'indiquées dans l'INI.
L'équivalent en script consiste à passer `flora_mode=True` au constructeur `Simulator`.
Lorsque `phy_model="omnet_full"` est utilisé (par exemple en mode FLoRa), le preset
`environment="flora"` est désormais appliqué automatiquement afin de conserver
un exposant de 2,7 et un shadowing de 3,57 dB identiques au modèle d'origine.
Le capture effect complet du code C++ est alors activé tandis que le PA démarre
et s'arrête selon `tx_start_delay_s`/`rx_start_delay_s` et `pa_ramp_*`. Les
dérives de fréquence ainsi que la gigue d'horloge sont incluses par défaut.

### Aligner le modèle de propagation

Pour n'utiliser que le modèle de propagation de FLoRa, créez le `Simulator`
avec l'option `flora_mode=True`. Ce mode applique automatiquement :

- un exposant de perte de parcours fixé à `2.7` ;
- un shadowing de `σ = 3.57` dB ;
- un seuil de détection d'environ `-110` dBm.
- l'utilisation automatique du modèle `omnet_full`.
- un intervalle moyen de `100` s appliqué si aucun intervalle n'est spécifié.

`Simulator` interprète `packet_interval` et `first_packet_interval` comme les
moyennes d'intervalles exponentiels lorsque le mode **Aléatoire** est actif.
Si ces deux paramètres restent à leurs valeurs par défaut en mode FLoRa, ils
sont automatiquement ramenés à `100` s afin de reproduire le comportement des
scénarios d'origine. Vous pouvez saisir d'autres valeurs dans le tableau de bord
pour personnaliser la fréquence d'émission.

### Équations FLoRa de perte de parcours et de PER

Le module `flora_phy.py` implémente la même perte de parcours que dans FLoRa :

```
loss = PATH_LOSS_D0 + 10 * n * log10(distance / REFERENCE_DISTANCE)
```

avec `PATH_LOSS_D0 = 127.41` dB et `REFERENCE_DISTANCE = 40` m. L'exposant
`n` vaut `2.7` lorsque le profil `flora` est sélectionné. Le taux d'erreur
(PER) est approché par une courbe logistique :

```
PER = 1 / (1 + exp(2 * (snr - (th + 2))))
```

où `th` est le seuil SNR par Spreading Factor ({7: -7.5, 8: -10, 9: -12.5,
10: -15, 11: -17.5, 12: -20} dB). Ces équations sont activées en passant
`phy_model="omnet_full"` ou `use_flora_curves=True` au constructeur du `Channel`.
Pour le mode OMNeT++, le taux d'erreur binaire est déterminé grâce à la
fonction `calculateBER` de `LoRaModulation` transposée telle quelle en
Python afin de reproduire fidèlement les performances de décodage.

Le calcul BER exact est désormais **activé par défaut** dans `FloraPHY`. Passez
`use_exact_ber=False` lors de sa construction pour revenir à l'approximation
logistique si vous souhaitez accélérer les simulations.

> **Remarque :** cette approche logistique reste une approximation des courbes
> PER de FLoRa. La version C++ calcule la probabilité d'erreur binaire par
> intégration dans `calculateBER`. Pour un réalisme maximal, lancez le
> simulateur avec `phy_model="flora_cpp"` : la bibliothèque native est
> compilée automatiquement lors de l'installation.

Le paramètre ``flora_loss_model`` permet de choisir parmi plusieurs modèles
d'atténuation : ``"lognorm"`` (par défaut), ``"oulu"`` correspondant à
``LoRaPathLossOulu`` (B = 128.95 dB, n = 2.32, d0 = 1000 m) ou ``"hata"`` pour
``LoRaHataOkumura`` (K1 = 127.5, K2 = 35.2).

Lorsque ``"oulu"`` est sélectionné, un shadowing gaussien de variance ``sigma``
est ajouté à l'atténuation. Cette valeur vaut ``7.8`` dB par défaut et peut être
ajustée via le paramètre ``Channel.shadowing_std``.


## SF et puissance initiaux

Deux nouvelles cases à cocher du tableau de bord permettent de fixer le
Spreading Factor et/ou la puissance d'émission de tous les nœuds avant le
lancement de la simulation. Une fois la case cochée, sélectionnez la valeur
souhaitée via le curseur associé (SF 7‑12 et puissance 2‑20 dBm). Si la case est
décochée, chaque nœud conserve des valeurs aléatoires par défaut.

## Fonctionnalités LoRaWAN

Une couche LoRaWAN simplifiée est maintenant disponible. Le module
`lorawan.py` définit la structure `LoRaWANFrame` ainsi que les fenêtres
`RX1` et `RX2`. Les nœuds possèdent des compteurs de trames et les passerelles
peuvent mettre en file d'attente des downlinks via `NetworkServer.send_downlink`.

Depuis cette version, la gestion ADR suit la spécification LoRaWAN : en plus des
commandes `LinkADRReq`/`LinkADRAns`, les bits `ADRACKReq` et `ADR` sont pris en
charge, le `ChMask` et le `NbTrans` influencent réellement les transmissions,
le compteur `adr_ack_cnt` respecte le délai `ADR_ACK_DELAY`, est remis à zéro
à chaque downlink et le serveur répond automatiquement lorsqu'un équipement
sollicite `ADRACKReq`. Cette
implémentation est complète et directement inspirée du modèle FLoRa,
adaptée ici sous une forme plus légère sans OMNeT++.

Lancer l'exemple minimal :

```bash
python run.py --lorawan-demo
```

Le tableau de bord inclut désormais un sélecteur **Classe LoRaWAN** permettant de choisir entre les modes A, B ou C pour l'ensemble des nœuds, ainsi qu'un champ **Taille payload (o)** afin de définir la longueur utilisée pour calculer l'airtime. Ces réglages facilitent la reproduction fidèle des scénarios FLoRa.

## Différences par rapport à FLoRa

Cette réécriture en Python reprend la majorité des concepts du modèle OMNeT++
mais simplifie volontairement certains aspects.

**Fonctionnalités entièrement prises en charge**
- respect du duty cycle, effet capture et interférence cumulative
- transmissions multi-canaux et distribution configurable
- mobilité des nœuds avec trajectoires lissées
- consommation d'énergie basée sur le profil FLoRa
- plans de fréquences régionaux prédéfinis (EU868, US915, AU915, AS923, IN865, KR920)
- profils d'énergie personnalisables
- commandes ADR (`LinkADRReq/Ans`, `ADRACKReq`, masque de canaux, `NbTrans`)
- procédure OTAA et file de downlinks programmés
- chiffrement AES-128 avec MIC pour tous les messages
- gestion complète des classes LoRaWAN B et C avec perte de beacon et dérive d'horloge optionnelles

**Fonctionnalités absentes**
- interface graphique OMNeT++ et couche physique détaillée

### Écarts connus avec FLoRa
- le canal radio est désormais plus complet (multipath, interférences
  cumulées et sensibilité par SF calculée automatiquement) mais certains
  paramètres restent approximés
- les calculs détaillés de puissance reçue avec antennes directionnelles et
  l'influence des états TX/RX/IDLE de la radio ne sont pas encore modélisés
- les temporisations et la file d'événements sont maintenant alignées sur
  FLoRa pour un PDR et des délais comparables à ±1 %
- la sensibilité et le bruit thermiques sont maintenant calculés à partir du
  bruit de fond théorique et du facteur de bruit, ce qui se rapproche des
  valeurs des modems Semtech

Le simulateur gère désormais l'ensemble des commandes MAC de LoRaWAN : réglage
des paramètres ADR, réinitialisation de clés, rejoins et changement de classe.

Pour des résultats plus proches du terrain, activez `fast_fading_std` et
`multipath_taps` pour simuler un canal multipath. Utilisez également
`interference_dB` pour introduire un bruit extérieur constant ou variable.

### Effet de capture

Le canal `Channel` applique par défaut un seuil de capture de **6 dB** : un
signal plus fort peut être décodé en présence d'interférences s'il dépasse le
plus faible d'au moins 6 dB et si ce signal domine pendant **cinq symboles de
preambule** au minimum. Lorsque `phy_model` vaut `"flora"`, `"flora_full"` ou `"flora_cpp"`, la
décision reprend la matrice `nonOrthDelta` du simulateur FLoRa original ; la
différence de puissance exigée dépend alors des Spreading Factors en présence.

Pour reproduire un scénario FLoRa :
1. Passez `flora_mode=True` et `flora_timing=True` lors de la création du
   `Simulator` (ou activez **Mode FLoRa complet**). Le canal radio utilise alors
   le modèle log-normal de FLoRa avec un fading Rayleigh léger
   (`multipath_taps=3`), un seuil de détection fixé à `-110 dBm` et une fenêtre
   d'interférence minimale de `5 s`. Le délai réseau est également de 10 ms avec
   un traitement serveur de 1,2 s comme dans OMNeT++.
2. Appliquez l'algorithme ADR1 via `from simulateur_lora_sfrd.launcher.adr_standard_1 import apply as adr1` puis `adr1(sim, disable_channel_impairments=False)`.
   Cette fonction reprend la logique du serveur FLoRa original.
3. Spécifiez `adr_method="avg"` lors de la création du `Simulator` (ou sur
   `sim.network_server`) pour utiliser la moyenne des 20 derniers SNR.
4. Fournissez le chemin du fichier INI à `Simulator(config_file=...)` ou
   saisissez les coordonnées manuellement via **Positions manuelles**.
5. Renseignez **Graine** pour conserver exactement le même placement et la même
   séquence d'intervalles d'une exécution à l'autre.
6. Ou lancez `python examples/run_flora_example.py` qui combine ces réglages.

### Compilation de FLoRa (OMNeT++)

Le dossier `flora-master` contient la version originale du simulateur FLoRa.
Après avoir installé OMNeT++ et cloné le framework INET 4.4 à la racine du
projet :

```bash
git clone https://github.com/inet-framework/inet.git -b v4.4 inet4.4
cd inet4.4 && make makefiles && make -j$(nproc)
```

Compilez ensuite FLoRa :

```bash
cd ../flora-master
make makefiles
make -j$(nproc)
```

Pour interfacer le simulateur Python avec la couche physique C++ et calculer la
 BER exacte via ``ctypes``, la bibliothèque partagée ``libflora_phy.so`` est
 désormais compilée automatiquement lors de l'installation (`pip install -e .` ou `pip install -e .[dev]`).
Si elle est absente, ``FloraPHY`` bascule automatiquement sur une implémentation
Python (plus lente mais fonctionnelle) et émet un avertissement.  Vous pouvez
toujours lancer manuellement `./scripts/build_flora_cpp.sh` depuis la racine du
dépôt pour régénérer la bibliothèque ; le fichier généré est détecté
automatiquement par ``FloraPHY``.

Placez ce fichier à la racine du projet ou dans ``flora-master`` puis lancez le
simulateur avec ``phy_model="flora_cpp"`` pour utiliser ces routines natives.

Exécutez enfin le scénario d'exemple pour générer un fichier `.sca` dans
`flora-master/results` :

```bash
./src/run_flora -u Cmdenv simulations/examples/n100-gw1.ini
```

## Format du fichier CSV

L'option `--output` de `run.py` permet d'enregistrer les métriques de la
simulation dans un fichier CSV. Ce dernier contient l'en‑tête suivant :

```
nodes,gateways,channels,mode,interval,steps,delivered,collisions,PDR(%),energy,avg_delay,throughput_bps
```

* **nodes** : nombre de nœuds simulés.
* **gateways** : nombre de passerelles.
* **channels** : nombre de canaux radio simulés.
* **mode** : `Random` ou `Periodic`.
* **interval** : intervalle moyen/fixe entre deux transmissions.
* **steps** : nombre de pas de temps simulés.
* **delivered** : paquets reçus par au moins une passerelle.
* **collisions** : paquets perdus par collision.
* **PDR(%)** : taux de livraison en pourcentage.
* **energy** : énergie totale consommée (unités arbitraires).
* **avg_delay** : délai moyen des paquets livrés.
* **throughput_bps** : débit binaire moyen des paquets délivrés.

## Exemple d'analyse

Un script Python d'exemple nommé `analyse_resultats.py` est disponible dans le
dossier `examples`. Il agrège plusieurs fichiers CSV et trace le PDR en fonction
du nombre de nœuds :

```bash
python examples/analyse_resultats.py resultats1.csv resultats2.csv
```

Le script affiche le PDR moyen puis sauvegarde un graphique dans
`pdr_par_nodes.png`.

Si le même fichier CSV contient plusieurs runs produits avec le dashboard ou
`run.py --runs`, le script `analyse_runs.py` permet d'obtenir les moyennes par
run :

```bash
python examples/analyse_runs.py résultats.csv
```

Deux autres utilitaires exploitent les fichiers `metrics_*.csv` exportés par le
tableau de bord :

```bash
python examples/plot_sf_distribution.py metrics1.csv metrics2.csv
python examples/plot_energy.py metrics.csv            # énergie totale
python examples/plot_energy.py --per-node metrics.csv # par nœud
```

`plot_sf_distribution.py` génère `sf_distribution.png` alors que
`plot_energy.py` crée `energy_total.png` ou `energy_per_node.png`.

## Calcul de l'airtime

La durée d'un paquet LoRa est obtenue à partir de la formule théorique :

```
T_sym = 2**SF / BW
T_preamble = (preamble_symbols + 4.25) * T_sym
N_payload = 8 + max(ceil((8*payload_size - 4*SF + 28 + 16) / (4*(SF - 2*DE))), 0)
           * (coding_rate + 4)
T_payload = N_payload * T_sym
airtime = T_preamble + T_payload
```

Chaque entrée de `events_log` comporte `start_time` et `end_time` ; leur
différence représente l'airtime réel du paquet.

```python
from simulateur_lora_sfrd.launcher.channel import Channel
ch = Channel()
temps = ch.airtime(sf=7, payload_size=20)
```


## Nettoyage des résultats

Le script `launcher/clean_results.py` supprime les doublons et les valeurs
manquantes d'un fichier CSV, puis sauvegarde `<fichier>_clean.csv` :

```bash
python launcher/clean_results.py résultats.csv
```

## Validation des résultats

L'exécution de `pytest` permet de vérifier la cohérence des calculs de RSSI et le traitement des collisions :

```bash
pytest -q
```

Un test dédié compare également les résultats du simulateur Python avec ceux du
FLoRa original lorsqu'un fichier `.sca` est disponible :

```bash
pytest tests/test_flora_sca.py -q
```

Vous pouvez aussi comparer les métriques générées avec les formules théoriques détaillées dans `tests/test_simulator.py`.

### Distribution des intervalles

`timeToFirstPacket` et les inter-arrivals suivent la loi `Exp(1/µ_SFRD)`. Les tests `tests/test_interval_distribution.py` vérifient que la moyenne reste dans une tolérance de ±2 %, que le coefficient de variation est proche de 1 et que la p‑value du test de Kolmogorov–Smirnov dépasse 0,05. Le duty cycle et la gestion des collisions ne modifient pas cette distribution : seules les transmissions effectives sont retardées, comme le montrent `tests/test_poisson_independence.py`.

Pour suivre les évolutions du projet, consultez le fichier `CHANGELOG.md`.

Ce projet est distribué sous licence [MIT](LICENSE).

## Exemples complets

Plusieurs scripts sont fournis dans le dossier `examples` pour illustrer
l'utilisation du simulateur :

```bash
python examples/run_basic.py          # simulation rapide avec 20 nœuds
python examples/run_basic.py --dump-intervals  # exporte les intervalles
python examples/run_flora_example.py  # reproduction d'un scénario FLoRa
```

L'option `--dump-intervals` active `dump_interval_logs` : un fichier Parquet est
généré pour chaque nœud avec la date Poisson attendue et l'instant réel de
transmission. Ces traces permettent de vérifier empiriquement la distribution
des arrivées.

Les utilitaires `analyse_resultats.py` et `analyse_runs.py` aident à traiter les
fichiers CSV produits par `run.py` ou par le tableau de bord.

## Guide d'extension du dashboard

Le fichier [docs/extension_guide.md](docs/extension_guide.md) détaille comment
ajouter des options au tableau de bord et intégrer vos propres modules. Ce guide
vise à faciliter les contributions extérieures.

## Améliorations possibles

Les points suivants ont été intégrés au simulateur :

- **PDR par nœud et par type de trafic.** Chaque nœud maintient l'historique de ses vingt dernières transmissions afin de calculer un taux de livraison global et récent. Ces valeurs sont visibles dans le tableau de bord et exportées dans un fichier `metrics_*.csv`.
- **Historique glissant et indicateurs QoS.** Le simulateur maintient un historique des transmissions pour calculer divers indicateurs de qualité de service.
- **Indicateurs supplémentaires.** La méthode `get_metrics()` retourne le PDR par SF, passerelle, classe et nœud. Le tableau de bord affiche un récapitulatif et l'export produit deux fichiers CSV : un pour les événements détaillés et un pour les métriques agrégées.
 - **Moteur d'événements précis.** La file de priorité gère désormais un délai réseau de 10 ms et un traitement serveur de 1,2 s, reproduisant ainsi fidèlement l'ordonnancement d'OMNeT++.
- **Suivi détaillé des ACK.** Chaque nœud mémorise les confirmations reçues pour appliquer fidèlement la logique ADR de FLoRa.
- **Scheduler de downlinks prioritaire.** Le module `downlink_scheduler.py` organise les transmissions B/C en donnant la priorité aux commandes et accusés de réception.

## Limites actuelles

Le simulateur reste volontairement léger et certaines fonctionnalités manquent
encore de maturité :

- La couche physique est simplifiée et n'imite pas parfaitement les comportements
  réels des modems LoRa.
- La mobilité par défaut s'appuie sur des trajets de Bézier. Un modèle RandomWaypoint et son planificateur A* permettent d'éviter relief et obstacles 3D.
- La sécurité LoRaWAN s'appuie désormais sur un chiffrement AES-128 complet et la validation du MIC. Le serveur de jointure gère l'ensemble de la procédure OTAA.

Les contributions sont les bienvenues pour lever ces limitations ou proposer de
nouvelles idées.

