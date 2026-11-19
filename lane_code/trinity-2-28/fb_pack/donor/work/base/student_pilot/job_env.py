"""Opaque deployment names preserve the legacy environment contract."""
import os
ALIASES = {'STUDENT_ORCHARD': 'Q_E1', 'STUDENT_SLURM_SITE': 'Q_E2', 'STUDENT_MODEL_ROOT': 'Q_E3', 'STUDENT_FRAME_ROOT_MAP': 'Q_E4', 'R1_STUDENT_HEX': 'Q_E5'}
def key(name):
    alias=ALIASES.get(name)
    return alias if alias is not None and alias in os.environ else name
