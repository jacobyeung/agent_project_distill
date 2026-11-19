"""Locate the dry-run parity discrepancy without changing pricing geometry."""
import gzip,io,json,sys,time,resource
import numpy as np
from adapters import ROOT,READER,dependencies,reviewed_loader,load,source_hashes
from dryrun import read,write,PINS,OUT
from predicted import replay,cache_detect

def main():
    import torch
    torch.set_num_threads(8);t=time.monotonic()
    h,l,G=dependencies();loader,guard,_=reviewed_loader()
    sys.path[:0]=[str(READER),str(READER/'heads/selector')]
    from selector_head import load_head
    from e2e_reader.geometry import from_tower
    from student_pilot import camera_targets
    from student_pilot.scene_state import FrameMap
    c=json.loads(read(ROOT/'train_manifest.json'))['captures'][0];key=h.digest(c['canonical'])[:16]
    directory=READER/'heads/selector/work/run_iso'
    for ext in ('json','safetensors'):read(directory/f'selector_head.{ext}')
    head,_=load_head(directory)
    rec=json.loads(gzip.decompress(read(READER/'heads/selector/data/caps_iso/arkitscenes__41048124.json.gz')))
    folder=ROOT.__class__('/scratch/jjyeung/k1/run_tower_sam_2')/key
    with np.load(io.BytesIO(read(folder/'tower.npz'))) as z:tower={k:z[k] for k in z.files}
    receipt=json.loads(read(folder/'PHASE_COMPLETE.json'))
    raw=tower['raw_pose'][tower['anchor_slots']];R=np.array([camera_targets.rotation_from_xyzw(p[3:7]).T for p in raw]);g=np.mean(-R[:,:,1],axis=0);g/=np.linalg.norm(g)
    tablegeo=from_tower(tower['raw_pose'],tower['anchor_slots'],tower['frame_indices'],tower['depth_grid'],tower['grid_uv'],g,rec['scale'],receipt['source_hw'])
    path='/scratch/jjyeung/k1/run_convert_2/'+key+'/geometry.npz';data=read(path)
    with np.load(io.BytesIO(data)) as z:geometa={k:z[k].tolist() for k in z.files if z[k].size<20}
    with guard.capture('train_diagnosis',c['canonical']):gd=loader(path,FrameMap(tuple(c['anchor_indices'])),'tower_scaled')
    cache=json.loads(read('/scratch/jjyeung/k1/run_convert_2/'+key+'/candidates.json'))
    result=[]
    for geom,geo in [('GD',gd),('table_geometry',tablegeo)]:
        for name in ['fireplace','tv']:
            r=replay(cache,geo,head,name,rec['rows']);want=[i for i in rec['inputs'] if i['name']==name]
            with torch.no_grad():logits=head.with_null(torch.tensor([i['x'] for i in want],dtype=torch.float64),None,name).tolist()
            k=int(np.argmax(logits));expected=None if k==len(want) else want[k]['candidate_id']
            actual=None if r['null_argmax']<0 else r['accepted'][r['null_argmax']]['candidate_id']
            got={a['candidate_id']:x for a,x in zip(r['accepted'],r['x'])};shared=[i for i in want if i['candidate_id'] in got]
            result.append(dict(geometry=geom,name=name,actual=actual,expected=expected,matched=actual==expected,max_feature_error=max([float(np.max(np.abs(np.array(i['x'])-got[i['candidate_id']]))) for i in shared],default=None),got_ids=list(got),expected_ids=[i['candidate_id'] for i in want],selected_members=[] if actual is None else [p.frame-1 for p in r['tracks'][actual].proposals],table_selected_members=[] if expected is None else next(x['members'] for x in rec['rows'] if x['candidate_id']==expected)))
    PINS.update(source_hashes());write(OUT/'REPLAY_DIAGNOSIS.json',dict(rows=result,gd_metadata=geometa,table_scale=rec['scale'],table_gravity=g,seconds=time.monotonic()-t,peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024))
    for r in result:print({k:v for k,v in r.items() if k not in ['table_selected_members','got_ids','expected_ids']})
if __name__=='__main__':main()
