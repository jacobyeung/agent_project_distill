"""Train-only StageOne parity, with stored isolated raw-name table choices."""
import gzip, json, sys, time, resource
import numpy as np
from adapters import ROOT, READER, dependencies, reviewed_loader, source_hashes
from dryrun import read, write, PINS, OUT
from predicted import replay

def run(c, geo, head):
    import torch
    slug=c['canonical'].replace('/','__')
    tables={kind:json.loads(gzip.decompress(read(READER/f'heads/selector/data/{kind}/{slug}.json.gz'))) for kind in ('caps_raw','caps_iso')}
    import hashlib
    key=hashlib.sha256(json.dumps(c['canonical'],sort_keys=True,allow_nan=False).encode()).hexdigest()[:16]
    cache=json.loads(read('/scratch/jjyeung/k1/run_convert_2/'+key+'/candidates.json'))
    result=[];states={}
    for name in sorted({i['name'] for i in tables['caps_iso']['inputs']}):
        t=time.monotonic();r=replay(cache,geo,head,name,tables['caps_raw']['rows']);states[name]=r
        inputs=[i for i in tables['caps_iso']['inputs'] if i['name']==name]
        with torch.no_grad(): k=int(torch.argmax(head.with_null(torch.tensor([i['x'] for i in inputs],dtype=torch.float64),None,name)))
        expected=None if k==len(inputs) else inputs[k]['candidate_id']
        got=None if r['null_argmax']<0 else r['accepted'][r['null_argmax']]['candidate_id']
        result.append(dict(capture=c['canonical'],name=name,got=got,expected=expected,passed=got==expected,seconds=time.monotonic()-t))
        print('REPLAY',c['canonical'],name,got==expected,round(time.monotonic()-t,2),flush=True)
    return result,states,tables

def main():
    import torch
    torch.set_num_threads(8)
    t=time.monotonic();h,l,G=dependencies();loader,guard,_=reviewed_loader()
    sys.path.insert(0,str(ROOT/'vendor'))
    from selector_head import load_head
    from student_pilot.scene_state import FrameMap
    directory=READER/'heads/selector/work/run_iso'
    for suffix in ('json','safetensors'):read(directory/f'selector_head.{suffix}')
    head,_=load_head(directory)
    cs=json.loads(read(ROOT/'train_manifest.json'))['captures']
    selected=[next(c for c in cs if c['canonical'].startswith(ds+'/') and any(r['type']=='object_abs_distance' for r in c['rows'])) for ds in ('arkitscenes','scannetpp')]
    result=[]
    for c in selected:
        path='/scratch/jjyeung/k1/run_convert_2/'+h.digest(c['canonical'])[:16]+'/geometry.npz';read(path)
        with guard.capture('train_parity',c['canonical']):geo=loader(path,FrameMap(tuple(c['anchor_indices'])),'tower_scaled')
        rows,_,_=run(c,geo,head);result+=rows
    PINS.update(source_hashes());matched=sum(r['passed'] for r in result)
    write(OUT/'REPLAY_CHECK.json',dict(rows=result,matched=matched,total=len(result),rate=matched/len(result),passed=matched/len(result)>=.95,seconds=time.monotonic()-t,peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024))
if __name__=='__main__':main()
