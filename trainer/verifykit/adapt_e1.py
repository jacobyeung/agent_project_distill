"""Convert B2's per-scene linked candidates to native-mask verification references."""
import argparse
import json
from pathlib import Path
from .io import RAW, FRAMES, cache, tower, dump, write_rows, validate, sha
from .prepare import call_counts, mdg_presence


def adapt(source, out, k=5, presence_root=None):
    source=Path(source);paths=sorted(source.glob('*.json')) if source.is_dir() else [source]
    if not paths:raise ValueError('No E1 candidate manifests')
    groups=[];pins={}
    for path in paths:
        manifest=json.loads(path.read_text())
        if 'candidates' not in manifest or 'scene' not in manifest:continue
        pins[str(path)]=sha(path);scene=manifest['scene'];raw=manifest.get('raw',str(RAW/(scene.replace('/','__')+'.npz')))
        data=cache(raw);pins[raw]=sha(raw)
        for name,candidates in sorted(manifest['candidates'].items()):
            phrase=tower().phrase(name)
            prior=mdg_presence(presence_root,scene,name) if presence_root else None
            selected=sorted(candidates,key=lambda c:(-c['features']['peak'],c['id']))[:None if k == 'all' else k]
            cs=[]
            for c in selected:
                f=c['features'];members=[]
                for p in c['proposals']:
                    slot=int(p['frame'])-1
                    raw_instances=data['frames'][str(slot)]['phrases'][phrase]['instances']
                    indexed=sorted(enumerate(raw_instances),key=lambda pair:-float(pair[1]['score']))
                    actual,instance=indexed[p['index']]
                    if abs(float(instance['score'])-p['score'])>1e-7:raise ValueError('E1 proposal index/score differs from raw cache')
                    ref=dict(path=raw,phrase=phrase,slot=slot,instance_index=actual)
                    members.append(dict(slot=slot,mask_ref=ref))
                representative=next(m for m,p in zip(members,c['proposals']) if p['frame']==f['representative_frame'] and p['index']==f['representative_index'])
                cs.append(dict(candidate_id=c['id'],**representative,peak=f['peak'],
                    presence=float(prior[representative['slot']]) if prior is not None else f['best_presence'],
                    support=f['support'],exclusivity_margin=f['exclusivity_margin'],members=members,physical_slot=c['slot']))
            g=dict(schema='verify-candidates-v1',object_id=scene+'::'+name,scene=scene,name=name,
                frame_indices=manifest['frame_indices'],frames_root=str(FRAMES),candidates=cs,
                candidate_source='E1_LINKED_TOP_K',k=k,presence_source='mdg' if prior is not None else 'E1_prior',oracle=False)
            if prior is not None:
                g['v3_slots']=sorted(range(32),key=lambda slot:(-prior[slot],slot))[:4]
                g['v3_presence_source']='mdg'
            groups.append(g)
    if not groups:raise ValueError('No E1 scene/name groups')
    write_rows(out,validate(groups));counts=call_counts(groups)
    dump(str(out)+'.meta.json',dict(source_sha256=pins,counts=counts,k=k,
        peak_definition='B2 peak: mean of the two strongest proposal joint scores, or the only proposal.',
        representative='B2 representative_frame/index: strongest joint, frame/index tie break.'))
    return counts


def main():
    p=argparse.ArgumentParser(__doc__);p.add_argument('--source',required=True);p.add_argument('--out',required=True)
    p.add_argument('--k',default='5');p.add_argument('--presence-root');a=p.parse_args()
    if a.k != 'all':
        try: a.k=int(a.k)
        except ValueError:p.error('K must be positive or all')
        if a.k<1:p.error('K must be positive or all')
    print(json.dumps(adapt(a.source,a.out,a.k,a.presence_root)))

if __name__=='__main__':main()
