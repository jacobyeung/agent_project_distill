"""Compute real receipt identities without running any phase or neural forward."""
import json
import os
from pathlib import Path
import sys

assert os.environ['CUDA_VISIBLE_DEVICES'] == ''
kit = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(kit / 'native_kit'), str(kit / 'work')]
import bindings as B

print(json.dumps({
    'kit': str(kit),
    'bindings_module': B.__file__,
    'source_identity': B.source_identity(),
    'producer_sha256': B.sha(kit / 'work/k1_phases.py'),
}, indent=2, sort_keys=True))
