"""Bounded read-only path audit; large payloads are never opened."""
import ast
import json
from pathlib import Path
import sys

AREA = Path(__file__).resolve().parent.parent
OLD = '/scratch/jjyeung/orch_n30/trin_read'
LIMIT = 4*1024**2


def flatten(value, where='$'):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from flatten(item, where+'.'+str(key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from flatten(item, where+'['+str(index)+']')
    elif isinstance(value, str):
        yield where, value


def main():
    rows = []; scanned = []; skipped = []
    def source(path, staged=False):
        scanned.append(str(path.relative_to(AREA)))
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Str) or not node.s.startswith('/'): continue
            value=node.s
            category='namespace-absolute (unaffected)'
            action='Keep logical namespace/system paths; bind sources come from the selected root.'
            if OLD in value:
                category='blocks relocation' if staged else 'follows TRIN_AREA'
                action=('Use build_p or build_t6p as the entry point; keep this staged source and its manifest unchanged.'
                        if staged else 'The literal records the unchanged default or tests that default; TRIN_AREA selects the lane.')
            elif '/evalx27/' in value:
                category='blocks relocation' if staged or '/tests/' in str(path) else 'follows TRIN_AREA'
                action=('This external reference remains in the staged or test source. Use the relocated build entry point and its KIT-local reference; inherited integration tests still need their external fixtures.'
                        if staged or '/tests/' in str(path) else 'With TRIN_AREA set, REFERENCE uses KIT/build/pb59bef09f3; unset keeps the default.')
            elif value == '/scratch' and path.name == 'milestone.py':
                category='follows TRIN_AREA';action='completed_local also accepts a regular, non-symlink file beneath TRIN_AREA.'
            rows.append(dict(file=str(path.relative_to(AREA)), line=node.lineno, value=value,
                             names_original_area=OLD in value, classification=category, handling=action))
    for build in ('build_p','build_t6p'):
        for name in ('trinity_read.py','namespace_worker.py','compare_tokens.py','milestone.py'):
            p=AREA/build/name
            if p.exists(): source(p)
        for p in sorted((AREA/build/'tests').glob('*.py')): source(p)
    root=AREA/'root'
    paths={root/'STAGING.json',root/'bootstrap/CONFIG.json'}
    paths.update((root/'trinity_runner').iterdir())
    # Receipts live immediately under each need/probe packet. Do not traverse environments.
    for name in ('needs','runs','exports'):
        parent=root/name
        if not parent.exists(): continue
        for packet in parent.iterdir():
            if packet.is_dir() and not packet.is_symlink():
                paths.update(p for p in packet.iterdir() if p.suffix=='.json')
    cached=AREA/'work/selfcheck_13_t3b.json'
    if cached.exists() and cached.stat().st_size<LIMIT:
        audit=json.loads(cached.read_text())
        for row in audit['portability']['findings']:
            p=Path(row['file'])
            if p.name=='CONFIG.json' and str(p).startswith(str(root)+'/'): paths.add(p)
    for p in sorted(paths):
        if p.is_symlink() or not p.is_file(): continue
        if p.stat().st_size>=LIMIT:
            skipped.append(dict(file=str(p.relative_to(AREA)),bytes=p.stat().st_size,reason='4 MiB file limit'))
            continue
        if p.suffix=='.py': source(p,staged=True);continue
        scanned.append(str(p.relative_to(AREA)))
        if p.suffix!='.json': continue
        for field,value in flatten(json.loads(p.read_text())):
            if OLD not in value: continue
            rows.append(dict(file=str(p.relative_to(AREA)),field=field,value=value,names_original_area=True,
                classification='blocks relocation',
                handling='Retained execution receipt names the old host path. Keep bytes unchanged; generate fresh need/probe/read receipts under TRIN_AREA. Never replay recorded argv or reuse a recorded run CONFIG as an entry point.'))
    result=dict(scope='Active source modules, top-level test modules, staged bootstrap CONFIG and runner, packet receipts and CONFIG paths recorded by the existing selfcheck. Retained test output trees are inert copied evidence, not test modules.',
                scanned=scanned,skipped=skipped,rows=rows)
    out=AREA/'build_p/PATH_AUDIT_P.json'
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(scanned=len(scanned),absolute_strings=len(rows),lane_references=sum(r['names_original_area'] for r in rows),skipped=skipped)))

if __name__=='__main__': main()
