from pathlib import Path
import sys,traceback
L=Path(__file__).resolve().parents[2];sys.path[:0]=[str(L/'work/build21'),str(L/'work/tree_r1')]
import resolver21e as R
f=R.fixture()
try:
    with R.external_boundary(f):v=R.J.resolve(R.K,f['pool'],f['listing'],f['root']/'resolved.json')
    print('PASS',v['config']['r1_training']['donor_config_sha256'])
except Exception:traceback.print_exc()
