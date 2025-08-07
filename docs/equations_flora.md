# Équations principales du simulateur

Ce document rassemble les formules de référence employées par le simulateur FLoRa.

## Perte de parcours

Le module `flora_phy.py` reproduit la perte de parcours de FLoRa :

```python
loss = PATH_LOSS_D0 + 10 * n * math.log10(distance / REFERENCE_DISTANCE)
```

avec `PATH_LOSS_D0 = 127.41` dB et `REFERENCE_DISTANCE = 40` m. L'exposant `n` vaut `2.7` pour le profil `flora`【F:README.md†L424-L433】【F:simulateur_lora_sfrd/launcher/flora_phy.py†L29-L61】.

## Taux d'erreur paquet (PER)

La probabilité d'erreur est approchée par une loi logistique :

```python
PER = 1 / (1 + math.exp(2 * (snr - (th + 2))))
```

> **Remarque :** cette loi logistique est une simplification des courbes PER de
> FLoRa. Le code C++ original intègre la fonction `calculateBER` pour un calcul
> par intégration. Pour des résultats plus fidèles, compilez
> `libflora_phy` (`.so` sous Linux, `.dll` sous Windows) et utilisez
> `phy_model="flora_cpp"`.

où `th` correspond au seuil SNR du spreading factor courant【F:README.md†L434-L441】【F:simulateur_lora_sfrd/launcher/flora_phy.py†L127-L130】.

## Calcul de l'airtime

La durée d'un paquet LoRa est obtenue à partir de :

```text
T_sym = 2**SF / BW
T_preamble = (preamble_symbols + 4.25) * T_sym
N_payload = 8 + max(ceil((8*payload_size - 4*SF + 28 + 16) / (4*(SF - 2*DE))), 0)
            * (coding_rate + 4)
T_payload = N_payload * T_sym
airtime = T_preamble + T_payload
```

Cette formule est utilisée par `Channel.airtime` pour renvoyer la durée en secondes :

```python
rs = bandwidth / (2 ** sf)
ts = 1.0 / rs
de = 1 if sf >= low_data_rate_threshold else 0
cr_denom = coding_rate + 4
numerator = 8 * payload_size - 4 * sf + 28 + 16 - 20 * 0
denominator = 4 * (sf - 2 * de)
n_payload = max(math.ceil(numerator / denominator), 0) * cr_denom + 8
t_preamble = (preamble_symbols + 4.25) * ts
t_payload = n_payload * ts
return t_preamble + t_payload
```
【F:README.md†L642-L661】【F:simulateur_lora_sfrd/launcher/channel.py†L558-L570】

## Modèle OMNeT++

Les équations de calcul du taux d'erreur binaire (BER) et symbolique (SER) proviennent de `omnet_modulation.py` :

```python
dsnr = 20.0 * snir * bandwidth / bitrate
# Somme combinatoire
dsumk = ...
return (8.0 / 15.0) * (1.0 / 16.0) * dsumk
```

```python
ber = calculate_ber(snir, bandwidth, bitrate)
ser = 1.0 - (1.0 - ber) ** 4
return min(max(ser, 0.0), 1.0)
```
【F:simulateur_lora_sfrd/launcher/omnet_modulation.py†L8-L35】

## Bruit de fond

Le bruit thermique moyen pour une bande passante ``BW`` (Hz) est calculé par :

```python
thermal = -174 + 10 * math.log10(BW) + noise_figure_dB  # dBm
```

Cette équation suppose une température de référence de 290 K et ajoute le
facteur de bruit du récepteur ``noise_figure_dB``【F:simulateur_lora_sfrd/launcher/omnet_model.py†L65-L69】【F:simulateur_lora_sfrd/launcher/channel.py†L448-L451】.

Pour reproduire exactement FLoRa, les sensibilités de chaque couple
spreading factor/largeur de bande sont chargées depuis la table Semtech
codée dans ``LoRaAnalogModel.cc``【F:flora-master/src/LoRaPhy/LoRaAnalogModel.cc†L36-L80】
et exposée via ``Channel._flora_noise_dBm``【F:simulateur_lora_sfrd/launcher/channel.py†L719-L726】.

| SF | 125 kHz | 250 kHz | 500 kHz |
|----|---------|---------|---------|
| 6  | −121 dBm | −118 dBm | −111 dBm |
| 7  | −124 dBm | −122 dBm | −116 dBm |
| 8  | −127 dBm | −125 dBm | −119 dBm |
| 9  | −130 dBm | −128 dBm | −122 dBm |
| 10 | −133 dBm | −130 dBm | −125 dBm |
| 11 | −135 dBm | −132 dBm | −128 dBm |
| 12 | −137 dBm | −135 dBm | −129 dBm |

> **Hypothèses :** valeurs données pour un récepteur idéal sans interférence
externe. Les unités sont en dBm.

## Effet de capture

Deux transmissions sur la même fréquence entrent en collision si elles se
chevauchent après ``capture_window_symbols`` symboles de préambule et que
la différence de puissance n'atteint pas le seuil ``NON_ORTH_DELTA`` (dB)
:

```python
diff = rssi0 - rssi_i  # dB
th = NON_ORTH_DELTA[sf0 - 7][sf_i - 7]  # dB
capture = diff >= th
```

La fenêtre critique commence à
``t_cs = start0 + (preamble_symbols - capture_window_symbols) * T_sym``
où ``T_sym = 2**sf0 / BW`` est le temps symbole en secondes. Si l'interférence
se poursuit au-delà de ``t_cs`` et que ``capture`` est faux, le paquet est
perdu【F:simulateur_lora_sfrd/launcher/flora_phy.py†L20-L26】【F:simulateur_lora_sfrd/launcher/flora_phy.py†L99-L125】【F:flora-master/src/LoRaPhy/LoRaReceiver.cc†L163-L185】.

> **Hypothèses :** les puissances sont exprimées en dBm. Seules les
transmissions sur la même fréquence sont considérées.

## Modèle énergétique

L'énergie consommée dans un état radio se calcule par
``E = V * I * t`` (Joules) où ``V`` est la tension d'alimentation (V), ``I`` le
courant de l'état (A) et ``t`` la durée (s). Par exemple, pour l'état
transmission :

```python
I_tx = profile.get_tx_current(tx_power)  # A
E_tx = V * I_tx * airtime
E_ramp = V * I_tx * (ramp_up_s + ramp_down_s)
```

Cette logique est appliquée par ``Node.add_energy`` et
``Node.consume_until`` pour accumuler l'énergie par état【F:simulateur_lora_sfrd/launcher/node.py†L378-L386】【F:simulateur_lora_sfrd/launcher/node.py†L449-L461】
et reflète le modèle OMNeT++ où l'énergie est l'intégrale de la puissance
instantanée【F:flora-master/src/LoRaEnergyModules/LoRaEnergyConsumer.cc†L153-L154】.

> **Hypothèses :** la tension est constante et les courants par état proviennent
du profil énergétique configuré.
