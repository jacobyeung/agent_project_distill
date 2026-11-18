from pathlib import Path
L=Path(__file__).resolve().parents[2]
for rel in ('n1fix/handover','r1/export'):
    root=L/'work/n1fix2/proofs/targeted'/rel
    if (root/'m200').exists(): (root/'m200').rename(root/'invalid_fixture_export2')
    if (root/'binding.json').exists(): (root/'binding.json').rename(root/'invalid_fixture_binding2.json')
