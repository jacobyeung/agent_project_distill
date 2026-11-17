"""Run staged CPU suites with every fixture/code path constrained to W."""
import os,sys,time
from pathlib import Path
W=Path(__file__).resolve().parents[1]
base='out/baseline' if '--baseline' in sys.argv else 'out/src';P=W/base
root=Path('/scratch/jjyeung/orch_n30/reader_r1/work/b1/work/b04full');tests=W/'work/existing_full'/('baseline' if '--baseline' in sys.argv else 'patched')
tests.mkdir(parents=True,exist_ok=True)
for p in (root/'tests').glob('test_*.py'):
 s=p.read_text().replace('ROOT = Path(__file__).resolve().parents[1]',f'ROOT = Path({str(root)!r})')
 s=s.replace('/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449',str(P/'tree'))
 s=s.replace('/scratch/jjyeung/n30_mirror/k1_ops3/run_tower_sam_2',str(W/'work/missing_k1'))
 (tests/p.name).write_text(s)
sys.path[:0]=[str(P/'b'),str(P/'tree'),str(P),str(tests),str(root/'tests')]
# Resolve reader submodules to the selected package before legacy tests prepend b04 paths.
import e2e_reader
assert Path(e2e_reader.__file__).is_relative_to(P)
import pytest
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
raise SystemExit(pytest.main(['-ra','--tb=short','-p','no:cacheprovider','--basetemp',str(W/'work/pytest_tmp'/str(time.time_ns())),str(tests)]))
