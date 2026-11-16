import copy
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TREE = os.environ.get('VLA_TREE', '/scratch/jjyeung/orch_cd/integ_v3/work/tree')
for path in (str(ROOT), TREE):
    if path not in sys.path:
        sys.path.insert(0, path)

import torch  # noqa: E402

torch.set_num_threads(int(os.environ.get('OMP_NUM_THREADS', '4')))


@pytest.fixture(scope='session')
def tiny_student_base():
    from vla_heads.testing import tiny_qwen35
    return tiny_qwen35()


@pytest.fixture
def tiny_student(tiny_student_base):
    """A fresh copy per test: adapters register hooks and LoRA modules on the model they wrap."""
    return copy.deepcopy(tiny_student_base)
