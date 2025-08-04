"""Utilities for estimating environmental losses.

This module provides a helper to estimate the attenuation introduced by
obstacles between a transmitter and a receiver.  The attenuation can be
estimated either from a simple 2D raster map or from an arbitrary 3D model
object exposing a ``loss_between`` method.

The implementation is intentionally lightweight and does not depend on any
particular GIS or 3D engine.  It serves as a basic building block that can be
extended with more sophisticated models if needed.
"""

from __future__ import annotations

from typing import Sequence, Any

import numpy as np


def compute_obstacle_loss_dB(
    tx_pos: Sequence[float],
    rx_pos: Sequence[float],
    env_map: Sequence[Sequence[float]] | np.ndarray | None = None,
    model_3d: Any | None = None,
) -> float:
    """Estimate additional path loss caused by obstacles.

    Parameters
    ----------
    tx_pos, rx_pos:
        Coordinates of the transmitter and receiver. Only the X/Y components
        are considered for the 2D map case. 3D models may use the optional Z
        component if available.
    env_map:
        Optional 2D array-like structure representing an attenuation map in dB
        per cell.  The grid is sampled along the line-of-sight and the values
        are summed.
    model_3d:
        Optional object with a ``loss_between(tx_pos, rx_pos)`` method
        returning the attenuation in dB.

    Returns
    -------
    float
        The estimated loss in decibels due to obstacles. ``0.0`` is returned
        when no environmental data is supplied.
    """

    if model_3d is not None and hasattr(model_3d, "loss_between"):
        return float(model_3d.loss_between(tx_pos, rx_pos))

    if env_map is None:
        return 0.0

    grid = np.asarray(env_map, dtype=float)
    x0, y0 = tx_pos[0], tx_pos[1]
    x1, y1 = rx_pos[0], rx_pos[1]

    # Sample points along the straight line connecting the two positions. The
    # sampling step is one unit in the dominant axis direction.
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    xs = np.linspace(x0, x1, n)
    ys = np.linspace(y0, y1, n)

    h, w = grid.shape
    loss = 0.0
    for x, y in zip(xs, ys):
        ix = int(round(x))
        iy = int(round(y))
        if 0 <= ix < w and 0 <= iy < h:
            loss += float(grid[iy, ix])

    return loss


__all__ = ["compute_obstacle_loss_dB"]

