"""Refresh code pins without expanding the sealed production member inventory."""
from pathlib import Path
import sys
B=Path(__file__).resolve().parents[1];O=B/'out';K=O/'guard_kit'
sys.path.insert(0,str(K))
from guard_core import read,write,sha

baseline=read(B/'work/G3_BASELINE.json')
family=read(O/'FAMILY.json')
names=baseline['code_manifest']['members']
assert set(names)==set(baseline['family']['code_pins'])
assert family['release_ready'] is False
family['code_pins']={name:sha(K/name) for name in names}
family['blockers']=[blocker for blocker in family['blockers']
                    if blocker!='Whole-worker CPU namespace run has not completed.']
assert family['blockers']
write(O/'FAMILY.json',family)
print('Family pins refreshed; production release remains blocked.')
