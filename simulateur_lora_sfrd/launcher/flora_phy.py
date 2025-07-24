"""FLoRa-like physical layer helpers."""

from __future__ import annotations

import math
import random


class FloraPHY:
    """Replicate FLoRa path loss and capture formulas."""

    NON_ORTH_DELTA = [
        [1, -8, -9, -9, -9, -9],
        [-11, 1, -11, -12, -13, -13],
        [-15, -13, 1, -13, -14, -15],
        [-19, -18, -17, 1, -17, -18],
        [-22, -22, -21, -20, 1, -20],
        [-25, -25, -25, -24, -23, 1],
    ]

    REFERENCE_DISTANCE = 40.0
    PATH_LOSS_D0 = 127.41

    def __init__(self, channel) -> None:
        self.channel = channel

    def path_loss(self, distance: float) -> float:
        if distance <= 0:
            return 0.0
        loss = (
            self.PATH_LOSS_D0
            + 10 * self.channel.path_loss_exp
            * math.log10(max(distance, 1.0) / self.REFERENCE_DISTANCE)
        )
        if self.channel.shadowing_std > 0:
            loss += random.gauss(0.0, self.channel.shadowing_std)
        return loss + self.channel.system_loss_dB

    def capture(self, rssi_list: list[float], sf_list: list[int]) -> list[bool]:
        if not rssi_list:
            return []
        order = sorted(range(len(rssi_list)), key=lambda i: rssi_list[i], reverse=True)
        winners = [False] * len(rssi_list)
        if len(order) == 1:
            winners[order[0]] = True
            return winners
        idx0 = order[0]
        sf0 = sf_list[idx0]
        rssi0 = rssi_list[idx0]
        captured = True
        for idx in order[1:]:
            diff = rssi0 - rssi_list[idx]
            th = self.NON_ORTH_DELTA[sf0 - 7][sf_list[idx] - 7]
            if diff < th:
                captured = False
                break
        if captured:
            winners[idx0] = True
        return winners
