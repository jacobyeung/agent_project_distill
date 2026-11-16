"""Gripper maps between dataset conventions and the normalised [-1, 1] (-1 = open)."""
import numpy as np
import torch


def gripper_to_unit(g, open_value=-1.0):
    """Map a gripper command to [-1, 1] with -1 = open. `open_value` is the dataset's open value
    (-1 for LIBERO; 0 for datasets with 0 = open, 1 = close)."""
    if open_value == -1.0:
        return g
    if open_value == 0.0:
        return 2 * g - 1
    if open_value == 1.0:
        return -g
    raise ValueError('open_value must be -1, 0 or 1')


def gripper_from_unit(g, open_value=-1.0, binarize=True):
    """Inverse of gripper_to_unit. `binarize` snaps to the closed/open command (sign, 0 -> open)."""
    if binarize:
        g = torch.where(g > 0, 1.0, -1.0).to(g.dtype) if torch.is_tensor(g) else np.where(np.asarray(g) > 0, 1.0, -1.0)
    if open_value == -1.0:
        return g
    if open_value == 0.0:
        return (g + 1) / 2
    if open_value == 1.0:
        return -g
    raise ValueError('open_value must be -1, 0 or 1')
