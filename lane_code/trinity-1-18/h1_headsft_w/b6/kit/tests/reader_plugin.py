"""Keep the unchanged reader tests' output in K and import the patched tree."""
import sys
import os
from pathlib import Path
import torch
import h1eval
from e2e_reader import artifact  # bind the frozen reader before the unchanged test imports
K=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(K/'tree'))
from student_pilot import carrier_c1_routing  # bind the tested implementation before reader test imports

def pytest_collection_modifyitems(items):
    torch.set_num_threads(2)
    sys.path.insert(0,str(K/'tree'))
    for item in items:
        module=item.module
        if module.__name__.endswith('test_tiny_e2e'):
            module.OUT=Path(os.environ.get('LANE_TEST_OUTPUT', K/'tmp/b4'))/'reader_proofs'
            module.CODE_ROOTS={'reader':K/'h1eval/reader_core/e2e_reader','tree':K/'tree'}
