"""Merge complete unperturbed tower shards into a deterministic answer/trace return.

Run metadata and measured timings stay in PROVENANCE.json. The tar contains the
exact semantic record values in canonical JSON, never runtime telemetry.
"""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile

from .atomic_journal import AtomicJournal, atomic_write, scene_selected

TELEMETRY = ('seconds', 'timings', 'audit', 'perception_memo', 'read_cache', 'read_profile')


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()


def semantic(row):
    out = dict(row['output'])
    audit = out.get('audit')
    if audit and audit.get('violations'):raise ValueError('Cannot accept an audit violation')
    for field in TELEMETRY:out.pop(field,None)
    result = {k:v for k,v in row.items() if k != 'seconds'}
    result['output'] = out
    return result


def merge(manifest, roots, output, *, types=None, public_codec=None):
    wire=None
    if public_codec is not None:
        from a9 import PublicJSON
        wire=PublicJSON(public_codec)
    def encode(value):
        if wire is None:return canonical(value)
        return (wire.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()
    items = manifest['items']
    expected_items = [r for r in items if types is None or r['question_type'] in types]
    expected = {(r['id'],'tower','none') for r in expected_items}
    if len(expected) != len(expected_items):raise ValueError('Duplicate expected IDs')
    by_id={r['id']:r for r in expected_items}
    common=None;found={};evidence=[];shard_count=None
    seen_bindings=set()
    for root in map(Path,roots):
        env=(wire.loads if wire else json.loads)((root/'environment.json').read_text());binding=env['binding']
        if binding.get('journal_mode') != 'atomic-items-v1':raise ValueError('Merge requires atomic journals')
        if binding['item_set_sha256'] != manifest['item_set_sha256']:raise ValueError('Item-set binding differs')
        if binding['arms'] != ['tower'] or binding['modes'] != [{'name':'none'}]:
            raise ValueError('Merge supports only unperturbed tower reads')
        index,count=map(int,binding['shard'].split('/'))
        if count<1 or not 0<=index<count:raise ValueError('Invalid shard')
        if shard_count is None:shard_count=count
        if count!=shard_count:raise ValueError('Shard counts differ')
        identity={k:v for k,v in binding.items() if k not in ('shard','ids','types')}
        if common is None:common=identity
        if identity!=common:raise ValueError('Shard export/settings/source bindings differ')
        assigned=(scene_selected(items,index,count) if binding.get('shard_strategy')=='scene-count-v1'
                  else items[index::count])
        assigned_ids={r['id'] for r in assigned}
        ids=binding['ids']
        if len(set(ids))!=len(ids) or not set(ids)<=assigned_ids:raise ValueError('Wrong shard membership')
        if binding.get('types') is not None:
            typed={r['id'] for r in assigned if r['question_type'] in binding['types']}
            if set(ids)!=typed:raise ValueError('Wrong type membership')
        bkey=str(root.resolve())
        if bkey in seen_bindings:raise ValueError('Repeated journal directory')
        seen_bindings.add(bkey)
        # Read only immutable committed files; never repair another worker's projection.
        journal=object.__new__(AtomicJournal);journal.root=root;journal.directory=root/'committed'
        from . import atomic_journal as implementation
        original_json=implementation.json
        try:
            if wire is not None:implementation.json=wire
            rows=journal.read()
        finally:implementation.json=original_json
        if {r['id'] for r in rows} != set(ids):raise ValueError('Shard is incomplete')
        for row in rows:
            key=(row['id'],row['arm'],row['mode'])
            if key not in expected:raise ValueError('Unexpected item in return')
            if key in found:raise ValueError('Duplicate item across shards')
            item=by_id[row['id']]
            if row['type']!=item['question_type'] or row['room_key']!=item['room_key']:
                raise ValueError('Row type/room differs from manifest')
            found[key]=semantic(row)
        evidence.append(dict(root=str(root),environment=env,
                             seconds=[dict(id=r['id'],seconds=r['seconds']) for r in rows]))
    if set(found)!=expected:raise ValueError('Merged return is missing items')
    ordered=[found[(r['id'],'tower','none')] for r in expected_items]
    semantic_raw=b''.join(map(canonical,ordered))
    raw=b''.join(map(encode,ordered))
    header=encode(dict(schema='read-answer-trace-return-v1',items=len(ordered),
                          item_set_sha256=manifest['item_set_sha256'],
                          items_sha256=hashlib.sha256(semantic_raw).hexdigest()))
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    atomic_write(out/'items.jsonl',raw)
    atomic_write(out/'MANIFEST.json',header)
    atomic_write(out/'PROVENANCE.json',encode(dict(binding=common,journals=evidence)))
    buf=io.BytesIO()
    with gzip.GzipFile(fileobj=buf,mode='wb',mtime=0,filename='') as gz:
        with tarfile.open(fileobj=gz,mode='w',format=tarfile.USTAR_FORMAT) as archive:
            for name,data in (('MANIFEST.json',header),('items.jsonl',raw)):
                entry=tarfile.TarInfo(name);entry.size=len(data);entry.mode=0o600;entry.mtime=0
                archive.addfile(entry,io.BytesIO(data))
    atomic_write(out/'answer_trace_return.tgz',buf.getvalue())
    return dict(items=len(ordered),sha256=hashlib.sha256(buf.getvalue()).hexdigest())


def main():
    p=argparse.ArgumentParser();p.add_argument('--items',required=True)
    p.add_argument('--out',required=True);p.add_argument('--types')
    p.add_argument('journals',nargs='+');a=p.parse_args()
    from h1eval.items import load_manifest
    print(json.dumps(merge(load_manifest(a.items),a.journals,a.out,
                           types=a.types.split(',') if a.types else None),sort_keys=True))


if __name__=='__main__':main()
