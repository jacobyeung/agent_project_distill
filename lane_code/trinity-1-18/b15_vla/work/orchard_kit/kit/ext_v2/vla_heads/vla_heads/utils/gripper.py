"""Gripper conventions (vla_schema_v2 section 7).

The canonical unit g (`unit_open_neg`) is -1 = open and +1 = close, the LIBERO environment's command
convention. The head regresses g with L1 and g is not normalised. Dataset conventions:
- `unit_open_neg`: already g (LIBERO environment commands);
- `ipec`: IPEC LeRobot data, a6 in {0, 1} with 1 = open, so g = 1 - 2 a6 and a6 = (1 - g) / 2.
Execution sends `gripper_command(g)`: +1 (close) if g >= 0, else -1 (open). This equals StarVLA's
client (env = 1 - 2 [a6 > 0.5]) with a6 = (1 - g) / 2 for every g, the tie g = 0 included.
"""
import numpy as np
import torch

CONVENTIONS = ('unit_open_neg', 'ipec')


def _check(convention):
    if convention not in CONVENTIONS:
        raise ValueError(f'gripper convention {convention!r}; choose one of {CONVENTIONS}')


def gripper_to_unit(a, convention='ipec'):
    """Dataset gripper value -> canonical g (-1 open, +1 close)."""
    _check(convention)
    return a if convention == 'unit_open_neg' else 1 - 2 * a


def gripper_from_unit(g, convention='ipec'):
    """Canonical g -> the dataset's gripper value (the inverse of gripper_to_unit)."""
    _check(convention)
    return g if convention == 'unit_open_neg' else (1 - g) / 2


def gripper_command(g):
    """Predicted g -> the environment command: +1 (close) if g >= 0, else -1 (open)."""
    if torch.is_tensor(g):
        return torch.where(g >= 0, 1.0, -1.0).to(g.dtype)
    return np.where(np.asarray(g) >= 0, 1.0, -1.0)
