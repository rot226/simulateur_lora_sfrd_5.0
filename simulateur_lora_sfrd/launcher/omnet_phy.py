"""Simplified OMNeT++ physical layer helpers."""

from __future__ import annotations

import math
import random

from .omnet_model import OmnetModel


class _CorrelatedValue:
    """Simple correlated random walk."""

    def __init__(self, mean: float, std: float, correlation: float) -> None:
        self.mean = mean
        self.std = std
        self.corr = correlation
        self.value = mean

    def sample(self) -> float:
        self.value = self.corr * self.value + (1.0 - self.corr) * self.mean
        if self.std > 0.0:
            self.value += random.gauss(0.0, self.std)
        return self.value


class OmnetPHY:
    """Replicate OMNeT++ FLoRa PHY calculations with extra impairments."""

    NON_ORTH_DELTA = [
        [1, -8, -9, -9, -9, -9],
        [-11, 1, -11, -12, -13, -13],
        [-15, -13, 1, -13, -14, -15],
        [-19, -18, -17, 1, -17, -18],
        [-22, -22, -21, -20, 1, -20],
        [-25, -25, -25, -24, -23, 1],
    ]

    def __init__(
        self,
        channel,
        *,
        freq_offset_std_hz: float = 0.0,
        sync_offset_std_s: float = 0.0,
        dev_frequency_offset_hz: float = 0.0,
        dev_freq_offset_std_hz: float = 0.0,
        temperature_std_K: float = 0.0,
        pa_non_linearity_dB: float = -1.0,
        pa_non_linearity_std_dB: float = 0.5,
        phase_noise_std_dB: float = 0.0,
        clock_jitter_std_s: float = 0.0,
        phase_offset_rad: float = 0.0,
        phase_offset_std_rad: float = 0.0,
        oscillator_leakage_dB: float = 0.0,
        oscillator_leakage_std_dB: float = 0.0,
        rx_fault_std_dB: float = 0.0,
        flora_capture: bool = False,
        capture_window_symbols: int = 5,
        tx_start_delay_s: float = 0.0,
        rx_start_delay_s: float = 0.0,
        pa_ramp_up_s: float = 0.0,
        pa_ramp_down_s: float = 0.0,
        pa_ramp_current_a: float = 0.0,
        antenna_model: str | callable = "cos2",
        tx_current_a: float = 0.0,
        rx_current_a: float = 0.0,
        idle_current_a: float = 0.0,
        tx_start_current_a: float = 0.0,
        rx_start_current_a: float = 0.0,
        voltage_v: float = 3.3,
    ) -> None:
        """Initialise helper with optional hardware impairments.

        The ``tx_start_current_a`` and ``rx_start_current_a`` parameters model
        additional current draw during ``start_tx`` and ``start_rx`` delays.
        ``pa_ramp_current_a`` specifies the current drawn while the PA is
        ramping up or down. ``antenna_model`` selects the pattern used when
        applying orientation gains.
        """
        self.channel = channel
        self.model = OmnetModel(
            channel.fine_fading_std,
            channel.omnet.correlation,
            channel.omnet.noise_std,
            freq_drift_std=channel.omnet.freq_drift_std,
            clock_drift_std=channel.omnet.clock_drift_std,
            temperature_K=channel.omnet.temperature_K,
        )
        corr = channel.omnet.correlation
        self._freq_offset = _CorrelatedValue(
            channel.frequency_offset_hz,
            freq_offset_std_hz,
            corr,
        )
        self._sync_offset = _CorrelatedValue(
            channel.sync_offset_s,
            sync_offset_std_s,
            corr,
        )
        self._dev_freq = _CorrelatedValue(
            dev_frequency_offset_hz,
            dev_freq_offset_std_hz,
            corr,
        )
        self._temperature = _CorrelatedValue(
            channel.omnet.temperature_K,
            temperature_std_K,
            corr,
        )
        self._pa_nl = _CorrelatedValue(
            pa_non_linearity_dB,
            pa_non_linearity_std_dB,
            corr,
        )
        self._phase_noise = _CorrelatedValue(0.0, phase_noise_std_dB, corr)
        self._phase_offset = _CorrelatedValue(
            phase_offset_rad,
            phase_offset_std_rad,
            corr,
        )
        self._osc_leak = _CorrelatedValue(
            oscillator_leakage_dB,
            oscillator_leakage_std_dB,
            corr,
        )
        self._rx_fault = _CorrelatedValue(0.0, rx_fault_std_dB, corr)
        self.clock_jitter_std_s = clock_jitter_std_s
        self.receiver_noise_floor_dBm = channel.receiver_noise_floor_dBm
        self.tx_start_delay_s = float(tx_start_delay_s)
        self.rx_start_delay_s = float(rx_start_delay_s)
        self.pa_ramp_up_s = float(pa_ramp_up_s)
        self.pa_ramp_down_s = float(pa_ramp_down_s)
        self.pa_ramp_current_a = float(pa_ramp_current_a)
        self.antenna_model = antenna_model
        self.tx_current_a = float(tx_current_a)
        self.rx_current_a = float(rx_current_a)
        self.idle_current_a = float(idle_current_a)
        self.tx_start_current_a = float(tx_start_current_a)
        self.rx_start_current_a = float(rx_start_current_a)
        self.voltage_v = float(voltage_v)
        self.flora_capture = bool(flora_capture)
        self.capture_window_symbols = int(capture_window_symbols)
        self.tx_state = "on" if self.tx_start_delay_s == 0.0 else "off"
        self.rx_state = "on" if self.rx_start_delay_s == 0.0 else "off"
        self._tx_timer = 0.0
        self._rx_timer = 0.0
        self._tx_level = 1.0 if self.tx_state == "on" else 0.0
        self.energy_tx = 0.0
        self.energy_rx = 0.0
        self.energy_idle = 0.0

    # ------------------------------------------------------------------
    # Transceiver state helpers
    # ------------------------------------------------------------------
    def start_tx(self) -> None:
        if self.tx_start_delay_s > 0.0:
            self.tx_state = "starting"
            self._tx_timer = self.tx_start_delay_s
            self._tx_level = 0.0
        elif self.pa_ramp_up_s > 0.0:
            self.tx_state = "ramping_up"
            self._tx_timer = self.pa_ramp_up_s
            self._tx_level = 0.0
        else:
            self.tx_state = "on"
            self._tx_level = 1.0

    def start_rx(self) -> None:
        if self.rx_start_delay_s > 0.0:
            self.rx_state = "starting"
            self._rx_timer = self.rx_start_delay_s
        else:
            self.rx_state = "on"

    def stop_tx(self) -> None:
        if self.pa_ramp_down_s > 0.0 and self.tx_state == "on":
            self.tx_state = "ramping_down"
            self._tx_timer = self.pa_ramp_down_s
            self._tx_level = 1.0
        else:
            self.tx_state = "off"
            self._tx_level = 0.0

    def stop_rx(self) -> None:
        self.rx_state = "off"

    def update(self, dt: float) -> None:
        # Accumulate energy consumption based on current state
        if self.tx_state == "starting":
            current = self.tx_start_current_a or self.tx_current_a
            self.energy_tx += self.voltage_v * current * dt
        elif self.tx_state in ("ramping_up", "ramping_down"):
            current = self.pa_ramp_current_a or self.tx_current_a
            self.energy_tx += self.voltage_v * current * dt
        elif self.tx_state != "off":
            self.energy_tx += (
                self.voltage_v * self.tx_current_a * self._tx_level * dt
            )
        elif self.rx_state == "starting":
            current = self.rx_start_current_a or self.rx_current_a
            self.energy_rx += self.voltage_v * current * dt
        elif self.rx_state == "on":
            self.energy_rx += self.voltage_v * self.rx_current_a * dt
        else:
            self.energy_idle += self.voltage_v * self.idle_current_a * dt

        if self.tx_state == "starting":
            self._tx_timer -= dt
            if self._tx_timer <= 0.0:
                if self.pa_ramp_up_s > 0.0:
                    self.tx_state = "ramping_up"
                    self._tx_timer = self.pa_ramp_up_s
                    self._tx_level = 0.0
                else:
                    self.tx_state = "on"
                    self._tx_level = 1.0
        elif self.tx_state == "ramping_up":
            self._tx_timer -= dt
            self._tx_level = 1.0 - max(self._tx_timer, 0.0) / self.pa_ramp_up_s
            if self._tx_timer <= 0.0:
                self.tx_state = "on"
                self._tx_level = 1.0
        elif self.tx_state == "ramping_down":
            self._tx_timer -= dt
            self._tx_level = max(self._tx_timer, 0.0) / self.pa_ramp_down_s
            if self._tx_timer <= 0.0:
                self.tx_state = "off"
                self._tx_level = 0.0
        if self.rx_state == "starting":
            self._rx_timer -= dt
            if self._rx_timer <= 0.0:
                self.rx_state = "on"

    @property
    def radio_state(self) -> str:
        """Return simplified transceiver state (TX/RX/IDLE)."""
        if self.tx_state != "off":
            return "TX"
        if self.rx_state == "on":
            return "RX"
        return "IDLE"

    # ------------------------------------------------------------------
    def path_loss(self, distance: float) -> float:
        """Return path loss in dB using the log distance model."""
        if distance <= 0:
            return 0.0
        d = max(distance, 1.0)
        ch = self.channel
        loss = ch.path_loss_d0 + 10 * ch.path_loss_exp * math.log10(
            d / ch.reference_distance
        )
        return loss + self.channel.system_loss_dB

    def noise_floor(self) -> float:
        """Return the noise floor (dBm) including optional variations."""
        ch = self.channel
        if ch.receiver_noise_floor_dBm != -174.0:
            thermal = ch.receiver_noise_floor_dBm
        else:
            if self._temperature.std > 0.0:
                temp = self._temperature.sample()
                original = self.model.temperature_K
                self.model.temperature_K = temp
                eff_bw = min(ch.bandwidth, ch.frontend_filter_bw)
                thermal = self.model.thermal_noise_dBm(eff_bw)
                self.model.temperature_K = original
            else:
                eff_bw = min(ch.bandwidth, ch.frontend_filter_bw)
                thermal = self.model.thermal_noise_dBm(eff_bw)
        noise = thermal + ch.noise_figure_dB + ch.interference_dB
        if ch.humidity_noise_coeff_dB != 0.0:
            noise += ch.humidity_noise_coeff_dB * (ch._humidity.sample() / 100.0)
        for f, bw, power in ch.band_interference:
            half = (bw + ch.bandwidth) / 2.0
            diff = abs(ch.frequency_hz - f)
            if diff <= half:
                noise += power
            elif ch.adjacent_interference_dB > 0 and diff <= half + ch.bandwidth:
                noise += max(power - ch.adjacent_interference_dB, 0.0)
        if ch.noise_floor_std > 0:
            noise += random.gauss(0.0, ch.noise_floor_std)
        if ch.impulsive_noise_prob > 0.0 and random.random() < ch.impulsive_noise_prob:
            noise += ch.impulsive_noise_dB
        noise += self.model.noise_variation()
        noise += self._osc_leak.sample()
        return noise

    def compute_rssi(
        self,
        tx_power_dBm: float,
        distance: float,
        sf: int | None = None,
        *,
        tx_pos: tuple[float, float] | tuple[float, float, float] | None = None,
        rx_pos: tuple[float, float] | tuple[float, float, float] | None = None,
        tx_angle: float | tuple[float, float] | None = None,
        rx_angle: float | tuple[float, float] | None = None,
        freq_offset_hz: float | None = None,
        sync_offset_s: float | None = None,
    ) -> tuple[float, float]:
        if self.rx_state != "on":
            return -float("inf"), -float("inf")
        ch = self.channel
        loss = self.path_loss(distance)
        if ch.shadowing_std > 0:
            loss += random.gauss(0.0, ch.shadowing_std)

        if freq_offset_hz is None:
            freq_offset_hz = self._freq_offset.sample()
        # Include time-varying frequency drift
        freq_offset_hz += self.model.frequency_drift()
        freq_offset_hz += self._dev_freq.sample()
        if sync_offset_s is None:
            sync_offset_s = self._sync_offset.sample()
        # Include short-term clock jitter
        sync_offset_s += self.model.clock_drift()
        if self.clock_jitter_std_s > 0.0:
            sync_offset_s += random.gauss(0.0, self.clock_jitter_std_s)

        phase = self._phase_offset.sample()

        tx_power_dBm += self._pa_nl.sample()
        if self._tx_level < 1.0:
            tx_power_dBm += 20.0 * math.log10(max(self._tx_level, 1e-3))
        rssi = (
            tx_power_dBm
            + ch.tx_antenna_gain_dB
            + ch.rx_antenna_gain_dB
            - loss
            - ch.cable_loss_dB
        )
        if (
            tx_angle is not None
            and rx_angle is not None
            and tx_pos is not None
            and rx_pos is not None
        ):
            dx = rx_pos[0] - tx_pos[0]
            dy = rx_pos[1] - tx_pos[1]
            dz1 = tx_pos[2] if len(tx_pos) >= 3 else 0.0
            dz2 = rx_pos[2] if len(rx_pos) >= 3 else 0.0
            dz = dz2 - dz1
            dist = math.sqrt(dx * dx + dy * dy + dz * dz)
            if dist > 0.0:
                los = (dx / dist, dy / dist, dz / dist)

                def _vec(angle):
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

                tx_vec = _vec(tx_angle)
                rx_vec = _vec(rx_angle)
                tx_dot = max(min(sum(a * b for a, b in zip(los, tx_vec)), 1.0), -1.0)
                rx_dot = max(min(sum(-a * b for a, b in zip(los, rx_vec)), 1.0), -1.0)
                tx_diff = math.acos(tx_dot)
                rx_diff = math.acos(rx_dot)
                rssi += self._directional_gain(tx_diff)
                rssi += self._directional_gain(rx_diff)
        if ch.tx_power_std > 0:
            rssi += random.gauss(0.0, ch.tx_power_std)
        if ch.fast_fading_std > 0:
            rssi += random.gauss(0.0, ch.fast_fading_std)
        if ch.multipath_taps > 1:
            rssi += self._multipath_fading_db()
        if ch.time_variation_std > 0:
            rssi += random.gauss(0.0, ch.time_variation_std)
        rssi += self.model.fine_fading()
        rssi += ch.rssi_offset_dB
        rssi -= ch._filter_attenuation_db(freq_offset_hz)

        snr = rssi - self.noise_floor() + ch.snr_offset_dB
        penalty = self._alignment_penalty_db(freq_offset_hz, sync_offset_s, phase, sf)
        snr -= penalty
        snr -= abs(self._phase_noise.sample())
        snr -= abs(self._rx_fault.sample())
        if sf is not None:
            snr += 10 * math.log10(2 ** sf)
        return rssi, snr

    def _alignment_penalty_db(
        self, freq_offset_hz: float, sync_offset_s: float, phase_offset_rad: float, sf: int | None
    ) -> float:
        """Return SNR penalty for imperfect alignment."""
        bw = self.channel.bandwidth
        freq_factor = abs(freq_offset_hz) / (bw / 2.0)
        if sf is not None:
            symbol_time = (2 ** sf) / bw
        else:
            symbol_time = 1.0 / bw
        time_factor = abs(sync_offset_s) / symbol_time
        if freq_factor >= 1.0 and time_factor >= 1.0:
            return float("inf")
        phase_factor = abs(math.sin(phase_offset_rad / 2.0))
        penalty = 1.5 * (freq_factor ** 2 + time_factor ** 2 + phase_factor ** 2)
        return 10 * math.log10(1.0 + penalty)

    def capture(
        self,
        rssi_list: list[float],
        start_list: list[float] | None = None,
        end_list: list[float] | None = None,
        sf_list: list[int] | None = None,
        freq_list: list[float] | None = None,
    ) -> list[bool]:
        """Return capture decision with optional partial overlap weighting."""
        if not rssi_list:
            return []

        n = len(rssi_list)
        winners = [False] * n

        if self.flora_capture:
            if (
                start_list is None
                or end_list is None
                or sf_list is None
                or freq_list is None
            ):
                raise ValueError("sf_list, freq_list, start_list and end_list required")

            order = sorted(range(n), key=lambda i: rssi_list[i], reverse=True)
            if len(order) == 1:
                winners[order[0]] = True
                return winners

            idx0 = order[0]
            sf0 = sf_list[idx0]
            rssi0 = rssi_list[idx0]
            freq0 = freq_list[idx0]
            start0 = start_list[idx0]
            end0 = end_list[idx0]
            symbol_time = (2 ** sf0) / self.channel.bandwidth
            cs_begin = start0 + symbol_time * (
                self.channel.preamble_symbols - self.capture_window_symbols
            )

            captured = True
            for idx in order[1:]:
                if freq_list[idx] != freq0:
                    continue
                overlap = min(end0, end_list[idx]) > max(start0, start_list[idx])
                if not overlap:
                    continue
                diff = rssi0 - rssi_list[idx]
                th = self.NON_ORTH_DELTA[sf0 - 7][sf_list[idx] - 7]
                capture_effect = diff >= th
                timing_collision = cs_begin < end_list[idx]
                if not capture_effect and timing_collision:
                    captured = False
                    break

            if captured:
                winners[idx0] = True
            return winners

        if start_list is None or end_list is None:
            order = sorted(range(n), key=lambda i: rssi_list[i], reverse=True)
            if n == 1:
                winners[order[0]] = True
                return winners
            if rssi_list[order[0]] - rssi_list[order[1]] >= self.channel.capture_threshold_dB:
                winners[order[0]] = True
            return winners

        noise = self.noise_floor()
        powers = [10 ** (r / 10.0) for r in rssi_list]
        snrs: list[float] = []
        for i in range(n):
            total = 10 ** (noise / 10.0)
            dur_i = max(end_list[i] - start_list[i], 1e-9)
            for j in range(n):
                if j == i:
                    continue
                overlap = min(end_list[i], end_list[j]) - max(start_list[i], start_list[j])
                if overlap <= 0.0:
                    continue
                total += (overlap / dur_i) * powers[j]
            snrs.append(10 * math.log10(powers[i] / total))

        order = sorted(range(n), key=lambda i: snrs[i], reverse=True)
        if n == 1:
            winners[order[0]] = True
        elif snrs[order[0]] - snrs[order[1]] >= self.channel.capture_threshold_dB:
            winners[order[0]] = True
        return winners

    def _multipath_fading_db(self) -> float:
        """Return a fading value in dB based on multiple Rayleigh paths."""
        taps = self.channel.multipath_taps
        if taps <= 1:
            return 0.0
        i = sum(random.gauss(0.0, 1.0) for _ in range(taps))
        q = sum(random.gauss(0.0, 1.0) for _ in range(taps))
        amp = math.sqrt(i * i + q * q) / math.sqrt(taps)
        return 20 * math.log10(max(amp, 1e-12))

    def _directional_gain(self, angle_rad: float) -> float:
        """Return antenna gain for the given angle."""
        if callable(self.antenna_model):
            return float(self.antenna_model(angle_rad))
        model = str(self.antenna_model).lower()
        if model == "isotropic":
            return 0.0
        if model in ("cos", "cosine"):
            gain = max(math.cos(angle_rad), 0.0)
        else:
            gain = max(math.cos(angle_rad), 0.0) ** 2
        return 10 * math.log10(max(gain, 1e-3))

