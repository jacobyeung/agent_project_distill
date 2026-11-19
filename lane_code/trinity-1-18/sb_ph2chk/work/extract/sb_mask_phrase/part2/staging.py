"""Verify the materialized GPU payload, environment and all launch control files."""
import collections
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import sam3_pass as G

ROOT = G.HERE.parent
DEST = ROOT/'out'


def main():
    material = DEST/'STAGING_MATERIALIZED.json'
    source = json.loads(material.read_text())
    entries = {r['staged_path']: r for r in source['inventory']}
    supplement = ROOT/'out/ENV_SUPPLEMENT.json'
    entries.update({r['staged_path']: r for r in json.loads(supplement.read_text())['inventory']})
    for p in (G.HERE/'part2').rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:
            rel=str(p.relative_to(ROOT))
            entries[rel]=dict(path=str(p),staged_path=rel,roles=['control'])
    for p in (ROOT/'stage_payload.py', ROOT/'relocate_environment.py', ROOT/'supplement_environment.py', ROOT/'verify_staged.py', ROOT/'verify_cpu.py', ROOT/'package.sh', ROOT/'write_report.py', *sorted((ROOT/'work').glob('*ph2fix2*.py'))):
        rel=str(p.relative_to(ROOT)); entries[rel]=dict(path=str(p),staged_path=rel,roles=['control'])
    relocated = ROOT/'payload/environment/lib/python3.12/site-packages/__editable___sam3_0_1_0_finder.py'
    entries[str(relocated.relative_to(ROOT))]['roles'] = ['sam_environment', 'control']
    rows=[]; pins={str(supplement): G.sha(supplement), str(material):G.sha(material), str(ROOT/'out/ENV_RELOCATION.json'): G.sha(ROOT/'out/ENV_RELOCATION.json')}
    for rel,r in sorted(entries.items()):
        p=ROOT/rel
        if not p.is_file():
            rows.append(dict(r,status='MISSING',bytes=None)); continue
        actual=G.sha(p)
        expected=r.get('sha256') if 'control' not in r['roles'] else None
        row=dict(r,bytes=p.stat().st_size,sha256=actual,status='PASS' if expected in (None,actual) else 'FAIL')
        rows.append(row); pins[str(p)]=actual
    groups={}
    for role in sorted({role for r in rows for role in r['roles']}):
        subset=[r for r in rows if role in r['roles']]
        groups[role]=dict(files=len(subset),bytes=sum(r['bytes'] or 0 for r in subset))
    estimate_path = DEST/'GPU_ESTIMATE_PH2FIX2.json'
    estimate = json.loads(estimate_path.read_text())
    estimates = estimate['estimates']
    pins[str(estimate_path)] = G.sha(estimate_path)
    pins[str(G.HERE/'in/v3/KIT_SPEC_mask_phrase_v2.md')]=G.sha(G.HERE/'in/v3/KIT_SPEC_mask_phrase_v2.md')
    total=sum(r['bytes'] or 0 for r in rows)
    result=dict(status='PASS' if all(r['status']=='PASS' for r in rows) else 'MISSING_OR_FAIL',
                scope='Self-contained staged GPU application and SAM3 Python environment; host Linux/NVIDIA driver and standard shell utilities required',
                environment=str(ROOT/'payload/environment'),environment_source='/scratch/jjyeung/envs/sam3_capretry_native_v1',
                command='bash sb_mask_phrase/run.sh part2/staging.py',files=len(rows),bytes=total,GB=total/1e9,
                groups=groups,estimates=estimates,
                estimate_basis=estimate['formula']+'; '+estimate['limitation'],
                inventory=rows,input_sha256=pins)
    (DEST/'STAGING_PART2.json').write_text(json.dumps(result,indent=1)+'\n')
    (DEST/'STAGING_PART2.tsv').write_text('bytes\tsha256\troles\tstatus\tpath\tstaged_path\n'+''.join(
        f"{r['bytes']}\t{r.get('sha256','MISSING')}\t{','.join(r['roles'])}\t{r['status']}\t{r['path']}\t{r['staged_path']}\n" for r in rows))
    print(json.dumps({k:v for k,v in result.items() if k not in ('inventory','input_sha256')},indent=1))
    if result['status']!='PASS': raise SystemExit(1)


if __name__=='__main__': main()
