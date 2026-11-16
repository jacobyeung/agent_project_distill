"""Keep the unchanged reader tests' output in K and import the patched tree."""
import sys
from pathlib import Path
import torch
K=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(K/'tree'))
from student_pilot import carrier_c1_routing  # bind the tested implementation before reader test imports

def pytest_collection_modifyitems(items):
    torch.set_num_threads(2)
    sys.path.insert(0,str(K/'tree'))
    for item in items:
        module=item.module
        if module.__name__.endswith('test_tiny_e2e'):
            module.OUT=K/'tmp/reader_proofs'
            module.CODE_ROOTS={'reader':Path('/scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader'),'tree':K/'tree'}
