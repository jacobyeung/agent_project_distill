"""Verify local reader copies and imported dependencies against the R1 source manifest."""
import hashlib
import json
from pathlib import Path
from adapters import ROOT, TREE, READER
from dryrun import PINS, read, write, OUT

PACK=Path('/scratch/jjyeung/n30_mirror/sb_headacc2/pack')


def main():
    expected={line.split()[1]:line.split()[0] for line in read(PACK/'R1_A4_SRC_SHA256.txt').decode().splitlines() if line.strip()}
    paths=[(p,'b/e2e_reader/'+p.name,'replay_reader') for p in sorted((ROOT/'reader_src/e2e_reader').glob('*.py'))]
    for p in sorted((ROOT/'vendor').glob('*.py')):
        key=('b/heads/selector/' if p.name=='selector_head.py' else 'b/e2e_reader/')+p.name
        paths.append((p,key,'inherited_vendor'))
    for rel in ['student_pilot/routed_candidates.py','student_pilot/routed_features.py','student_pilot/camera_targets.py',
                'student_pilot/tower_scale_rule.py','student_pilot/geometry_profiles.py','student_pilot/ground_profiles.py',
                'student_pilot/ground_lifting.py']:
        paths.append((TREE/rel,'tree/'+rel,'replay_dependency'))
    for rel in ['selector_head.py','sl118/selector_inputs.py']:
        paths.append((READER/'heads/selector'/rel,'b/heads/selector/'+rel,'replay_dependency'))
    rows=[]
    for p,key,role in paths:
        actual=hashlib.sha256(read(p)).hexdigest()
        rows.append(dict(path=str(p),role=role,manifest_key=key,sha256=actual,expected_sha256=expected.get(key),
                         status='MISSING_MANIFEST_ENTRY' if key not in expected else 'MATCH' if actual==expected[key] else 'DIFFERS'))
    read(ROOT/'audit_sources.py')
    write(OUT/'SOURCE_AUDIT.json',dict(rows=rows))
    print(json.dumps([r for r in rows if r['status']!='MATCH'],indent=2))


if __name__=='__main__':main()
