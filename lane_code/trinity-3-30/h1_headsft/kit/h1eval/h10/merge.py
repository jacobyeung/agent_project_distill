"""Validate complete shard coverage, then use the shared evaluator's scorers."""
import argparse
import json
from pathlib import Path
import sys
if not __package__:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]));__package__='h1eval.h10'
from .launch import read_records, write_json, shard
from h1eval.items import load_manifest, sha, K
from h1eval.cli import code_hash, export_hash, write_curve
from h1eval.modes import mode_key, plan


def merge(directories, out, items=None, *, _types=None):
    roots=[Path(p) for p in directories]
    envs=[json.loads((p/'environment.json').read_text()) for p in roots]
    first=envs[0];binding=first['binding']
    comparable=lambda b:{k:v for k,v in b.items() if k not in ('shard','ids','device')}
    if any(comparable(e['binding'])!=comparable(binding) for e in envs):raise ValueError('Shard bindings differ')
    ns={shard(e['binding']['shard'])[1] for e in envs}
    if len(ns)!=1:raise ValueError('Shard denominators differ')
    n=ns.pop();indices=[shard(e['binding']['shard'])[0] for e in envs]
    if _types is None:
        if sorted(indices)!=list(range(n)):raise ValueError('Missing or duplicate shards')
    else:
        from h1eval.cli import modes
        from h1eval.modes import DEFAULT_MODES
        if binding['arms']!=['own'] or binding['modes']!=[{'name':'none'},*modes(DEFAULT_MODES)]:
            raise ValueError('Type plan differs from allocation plan')
        pairs=[(int(p.parent.name),i) for p,i in zip(roots,indices)]
        if sorted(pairs)!=[(t,i) for t in range(len(_types)) for i in range(n)]:
            raise ValueError('Missing or duplicate type shards')
        identities=[json.loads((p.parents[2]/'IDENTITY.json').read_text()) for p in roots]
        if any(v!=identities[0] for v in identities):raise ValueError('Allocation identities differ')
        if identities[0]['cards']!=n or identities[0]['order']!=list(_types) or identities[0]['arms']!=binding['arms']:
            raise ValueError('Allocation identity differs from shards')
    manifest=load_manifest(items or first['items'])
    if manifest['item_set_sha256']!=binding['item_set_sha256']:raise ValueError('Merge items differ')
    if code_hash()!=binding['evaluator_code_sha256']:raise ValueError('Evaluator changed since launch')
    if sha(K/'rows/expected_calls.py')!=binding['expected_calls_sha256'] or sha(K/'tree/student_pilot/h1_r0.py')!=binding['r0_code_sha256']:
        raise ValueError('Question parser or R0 code changed since launch')
    by_id={r['id']:r for r in manifest['items']};all_rows={}
    for root,env in zip(roots,envs):
        b=env['binding'];i,n=shard(b['shard'])
        members=[r['id'] for r in manifest['items'][i::n]
                 if _types is None or r['question_type']==_types[int(root.parent.name)]]
        if b['ids']!=members:raise ValueError('Shard membership differs')
        expected=plan([by_id[k] for k in b['ids']],b['arms'],b['modes'])
        rows=read_records(root/'items.jsonl');actual={(r['id'],r['arm'],r['mode']) for r in rows}
        if actual!=expected:raise ValueError('Incomplete or extra shard records')
        for r in rows:
            if r['intervention']!=next(m for m in b['modes'] if mode_key(m)==r['mode']):raise ValueError('Record mode differs')
            if r['room_key']!=by_id[r['id']]['room_key'] or r['type']!=by_id[r['id']]['question_type']:raise ValueError('Record metadata differs')
            key=(r['id'],r['arm'],r['mode'])
            if key in all_rows:raise ValueError('Duplicate merged record')
            all_rows[key]=r
    if set(all_rows)!=plan(manifest['items'],binding['arms'],binding['modes']):
        raise ValueError('Merged union differs from full plan')
    from h1eval.runner import measure, table
    measured=[]
    for key,r in sorted(all_rows.items()):
        base=all_rows[(r['id'],r['arm'],'none')]['output'] if r['mode']!='none' else None
        r={**r,'item_set':manifest['name'],'measurements':measure(r['output'],by_id[r['id']],base)}
        measured.append(r)
    out=Path(out)
    if out.exists() and any(out.iterdir()):raise ValueError('Merge output must be fresh')
    if export_hash(first['export'])!=binding['export_sha256']:raise ValueError('Export changed since launch')
    out.mkdir(parents=True,exist_ok=True)
    (out/'items.jsonl').write_text(''.join(json.dumps(r,allow_nan=False)+'\n' for r in measured))
    settings=dict(lineage=binding['lineage'],step=binding['step'],fixture=binding['fixture'],loader_sha256=binding['maker_sha256'])
    curve=write_curve(out,measured,manifest,first['export'],settings,32,binding['arms'],binding['modes'][1:])
    curve['dependencies'].update(reader_sha256=binding['reader_sha256'],artifact_manifest_sha256=binding['artifact_manifest_sha256'])
    curve['shards']=[str(r.resolve()) for r in roots]
    write_json(out/'curve.json',curve)
    (out/'report.md').write_text(table(measured,manifest.get('constants')))
    return dict(records=len(measured),items=len(by_id),curve=str(out/'curve.json'))


def merge_types(directories, out, items=None):
    """Merge the complete Orchard type/GPU layout, including empty shards."""
    from orchard_h10.common import ORDER
    if isinstance(directories,(str,Path)):
        directories=sorted(Path(directories).glob('*/*'))
    return merge(directories,out,items,_types=ORDER)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directories',nargs='+');p.add_argument('--out',default='h10_merged');p.add_argument('--items')
    p.add_argument('--type-layout',action='store_true');a=p.parse_args(argv)
    try:print(json.dumps((merge_types if a.type_layout else merge)(a.directories,a.out,a.items)));return 0
    except (ValueError,FileNotFoundError) as e:p.exit(2,str(e)+'\n')

if __name__=='__main__':raise SystemExit(main())
