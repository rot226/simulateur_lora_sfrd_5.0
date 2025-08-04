from __future__ import annotations

import math
import json
import os
import re
import numpy as np
from .omnet_model import OmnetModel


class _CorrelatedValue:
    """Correlated random walk used for optional impairments."""

    def __init__(
        self,
        mean: float,
        std: float,
        correlation: float,
        rng: np.random.Generator | None = None,
    ) -> None:
        self.mean = mean
        self.std = std
        self.corr = correlation
        self.value = mean
        self.rng = rng or np.random.Generator(np.random.MT19937())

    def sample(self) -> float:
        self.value = self.corr * self.value + (1.0 - self.corr) * self.mean
        if self.std > 0.0:
            self.value += self.rng.normal(0.0, self.std)
        return self.value

class Channel:
    """Représente le canal de propagation radio pour LoRa."""

    ENV_PRESETS = {
        "urban": (2.08, 3.57, 127.41, 40.0),
        "suburban": (2.32, 7.08, 128.95, 1000.0),
        "rural": (2.0, 2.0, 113.0, 1.0),
        # Parameters matching the FLoRa log-normal shadowing model
        "flora": (2.7, 3.57, 127.41, 40.0),
        "flora_oulu": (2.32, 7.8, 128.95, 1000.0),
        "flora_hata": (2.08, 3.57, 127.5, 40.0),
        # Additional presets for denser or indoor environments
        "urban_dense": (3.0, 8.0, 127.41, 40.0),
        "indoor": (3.5, 7.0, 127.41, 40.0),
    }

    # Preset frequency plans for common regions
    REGION_CHANNELS: dict[str, list[float]] = {
        "EU868": [868.1e6, 868.3e6, 868.5e6],
        "US915": [902.3e6 + 200e3 * i for i in range(8)],
        "AU915": [915.2e6 + 200e3 * i for i in range(8)],
        # Additional presets for Asian regions
        "AS923": [923.2e6, 923.4e6, 923.6e6],
        "IN865": [865.1e6, 865.3e6, 865.5e6],
        "KR920": [920.9e6, 921.1e6, 921.3e6],
    }

    """Path to default noise table matching FLoRa thresholds."""
    DEFAULT_FLORA_NOISE_JSON = os.path.join(
        os.path.dirname(__file__), "flora_noise_table.json"
    )

    @staticmethod
    def parse_flora_noise_table(path: str | os.PathLike) -> dict[int, dict[int, float]]:
        """Parse a FLoRa noise table from JSON or LoRaAnalogModel.cc."""
        path = os.fspath(path)
        if path.endswith(".json"):
            data = json.loads(open(path, "r", encoding="utf-8").read())
            return {
                int(sf): {int(bw): val for bw, val in tbl.items()}
                for sf, tbl in data.items()
            }
        text = open(path, "r", encoding="utf-8").read()
        table: dict[int, dict[int, float]] = {}
        current_sf: int | None = None
        for line in text.splitlines():
            m_sf = re.search(r"getLoRaSF\(\) == (\d+)", line)
            if m_sf:
                current_sf = int(m_sf.group(1))
                table[current_sf] = {}
                continue
            if current_sf is not None:
                m_bw = re.search(
                    r"getLoRaBW\(\) == Hz\((\d+)\).*dBmW2mW\((-?\d+)\)",
                    line,
                )
                if m_bw:
                    bw = int(m_bw.group(1))
                    val = int(m_bw.group(2))
                    table[current_sf][bw] = val
        return table

    def __init__(
        self,
        frequency_hz: float = 868e6,
        path_loss_exp: float = 2.0,
        shadowing_std: float = 6.0,
        path_loss_d0: float | None = None,
        reference_distance: float = 1.0,
        fast_fading_std: float = 0.0,
        multipath_taps: int = 1,
        cable_loss_dB: float = 0.0,
        tx_antenna_gain_dB: float = 0.0,
        rx_antenna_gain_dB: float = 0.0,
        time_variation_std: float = 0.0,
        receiver_noise_floor_dBm: float = -174.0,
        noise_figure_dB: float = 6.0,
        noise_floor_std: float = 0.0,
        # OMNeT++ inspired options
        fine_fading_std: float = 0.0,
        fading_correlation: float = 0.9,
        variable_noise_std: float = 0.0,
        advanced_capture: bool = False,
        flora_capture: bool = False,
        phy_model: str = "omnet",
        flora_loss_model: str = "lognorm",
        system_loss_dB: float = 0.0,
        rssi_offset_dB: float = 0.0,
        snr_offset_dB: float = 0.0,
        frequency_offset_hz: float = 0.0,
        freq_offset_std_hz: float = 0.0,
        sync_offset_s: float = 0.0,
        sync_offset_std_s: float = 0.0,
        dev_frequency_offset_hz: float = 0.0,
        dev_freq_offset_std_hz: float = 0.0,
        freq_drift_std_hz: float = 0.0,
        clock_drift_std_s: float = 0.0,
        clock_jitter_std_s: float = 0.0,
        temperature_K: float = 290.0,
        temperature_std_K: float = 0.0,
        phase_noise_std_dB: float = 0.0,
        pa_non_linearity_dB: float = -1.0,
        pa_non_linearity_std_dB: float = 0.5,
        humidity_percent: float = 50.0,
        humidity_std_percent: float = 0.0,
        humidity_noise_coeff_dB: float = 0.0,
        frontend_filter_order: int = 2,
        frontend_filter_bw: float | None = None,
        pa_ramp_up_s: float = 0.0,
        pa_ramp_down_s: float = 0.0,
        pa_ramp_current_a: float = 0.0,
        antenna_model: str | callable = "cos2",
        impulsive_noise_prob: float = 0.0,
        impulsive_noise_dB: float = 0.0,
        adjacent_interference_dB: float = 0.0,
        use_flora_curves: bool = False,
        tx_current_a: float = 0.0,
        rx_current_a: float = 0.0,
        idle_current_a: float = 0.0,
        voltage_v: float = 3.3,
        flora_noise_path: str | os.PathLike | None = None,
        sensitivity_mode: str = "flora",
        *,
        bandwidth: float = 125e3,
        coding_rate: int = 1,
        capture_threshold_dB: float = 6.0,
        capture_window_symbols: int = 5,
        tx_power_std: float = 0.0,
        interference_dB: float = 0.0,
        detection_threshold_dBm: float = -float("inf"),
        band_interference: list[tuple[float, float, float]] | None = None,
        environment: str | None = None,
        region: str | None = None,
        channel_index: int = 0,
        orthogonal_sf: bool = True,
        rng: np.random.Generator | None = None,
    ):
        """
        Initialise le canal radio avec paramètres de propagation.

        :param frequency_hz: Fréquence en Hz (par défaut 868 MHz).
        :param path_loss_exp: Exposant de perte de parcours (log-distance).
        :param shadowing_std: Écart-type du shadowing (variations aléatoires en dB), 0 pour ignorer.
        :param fast_fading_std: Variation rapide de l'amplitude (dB) pour simuler le fading multipath.
        :param multipath_taps: Nombre de trajets multipath additionnels simulés.
        :param cable_loss_dB: Pertes fixes dues au câble/connectique (dB).
        :param tx_antenna_gain_dB: Gain de l'antenne émettrice (dB).
        :param rx_antenna_gain_dB: Gain de l'antenne réceptrice (dB).
        :param time_variation_std: Écart-type d'une variation aléatoire
            appliquée au RSSI à chaque appel pour représenter un canal
            temporellement variable.
        :param receiver_noise_floor_dBm: Niveau de bruit thermique de référence (dBm/Hz).
        :param noise_figure_dB: Facteur de bruit ajouté par le récepteur (dB).
        :param noise_floor_std: Écart-type de la variation aléatoire du bruit
            (dB). Utile pour modéliser un canal plus dynamique.
        :param bandwidth: Largeur de bande LoRa (Hz).
        :param coding_rate: Index de code (0=4/5 … 4=4/8).
        :param capture_threshold_dB: Seuil de capture pour le décodage simultané.
        :param capture_window_symbols: Nombre de symboles de préambule requis
            avant qu'un paquet plus fort puisse capturer la réception (par
            défaut 5).
        :param tx_power_std: Écart-type de la variation aléatoire de puissance TX.
        :param interference_dB: Bruit supplémentaire moyen dû aux interférences.
        :param detection_threshold_dBm: RSSI minimal détectable (dBm). Les
            signaux plus faibles sont ignorés.
        :param band_interference: Liste optionnelle de tuples ``(freq, bw, dB)``
            décrivant des brouilleurs sélectifs. ``freq`` est la fréquence
            centrale en Hz, ``bw`` la largeur de bande et ``dB`` la puissance
            ajoutée au bruit lorsque le canal chevauche la bande.
        :param fine_fading_std: Écart-type du fading temporel fin.
        :param fading_correlation: Facteur de corrélation temporelle pour le
            fading et le bruit variable.
        :param variable_noise_std: Variation lente du bruit thermique en dB.
        :param advanced_capture: Active un mode de capture inspiré de FLoRa.
        :param flora_capture: Utilise la logique de collision FLoRa dans
            :class:`OmnetPHY`.
        :param phy_model: "omnet" (par défaut) pour utiliser le module OMNeT++.
            Le mode "omnet_full" reprend les équations complètes de
            ``LoRaAnalogModel`` afin de calculer RSSI et SNR avec les mêmes
            variations temporelles et la sélectivité de canal.
        :param flora_loss_model: Variante d'atténuation FLoRa à utiliser
            ("lognorm", "oulu" ou "hata").
        :param system_loss_dB: Pertes fixes supplémentaires (par ex. pertes
            système) appliquées à la perte de parcours.
        :param rssi_offset_dB: Décalage appliqué au RSSI calculé (dB).
        :param snr_offset_dB: Décalage appliqué au SNR calculé (dB).
        :param frequency_offset_hz: Désalignement fréquentiel moyen appliqué si
            aucun offset n'est fourni lors du calcul.
        :param sync_offset_s: Front d'attaque temporel moyen appliqué si aucun
            offset n'est fourni.
        :param freq_drift_std_hz: Écart-type de la dérive de fréquence simulée.
        :param clock_drift_std_s: Écart-type de la dérive d'horloge simulée.
        :param temperature_K: Température utilisée pour le calcul du bruit
            thermique.
        :param temperature_std_K: Variation de température pour moduler le
            bruit thermique.
        :param phase_noise_std_dB: Écart-type du bruit de phase appliqué au SNR.
        :param pa_non_linearity_dB: Décalage moyen dû à la non‑linéarité PA.
        :param pa_non_linearity_std_dB: Variation temporelle de cette
            non‑linéarité.
        :param humidity_percent: Humidité relative moyenne (0‑100 %).
        :param humidity_std_percent: Variation temporelle de l'humidité
            relative.
        :param humidity_noise_coeff_dB: Coefficient appliqué au pourcentage
            d'humidité pour moduler le bruit (dB).
        :param frontend_filter_order: Ordre du filtre passe‑bande modélisant
            la sélectivité de la chaîne RF. ``0`` pour désactiver.
        :param frontend_filter_bw: Largeur de bande du filtre (Hz). Par défaut,
            la même valeur que ``bandwidth``.
        :param pa_ramp_up_s: Temps de montée du PA simulé (s).
        :param pa_ramp_down_s: Temps de descente du PA (s).
        :param pa_ramp_current_a: Courant utilisé durant les rampes PA (A).
        :param antenna_model: Modèle d'antenne directionnelle à appliquer.
        :param impulsive_noise_prob: Probabilité d'ajouter du bruit impulsif à
            chaque calcul de bruit.
        :param impulsive_noise_dB: Amplitude du bruit impulsif ajouté (dB).
        :param adjacent_interference_dB: Pénalité appliquée aux brouilleurs sur
            un canal adjacent (dB).
        :param environment: Chaîne optionnelle pour charger un preset
            ("urban", "suburban" ou "rural").
        :param region: Nom d'un plan de fréquences prédéfini ("EU868", "US915",
            etc.). S'il est fourni, ``frequency_hz`` est ignoré et remplacé par
            la fréquence correspondante du canal ``channel_index``.
        :param channel_index: Index du canal à utiliser dans le plan de la
            région choisie.
        :param orthogonal_sf: Si ``True``, les transmissions de SF différents
            n'interfèrent pas entre elles.
        :param flora_noise_path: Chemin vers ``flora_noise_table.json`` ou vers
            ``LoRaAnalogModel.cc`` pour charger la table de bruit FLoRa.
        :param sensitivity_mode: "flora" pour utiliser les valeurs de bruit
            issues de FLoRa, "theoretical" pour un calcul thermique.
        """

        if environment is not None:
            env = environment.lower()
            if env not in self.ENV_PRESETS:
                raise ValueError(f"Unknown environment preset: {environment}")
            (
                path_loss_exp,
                shadowing_std,
                path_loss_d0,
                reference_distance,
            ) = self.ENV_PRESETS[env]
            self.environment = env
        else:
            self.environment = None

        if region is not None:
            reg = region.upper()
            if reg not in self.REGION_CHANNELS:
                raise ValueError(f"Unknown region preset: {region}")
            freqs = self.REGION_CHANNELS[reg]
            if channel_index < 0 or channel_index >= len(freqs):
                raise ValueError("channel_index out of range for region preset")
            frequency_hz = freqs[channel_index]
            self.region = reg
            self.channel_index = channel_index
        else:
            self.region = None
            self.channel_index = channel_index

        self.rng = rng or np.random.Generator(np.random.MT19937())
        self.frequency_hz = frequency_hz
        self.path_loss_exp = path_loss_exp
        self.shadowing_std = shadowing_std  # σ en dB (ex: 6.0 pour environnement urbain/suburbain)
        if path_loss_d0 is None:
            freq_mhz = self.frequency_hz / 1e6
            path_loss_d0 = 32.45 + 20 * math.log10(freq_mhz) - 60.0
        self.path_loss_d0 = path_loss_d0
        self.reference_distance = reference_distance
        self.fast_fading_std = fast_fading_std
        self.multipath_taps = int(multipath_taps)
        self.cable_loss_dB = cable_loss_dB
        self.tx_antenna_gain_dB = tx_antenna_gain_dB
        self.rx_antenna_gain_dB = rx_antenna_gain_dB
        self.time_variation_std = time_variation_std
        self.receiver_noise_floor_dBm = receiver_noise_floor_dBm
        self.noise_figure_dB = noise_figure_dB
        self.noise_floor_std = noise_floor_std
        self.tx_power_std = tx_power_std
        self.interference_dB = interference_dB
        self.band_interference = list(band_interference or [])
        self.detection_threshold_dBm = detection_threshold_dBm
        self.frequency_offset_hz = frequency_offset_hz
        self.freq_offset_std_hz = freq_offset_std_hz
        self.sync_offset_s = sync_offset_s
        self.sync_offset_std_s = sync_offset_std_s
        self.dev_frequency_offset_hz = dev_frequency_offset_hz
        self.dev_freq_offset_std_hz = dev_freq_offset_std_hz
        self.freq_drift_std_hz = freq_drift_std_hz
        self.clock_drift_std_s = clock_drift_std_s
        self.clock_jitter_std_s = clock_jitter_std_s
        self.temperature_K = temperature_K
        self.temperature_std_K = temperature_std_K
        self.phase_noise_std_dB = phase_noise_std_dB
        self.pa_non_linearity_dB = pa_non_linearity_dB
        self.pa_non_linearity_std_dB = pa_non_linearity_std_dB
        self.humidity_percent = humidity_percent
        self.humidity_std_percent = humidity_std_percent
        self.humidity_noise_coeff_dB = humidity_noise_coeff_dB
        self.frontend_filter_order = int(frontend_filter_order)
        self.frontend_filter_bw = float(frontend_filter_bw) if frontend_filter_bw is not None else bandwidth
        self.pa_ramp_up_s = float(pa_ramp_up_s)
        self.pa_ramp_down_s = float(pa_ramp_down_s)
        self.pa_ramp_current_a = float(pa_ramp_current_a)
        self.antenna_model = antenna_model
        self.impulsive_noise_prob = float(impulsive_noise_prob)
        self.impulsive_noise_dB = float(impulsive_noise_dB)
        self.adjacent_interference_dB = float(adjacent_interference_dB)
        self.use_flora_curves = use_flora_curves
        self.sensitivity_mode = sensitivity_mode
        self.tx_current_a = float(tx_current_a)
        self.rx_current_a = float(rx_current_a)
        self.idle_current_a = float(idle_current_a)
        self.voltage_v = float(voltage_v)
        if flora_noise_path is None:
            flora_noise_path = self.DEFAULT_FLORA_NOISE_JSON
        self.flora_noise_table = self.parse_flora_noise_table(flora_noise_path)
        self.omnet = OmnetModel(
            fine_fading_std,
            fading_correlation,
            variable_noise_std,
            freq_drift_std=freq_drift_std_hz,
            clock_drift_std=clock_drift_std_s,
            temperature_K=temperature_K,
        )
        self._temperature = _CorrelatedValue(
            temperature_K, temperature_std_K, fading_correlation, rng=self.rng
        )
        self._phase_noise = _CorrelatedValue(
            0.0, phase_noise_std_dB, fading_correlation, rng=self.rng
        )
        self._pa_nl = _CorrelatedValue(
            pa_non_linearity_dB, pa_non_linearity_std_dB, fading_correlation, rng=self.rng
        )
        self._humidity = _CorrelatedValue(
            humidity_percent, humidity_std_percent, fading_correlation, rng=self.rng
        )
        self._impulse = _CorrelatedValue(0.0, impulsive_noise_dB, fading_correlation, rng=self.rng)
        self.fine_fading_std = fine_fading_std
        self.fading_correlation = fading_correlation
        self.variable_noise_std = variable_noise_std
        self.advanced_capture = advanced_capture
        self.flora_capture = flora_capture
        self.phy_model = phy_model
        self.flora_loss_model = flora_loss_model
        self.system_loss_dB = system_loss_dB
        self.rssi_offset_dB = rssi_offset_dB
        self.snr_offset_dB = snr_offset_dB

        # Paramètres LoRa (BW 125 kHz, CR 4/5, préambule 8, CRC activé)
        self.bandwidth = bandwidth
        self.coding_rate = coding_rate
        self.preamble_symbols = 8
        # Low Data Rate Optimization activée au-delà de ce SF
        self.low_data_rate_threshold = 11  # SF >= 11 -> Low Data Rate Optimization activée

        self._update_sensitivity()
        # Seuil de capture (différence de RSSI en dB pour qu'un signal plus fort capture la réception)
        self.capture_threshold_dB = capture_threshold_dB
        self.capture_window_symbols = int(capture_window_symbols)
        self.orthogonal_sf = orthogonal_sf
        self.last_rssi_dBm = 0.0
        self.last_noise_dBm = 0.0
        self.last_filter_att_dB = 0.0

        if self.phy_model in ("omnet", "omnet_full"):
            from .omnet_phy import OmnetPHY
            self.omnet_phy = OmnetPHY(
                self,
                freq_offset_std_hz=self.freq_offset_std_hz,
                sync_offset_std_s=self.sync_offset_std_s,
                dev_frequency_offset_hz=dev_frequency_offset_hz,
                dev_freq_offset_std_hz=dev_freq_offset_std_hz,
                temperature_std_K=temperature_std_K,
                pa_non_linearity_dB=pa_non_linearity_dB,
                pa_non_linearity_std_dB=pa_non_linearity_std_dB,
                phase_noise_std_dB=phase_noise_std_dB,
                tx_start_delay_s=0.0,
                rx_start_delay_s=0.0,
                pa_ramp_up_s=pa_ramp_up_s,
                pa_ramp_down_s=pa_ramp_down_s,
                pa_ramp_current_a=self.pa_ramp_current_a,
                antenna_model=self.antenna_model,
                tx_current_a=self.tx_current_a,
                rx_current_a=self.rx_current_a,
                idle_current_a=self.idle_current_a,
                voltage_v=self.voltage_v,
                flora_capture=self.flora_capture,
                capture_window_symbols=self.capture_window_symbols,
            )
            self.flora_phy = None
            self.advanced_capture = True
        elif self.phy_model in ("flora", "flora_full") or self.use_flora_curves:
            from .flora_phy import FloraPHY
            self.flora_phy = FloraPHY(self, loss_model=self.flora_loss_model)
            self.omnet_phy = None
            self.advanced_capture = True
        elif self.phy_model == "flora_cpp":
            try:
                from .flora_cpp import FloraCppPHY
                self.flora_phy = FloraCppPHY()
            except Exception:
                from .flora_phy import FloraPHY
                self.flora_phy = FloraPHY(self, loss_model=self.flora_loss_model)
            self.omnet_phy = None
            self.advanced_capture = True
        else:
            self.omnet_phy = None
            self.flora_phy = None

    def noise_floor_dBm(self, freq_offset_hz: float = 0.0) -> float:
        """Retourne le niveau de bruit (dBm) pour la bande passante configurée.

        Le bruit peut varier autour de la valeur moyenne pour simuler un canal
        plus réaliste.
        """
        if self.omnet_phy:
            noise = self.omnet_phy.noise_floor()
            self.last_noise_dBm = noise
            return noise
        temp = self._temperature.sample()
        original = self.omnet.temperature_K
        self.omnet.temperature_K = temp
        eff_bw = min(self.bandwidth, self.frontend_filter_bw)
        thermal = self.omnet.variable_thermal_noise_dBm(eff_bw)
        self.omnet.temperature_K = original
        base = thermal + self.noise_figure_dB
        power = 10 ** (base / 10.0)
        if self.interference_dB != 0.0:
            power += 10 ** ((self.interference_dB - self._filter_attenuation_db(freq_offset_hz)) / 10.0)
        hum = self.humidity_noise_coeff_dB * (self._humidity.sample() / 100.0)
        if hum != 0.0:
            power += 10 ** ((base + hum) / 10.0) - 10 ** (base / 10.0)
        for f, bw, p in self.band_interference:
            half = (bw + self.bandwidth) / 2.0
            diff = abs(self.frequency_hz - f)
            if diff <= half:
                att = self._filter_attenuation_db(diff)
                power += 10 ** ((p - att) / 10.0)
            elif self.adjacent_interference_dB > 0 and diff <= half + self.bandwidth:
                val = max(p - self.adjacent_interference_dB, 0.0) - self._filter_attenuation_db(diff)
                power += 10 ** (val / 10.0)
        if self.noise_floor_std > 0:
            power *= 10 ** (self.rng.normal(0.0, self.noise_floor_std) / 10.0)
        if self.impulsive_noise_prob > 0.0:
            val = self._impulse.sample()
            if self.rng.random() < self.impulsive_noise_prob:
                power += 10 ** (val / 10.0)
        noise = 10 * math.log10(power)
        self.last_noise_dBm = noise
        return noise

    def path_loss(self, distance: float) -> float:
        """Calcule la perte de parcours (en dB) pour une distance donnée (m)."""
        if self.omnet_phy:
            return self.omnet_phy.path_loss(distance)
        if getattr(self, "flora_phy", None):
            return self.flora_phy.path_loss(distance)
        if distance <= 0:
            return 0.0
        d = max(distance, 1.0)
        pl = self.path_loss_d0 + 10 * self.path_loss_exp * math.log10(
            d / self.reference_distance
        )
        return pl + self.system_loss_dB

    def compute_rssi(
        self,
        tx_power_dBm: float,
        distance: float,
        sf: int | None = None,
        *,
        obstacle_loss_dB: float = 0.0,
        tx_pos: tuple[float, float] | tuple[float, float, float] | None = None,
        rx_pos: tuple[float, float] | tuple[float, float, float] | None = None,
        tx_angle: float | tuple[float, float] | None = None,
        rx_angle: float | tuple[float, float] | None = None,
        freq_offset_hz: float | None = None,
        sync_offset_s: float | None = None,
    ) -> tuple[float, float]:
        """Calcule le RSSI et le SNR attendus à une certaine distance.

        Un gain additionnel peut être appliqué si ``sf`` est renseigné pour
        représenter l'effet d'étalement de spectre LoRa. ``obstacle_loss_dB``
        permet d'appliquer une atténuation supplémentaire liée à l'environnement
        (bâtiments, relief, etc.).
        """
        if self.omnet_phy:
            return self.omnet_phy.compute_rssi(
                tx_power_dBm,
                distance,
                sf,
                obstacle_loss_dB=obstacle_loss_dB,
                tx_pos=tx_pos,
                rx_pos=rx_pos,
                tx_angle=tx_angle,
                rx_angle=rx_angle,
                freq_offset_hz=freq_offset_hz,
                sync_offset_s=sync_offset_s,
            )
        loss = self.path_loss(distance)
        if self.shadowing_std > 0 and not getattr(self, "flora_phy", None):
            loss += self.rng.normal(0, self.shadowing_std)

        tx_power_dBm += self._pa_nl.sample()
        # RSSI = P_tx + gains antennes - pertes - pertes câble
        rssi = (
            tx_power_dBm
            + self.tx_antenna_gain_dB
            + self.rx_antenna_gain_dB
            - loss
            - self.cable_loss_dB
        )
        if self.tx_power_std > 0:
            rssi += self.rng.normal(0, self.tx_power_std)
        if self.fast_fading_std > 0:
            rssi += self.rng.normal(0, self.fast_fading_std)
        if self.multipath_taps > 1:
            rssi += self._multipath_fading_db()
        if self.time_variation_std > 0:
            rssi += self.rng.normal(0, self.time_variation_std)
        rssi += self.omnet.fine_fading()
        if (
            tx_angle is not None
            and rx_angle is not None
            and tx_pos is not None
            and rx_pos is not None
        ):
            def _vec(pos1, pos2):
                dx = (pos2[0] - pos1[0])
                dy = (pos2[1] - pos1[1])
                dz1 = pos1[2] if len(pos1) >= 3 else 0.0
                dz2 = pos2[2] if len(pos2) >= 3 else 0.0
                dz = dz2 - dz1
                return dx, dy, dz

            dx, dy, dz = _vec(tx_pos, rx_pos)
            dist = math.sqrt(dx * dx + dy * dy + dz * dz)
            if dist > 0.0:
                los = (dx / dist, dy / dist, dz / dist)

                def _orient_vec(angle):
                    if isinstance(angle, (tuple, list)):
                        az, el = angle
                    else:
                        az = angle
                        el = 0.0
                    return (
                        math.cos(el) * math.cos(az),
                        math.cos(el) * math.sin(az),
                        math.sin(el),
                    )

                tx_vec = _orient_vec(tx_angle)
                rx_vec = _orient_vec(rx_angle)
                tx_dot = max(min(sum(a * b for a, b in zip(los, tx_vec)), 1.0), -1.0)
                rx_dot = max(min(sum(-a * b for a, b in zip(los, rx_vec)), 1.0), -1.0)
                tx_diff = math.acos(tx_dot)
                rx_diff = math.acos(rx_dot)
                rssi += self._directional_gain(tx_diff)
                rssi += self._directional_gain(rx_diff)
        rssi += self.rssi_offset_dB
        rssi -= obstacle_loss_dB
        if freq_offset_hz is None:
            freq_offset_hz = self.frequency_offset_hz
        freq_offset_hz += self.omnet.frequency_drift()
        if sync_offset_s is None:
            sync_offset_s = self.sync_offset_s
        sync_offset_s += self.omnet.clock_drift()
        if self.clock_jitter_std_s > 0.0:
            sync_offset_s += self.rng.normal(0.0, self.clock_jitter_std_s)

        attenuation = self._filter_attenuation_db(freq_offset_hz)
        rssi -= attenuation

        if self.phy_model == "flora_full" and sf is not None:
            noise = self._flora_noise_dBm(sf)
        elif self.phy_model == "omnet_full" and sf is not None:
            noise = self._omnet_noise_dBm(sf, freq_offset_hz)
        else:
            noise = self.noise_floor_dBm(freq_offset_hz)
        snr = rssi - noise + self.snr_offset_dB
        penalty = self._alignment_penalty_db(freq_offset_hz, sync_offset_s, sf)
        snr -= penalty
        snr -= abs(self._phase_noise.sample())
        if sf is not None:
            snr += 10 * math.log10(2 ** sf)
        self.last_rssi_dBm = rssi
        self.last_filter_att_dB = attenuation
        return rssi, snr

    def packet_error_rate(self, snr: float, sf: int, payload_bytes: int = 20) -> float:
        """Return PER based on the OMNeT++ BER model."""
        if getattr(self, "flora_phy", None) and self.use_flora_curves:
            return self.flora_phy.packet_error_rate(snr, sf, payload_bytes)

        from .omnet_modulation import calculate_ber

        bitrate = (
            sf
            * self.bandwidth
            * 4.0
            / ((1 << sf) * (self.coding_rate + 4))
        )
        snir = 10 ** (snr / 10.0)
        ber = calculate_ber(snir, self.bandwidth, bitrate)
        n_bits = payload_bytes * 8
        per = 1.0 - (1.0 - ber) ** n_bits
        return min(max(per, 0.0), 1.0)

    def _multipath_fading_db(self) -> float:
        """Return a fading value in dB based on multiple Rayleigh paths."""
        if self.multipath_taps <= 1:
            return 0.0
        i = sum(self.rng.normal(0.0, 1.0) for _ in range(self.multipath_taps))
        q = sum(self.rng.normal(0.0, 1.0) for _ in range(self.multipath_taps))
        amp = math.sqrt(i * i + q * q) / math.sqrt(self.multipath_taps)
        return 20 * math.log10(max(amp, 1e-12))

    def _filter_attenuation_db(self, freq_offset_hz: float) -> float:
        """Return attenuation due to the front-end filter."""
        if self.frontend_filter_order <= 0 or self.frontend_filter_bw <= 0:
            return 0.0
        fc = self.frontend_filter_bw / 2.0
        if fc <= 0.0:
            return 0.0
        ratio = abs(freq_offset_hz) / fc
        if ratio <= 0.0:
            return 0.0
        # |H(jw)|^2 = 1 / (1 + (w/wc)^(2n)) for an n-th order Butterworth filter
        # Attenuation in dB is -10 log10(|H|^2) = 10 log10(1 + ratio^(2n))
        return 10 * math.log10(1.0 + ratio ** (2 * self.frontend_filter_order))

    def _alignment_penalty_db(
        self, freq_offset_hz: float, sync_offset_s: float, sf: int | None
    ) -> float:
        """Return an SNR penalty due to imperfect alignment."""
        bw = self.bandwidth
        freq_factor = abs(freq_offset_hz) / (bw / 2.0)
        if sf is not None:
            symbol_time = (2 ** sf) / bw
        else:
            symbol_time = 1.0 / bw
        time_factor = abs(sync_offset_s) / symbol_time
        if freq_factor >= 1.0 and time_factor >= 1.0:
            return float("inf")
        penalty = 1.5 * (freq_factor ** 2 + time_factor ** 2)
        return 10 * math.log10(1.0 + penalty)

    def _directional_gain(self, angle_rad: float) -> float:
        """Return antenna gain for the given angle."""
        if callable(self.antenna_model):
            return float(self.antenna_model(angle_rad))
        model = str(self.antenna_model).lower()
        if model == "isotropic":
            return 0.0
        if model in ("cos", "cosine"):
            gain = max(math.cos(angle_rad), 0.0)
        else:  # default "cos2"
            gain = max(math.cos(angle_rad), 0.0) ** 2
        return 10 * math.log10(max(gain, 1e-3))

    def airtime(self, sf: int, payload_size: int = 20) -> float:
        """Calcule l'airtime complet d'un paquet LoRa en secondes."""
        # Durée d'un symbole
        rs = self.bandwidth / (2 ** sf)
        ts = 1.0 / rs
        de = 1 if sf >= self.low_data_rate_threshold else 0
        cr_denom = self.coding_rate + 4
        numerator = 8 * payload_size - 4 * sf + 28 + 16 - 20 * 0
        denominator = 4 * (sf - 2 * de)
        n_payload = max(math.ceil(numerator / denominator), 0) * cr_denom + 8
        t_preamble = (self.preamble_symbols + 4.25) * ts
        t_payload = n_payload * ts
        return t_preamble + t_payload

    # ------------------------------------------------------------------
    # Helpers for region frequency presets
    # ------------------------------------------------------------------

    @classmethod
    def register_region(cls, name: str, frequencies: list[float]) -> None:
        """Register a new region frequency plan."""
        cls.REGION_CHANNELS[name.upper()] = list(frequencies)

    @classmethod
    def region_channels(cls, region: str, **kwargs) -> list["Channel"]:
        """Return a list of ``Channel`` objects for the given region preset."""
        reg = region.upper()
        if reg not in cls.REGION_CHANNELS:
            raise ValueError(f"Unknown region preset: {region}")
        return [cls(frequency_hz=f, region=reg, channel_index=i, **kwargs)
                for i, f in enumerate(cls.REGION_CHANNELS[reg])]

    # ------------------------------------------------------------------
    # Sensitivity computation
    # ------------------------------------------------------------------

    SNR_THRESHOLDS = {7: -7.5, 8: -10.0, 9: -12.5, 10: -15.0, 11: -17.5, 12: -20.0}

    def _flora_noise_dBm(self, sf: int) -> float:
        return self.flora_noise_table.get(sf, {}).get(int(self.bandwidth), -126.5)

    def _omnet_noise_dBm(self, sf: int, freq_offset_hz: float = 0.0) -> float:
        """Return noise level similar to LoRaAnalogModel with variations."""
        base = self._flora_noise_dBm(sf)
        thermal = -174 + 10 * math.log10(self.bandwidth) + self.noise_figure_dB
        delta = self.noise_floor_dBm(freq_offset_hz) - thermal
        return base + delta


    def _update_sensitivity(self) -> None:
        if self.sensitivity_mode == "theoretical":
            bw = min(self.bandwidth, self.frontend_filter_bw)
            noise = -174 + 10 * math.log10(bw) + self.noise_figure_dB
            self.sensitivity_dBm = {
                sf: noise + snr for sf, snr in self.SNR_THRESHOLDS.items()
            }
        else:
            self.sensitivity_dBm = {
                sf: self._flora_noise_dBm(sf) for sf in self.flora_noise_table
            }
