from pathlib import Path
import json
import sys
L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'work/tree_r1'))
from tests.test_r2_data_path import SOURCES
dest=L/'fixtures'
dest.mkdir(exist_ok=True)
names=['work/shared/WITHHELD_ROOMS_80.json','work/shared/dev_scene_exclusions_d0.json',
 'work/records/design/REFREEZE_PREREGISTRATION_20261115.json',
 'work/records/design/POLICY_AUDIT_20261115.md','work/build3/apply_contracts.py']
names += ['work/records/'+v for v in SOURCES.values()]
names += [str(p.relative_to(L)) for p in (L/'work/kit07ca49df_meta/m').rglob('*')
          if p.is_file() and p.suffix not in ('.tar','.sqlite','.pt','.npz')]
for name in names:
    p=L/name
    if not p.is_file():
        continue
    target=dest/name
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(p.read_bytes())
(dest/'references').mkdir(exist_ok=True)
(dest/'references/B3_BANK_ENTRYPOINTS.json').write_bytes((L/'out/B3_BANK_ENTRYPOINTS.json').read_bytes())
(dest/'work/tmp').mkdir(exist_ok=True)
for group in ('slices_v3','slices_final'):
    for source in (L/'work/rows_slices'/group).glob('*.jsonl'):
        target=dest/'rows'/group/source.name
        target.parent.mkdir(parents=True,exist_ok=True)
        # Small published examples suffice for package regression; the complete
        # bounded-slice intake proof stays in the builder's evidence directory.
        with source.open() as f:
            rows=[next(f) for _ in range(3)]
        target.write_text(''.join(rows))
size=sum(p.stat().st_size for p in dest.rglob('*') if p.is_file())
assert size <= 60_000_000, size
print(json.dumps(dict(fixture_bytes=size)))
