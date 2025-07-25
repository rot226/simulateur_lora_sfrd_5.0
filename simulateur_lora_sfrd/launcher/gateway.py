import logging
import math

logger = logging.getLogger(__name__)
diag_logger = logging.getLogger("diagnostics")

class Gateway:
    """Représente une passerelle LoRa recevant les paquets des nœuds."""

    def __init__(
        self,
        gateway_id: int,
        x: float,
        y: float,
        altitude: float = 0.0,
        *,
        rx_gain_dB: float = 0.0,
    ):
        """
        Initialise une passerelle LoRa.

        ``rx_gain_dB`` correspond au gain d'antenne supplémentaire appliqué
        au signal reçu.

        :param gateway_id: Identifiant de la passerelle.
        :param x: Position X (mètres).
        :param y: Position Y (mètres).
        :param altitude: Altitude de l'antenne (mètres).
        :param rx_gain_dB: Gain d’antenne additionnel (dB).
        """
        self.id = gateway_id
        self.x = x
        self.y = y
        self.altitude = altitude
        self.rx_gain_dB = rx_gain_dB
        # Transmissions en cours indexées par (sf, frequency)
        self.active_map: dict[tuple[int, float], list[dict]] = {}
        # Mapping event_id -> (key, dict) for quick removal
        self.active_by_event: dict[int, tuple[tuple[int, float], dict]] = {}
        # Downlink frames waiting for the corresponding node receive windows
        self.downlink_buffer: dict[int, list] = {}

    def start_reception(
        self,
        event_id: int,
        node_id: int,
        sf: int,
        rssi: float,
        end_time: float,
        capture_threshold: float,
        current_time: float,
        frequency: float,
        min_interference_time: float = 0.0,
        *,
        freq_offset: float = 0.0,
        sync_offset: float = 0.0,
        bandwidth: float = 125e3,
        noise_floor: float | None = None,
        capture_mode: str = "basic",
        flora_phy=None,
        orthogonal_sf: bool = True,
    ):
        """
        Tente de démarrer la réception d'une nouvelle transmission sur cette passerelle.
        Gère les collisions et le capture effect.
        :param event_id: Identifiant de l'événement de transmission du nœud.
        :param node_id: Identifiant du nœud émetteur.
        :param sf: Spreading Factor de la transmission.
        :param rssi: Puissance du signal reçu (RSSI) en dBm.
        :param end_time: Temps (simulation) auquel la transmission se termine.
        :param capture_threshold: Seuil de capture en dB pour considérer qu'un signal plus fort peut être décodé malgré les interférences.
        :param frequency: Fréquence radio de la transmission (Hz).
        :param min_interference_time: Durée d'interférence tolérée (s). Les
            transmissions qui ne se chevauchent pas plus longtemps que cette
            valeur ne sont pas considérées comme en collision.
        :param noise_floor: Niveau de bruit pour le calcul du SNR (mode avancé).
        :param capture_mode: "basic" pour l'ancien comportement, "advanced" pour
            un calcul basé sur le SNR.
        :param flora_phy: Instance ``FloraPHY`` lorsque ``capture_mode`` vaut
            "flora".
        :param orthogonal_sf: Si ``True``, les transmissions de SF différents
            sont ignorées pour la détection de collision.
        """
        key = (sf, frequency)
        symbol_duration = (2 ** sf) / bandwidth
        # Gather all active transmissions that share the same frequency. When
        # ``orthogonal_sf`` is ``True`` we only consider the same SF. Otherwise
        # we must look across all SFs on this frequency.
        if orthogonal_sf:
            candidates = self.active_map.get(key, [])
        else:
            candidates = []
            for (sf_k, freq_k), txs in self.active_map.items():
                if freq_k == frequency:
                    candidates.extend(txs)
        concurrent_transmissions = [t for t in candidates if t['end_time'] > current_time]

        # Filtrer les transmissions dont le chevauchement est significatif
        interfering_transmissions = []
        for t in concurrent_transmissions:
            if orthogonal_sf and t.get('sf') != sf:
                continue
            overlap = min(t['end_time'], end_time) - current_time
            if overlap > min_interference_time:
                interfering_transmissions.append(t)

        # Liste des transmissions en collision potentielles (y compris la nouvelle)
        colliders = interfering_transmissions.copy()
        # Ajouter la nouvelle transmission elle-même
        new_transmission = {
            'event_id': event_id,
            'node_id': node_id,
            'sf': sf,
            'frequency': frequency,
            'rssi': rssi,
            'end_time': end_time,
            'start_time': current_time,
            'freq_offset': freq_offset,
            'sync_offset': sync_offset,
            'bandwidth': bandwidth,
            'symbol_duration': symbol_duration,
            'lost_flag': False,
        }
        colliders.append(new_transmission)

        if not interfering_transmissions:
            # Aucun paquet actif (ou chevauchement inférieur au seuil)
            self.active_map.setdefault(key, []).append(new_transmission)
            self.active_by_event[event_id] = (key, new_transmission)
            logger.debug(
                f"Gateway {self.id}: new transmission {event_id} from node {node_id} "
                f"(SF{sf}, {frequency/1e6:.3f} MHz) started, RSSI={rssi:.1f} dBm."
            )
            return

        # Sinon, on a une collision potentielle: déterminer le capture effect
        # Tri décroissant selon la puissance ou le SNR
        def _penalty(tx1, tx2):
            freq_diff = tx1.get('freq_offset', 0.0) - tx2.get('freq_offset', 0.0)
            time_diff = (tx1.get('start_time', 0.0) + tx1.get('sync_offset', 0.0)) - (
                tx2.get('start_time', 0.0) + tx2.get('sync_offset', 0.0)
            )
            bw = tx1.get('bandwidth', bandwidth)
            freq_factor = abs(freq_diff) / (bw / 2.0)
            symbol_time = (2 ** tx1.get('sf', sf)) / bw
            time_factor = abs(time_diff) / symbol_time
            if freq_factor >= 1.0 and time_factor >= 1.0:
                return float('inf')
            return 10 * math.log10(1.0 + freq_factor ** 2 + time_factor ** 2)

        def _enough_preamble(winner, others) -> bool:
            """Return ``True`` if ``winner`` may capture according to the
            5-symbol preamble rule."""
            sym_time = (2 ** winner.get('sf', sf)) / bandwidth
            limit = 5 * sym_time
            for other in others:
                if other is winner:
                    continue
                dt = other['start_time'] - winner['start_time']
                if dt < 0:
                    # another transmission started before the winner
                    return False
                if dt < limit:
                    return False
            return True

        if capture_mode in {"advanced", "omnet"} and noise_floor is not None:
            def _snr(i: int) -> float:
                rssi_i = colliders[i]['rssi']
                total = 10 ** (noise_floor / 10)
                for j, other in enumerate(colliders):
                    if j == i:
                        continue
                    pen = _penalty(colliders[i], other)
                    if pen == float('inf'):
                        continue
                    total += 10 ** ((other['rssi'] - pen) / 10)
                return rssi_i - 10 * math.log10(total)

            snrs = [ _snr(i) for i in range(len(colliders)) ]
            indices = sorted(range(len(colliders)), key=lambda i: snrs[i], reverse=True)
            strongest = colliders[indices[0]]
            strongest_metric = snrs[indices[0]]
            second = None
            for idx in indices[1:]:
                metric = snrs[idx]
                if second is None or metric > second:
                    second = metric
        elif capture_mode == "flora" and flora_phy is not None:
            colliders.sort(key=lambda t: t['rssi'], reverse=True)
            sf_list = [t['sf'] for t in colliders]
            rssi_list = [t['rssi'] for t in colliders]
            start_list = [t['start_time'] for t in colliders]
            end_list = [t['end_time'] for t in colliders]
            freq_list = [t['frequency'] for t in colliders]
            winners = flora_phy.capture(rssi_list, sf_list, start_list, end_list, freq_list)
            capture = any(winners)
            if capture:
                win_idx = winners.index(True)
                strongest = colliders[win_idx]
            else:
                strongest = colliders[0]
            second = None
        else:
            colliders.sort(key=lambda t: t['rssi'], reverse=True)
            strongest = colliders[0]
            strongest_metric = strongest['rssi']
            second = None
            for t in colliders[1:]:
                metric = t['rssi'] - _penalty(strongest, t)
                if second is None or metric > second:
                    second = metric
        if capture_mode != "flora":
            capture = False
            if second is not None:
                if (
                    strongest_metric - second >= capture_threshold
                    and _enough_preamble(strongest, colliders)
                ):
                    capture = True
            else:
                capture = True

        if capture:
            # Apply 5-symbol rule: the winning packet must have
            # started at least 5 symbols before the new one.
            capture_allowed = False
            if strongest is not new_transmission:
                elapsed = current_time - strongest.get('start_time', current_time)
                if elapsed >= 5 * symbol_duration:
                    capture_allowed = True
            if not capture_allowed:
                capture = False

        if capture:
            # Le signal le plus fort sera décodé, les autres sont perdus
            for t in colliders:
                if t is strongest:
                    t['lost_flag'] = False  # gagnant
                else:
                    t['lost_flag'] = True   # perdants
            # Retirer toutes les transmissions concurrentes actives qui sont perdantes
            for t in interfering_transmissions:
                if t['lost_flag']:
                    t_key = (t['sf'], t['frequency'])
                    try:
                        self.active_map[t_key].remove(t)
                        self.active_by_event.pop(t['event_id'], None)
                    except (ValueError, KeyError):
                        pass
            # Ajouter la transmission la plus forte si c'est la nouvelle (sinon elle est déjà dans active_transmissions)
            if strongest is new_transmission:
                new_transmission['lost_flag'] = False
                self.active_map.setdefault(key, []).append(new_transmission)
                self.active_by_event[event_id] = (key, new_transmission)
            # Sinon, la nouvelle transmission est perdue (on ne l'ajoute pas)
            logger.debug(
                f"Gateway {self.id}: collision avec capture – paquet {strongest['event_id']} capturé, autres perdus.")
            diag_logger.info(
                f"t={current_time:.2f} gw={self.id} capture winner={strongest['event_id']} "
                f"losers={[t['event_id'] for t in colliders if t is not strongest]}"
            )
        else:
            # Aucun signal ne peut être décodé (collision totale)
            for t in colliders:
                t['lost_flag'] = True
            # Retirer tous les paquets concurrents actifs (ils ne seront pas décodés finalement)
            for t in interfering_transmissions:
                t_key = (t['sf'], t['frequency'])
                try:
                    self.active_map[t_key].remove(t)
                    self.active_by_event.pop(t['event_id'], None)
                except (ValueError, KeyError):
                    pass
            # Ne pas ajouter la nouvelle transmission car tout est perdu (pas de décodage possible)
            logger.debug(
                f"Gateway {self.id}: collision sans capture – toutes les transmissions en collision sont perdues.")
            diag_logger.info(
                f"t={current_time:.2f} gw={self.id} collision={[t['event_id'] for t in colliders]} none"
            )
            # **Simplification** : après une collision totale, on considère le canal libre (les signaux brouillés ne sont pas conservés).
            return

    def end_reception(self, event_id: int, network_server, node_id: int):
        """
        Termine la réception d'une transmission sur cette passerelle si elle est active.
        Cette méthode est appelée lorsque l'heure de fin d'une transmission est atteinte.
        Elle supprime la transmission de la liste active et notifie le serveur réseau en cas de succès.
        :param event_id: Identifiant de l'événement de transmission terminé.
        :param network_server: L'objet NetworkServer pour notifier la réception d'un paquet décodé.
        :param node_id: Identifiant du nœud ayant transmis.
        """
        key, t = self.active_by_event.pop(event_id, (None, None))
        if t is not None and key is not None:
            try:
                self.active_map[key].remove(t)
            except (ValueError, KeyError):
                pass
            if not t['lost_flag']:
                network_server.schedule_receive(
                    event_id, node_id, self.id, t['rssi'], at_time=t['end_time']
                )
                logger.debug(
                    f"Gateway {self.id}: successfully received event {event_id} from node {node_id}."
                )
            else:
                logger.debug(
                    f"Gateway {self.id}: event {event_id} from node {node_id} was lost and not received."
                )

    # ------------------------------------------------------------------
    # Downlink handling
    # ------------------------------------------------------------------
    def buffer_downlink(self, node_id: int, frame):
        """Store a downlink frame for a node until its RX window."""
        self.downlink_buffer.setdefault(node_id, []).append(frame)

    def pop_downlink(self, node_id: int):
        """Retrieve the next pending downlink for a node."""
        queue = self.downlink_buffer.get(node_id)
        if queue:
            return queue.pop(0)
        return None

    def __repr__(self):
        return f"Gateway(id={self.id}, pos=({self.x:.1f},{self.y:.1f}))"
