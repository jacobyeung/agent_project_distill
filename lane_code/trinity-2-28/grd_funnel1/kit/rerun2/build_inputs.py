"""Local corpus -> exact call replay manifest; does not create training rows."""
import gzip
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent

def main():
    for step in (544,400):
        source=ROOT/f'work/step{step}.jsonl.gz'
        with gzip.open(source,'rt') as f:
            rows=[r for r in map(json.loads,f) if r['question_type']=='object_abs_distance']
        result=[]
        for r in rows:
            calls=[dict(call=c['call'],response=c.get('response'),served=c['served']) for c in r['arms']['tower']['tool_calls']
                   if c['family'] in ('ground','gap')]
            result.append(dict(item_id=r['item_id'],capture=r['scene'],task=r['raw']['input'],
                               source_indices=r['raw']['input']['source_frame_indices'],
                               mapping=r['raw']['mapping'],calls=calls))
        assert len(result)==len({r['item_id'] for r in result})==150
        (OUT/f'items{step}.json').write_text(json.dumps(dict(step=step,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                                                           items=result),indent=2)+'\n')
    inv=[]
    for line in (ROOT/'work/inventory_prefix.txt').read_text().splitlines():
        if '/dose_pool/out/' not in line or '/gt/' not in line:continue
        size,date,path=line.split(' ',2)
        inv.append(dict(path=path,bytes=int(size),inventory_date=date))
    scenes=sorted({r['capture'] for r in result}); records=[]
    for scene in scenes:
        dataset,name=scene.split('/')
        relative=(f'arkit_gt/gt/{name}.npz' if dataset=='arkitscenes' else f't1_gt/gt/{dataset}__{name}.npz')
        matches=[v for v in inv if v['path'].endswith('/'+relative)]
        records.append(dict(capture=scene,host='trinity-1-18',
                            path='/scratch/jjyeung/orch_cd/dose_pool/out/'+relative,
                            relative_path=relative,bytes=matches[0]['bytes'] if matches else None,
                            evidence='inventory-listed; not freshly statted' if matches else 'not listed in named GT directories',
                            matched_frames_and_instances_verified=False))
    (OUT/'gt_staging.json').write_text(json.dumps(dict(schema='gt-staging-v1',files=records,
        known_bytes=sum(r['bytes'] or 0 for r in records),known_files=sum(r['bytes'] is not None for r in records),
        inventory_prefix_bytes=4000000,inventory_total_bytes=25016605),indent=2)+'\n')
    (OUT/'gt_available.txt').write_text(''.join(r['relative_path']+'\n' for r in records if r['bytes'] is not None))
    print('manifests: 150 items per step;',sum(r['bytes'] is not None for r in records),'GT files')

if __name__=='__main__':main()
