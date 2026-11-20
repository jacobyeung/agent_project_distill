"""Build only datasets that independently reproduce under frozen tolerances."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from round2 import *
from concurrent.futures import ProcessPoolExecutor, as_completed

def job(dataset,cid,indices):
    start=time.monotonic();path=OUT/'gt'/relpath(dataset,cid)
    try:
        evidence=build_raw(dataset,cid,indices,path)
        return dict(built=True,path=str(path),evidence=evidence,seconds=time.monotonic()-start)
    except Exception as e:
        return dict(built=False,path=str(path),error=repr(e),seconds=time.monotonic()-start)

def main():
    assert 'PIPE_RC 0 0 0 0' in (ROOT/'stage.log').read_text()
    repro=read(OUT/'REPRODUCTION.json')
    spp=read(OUT/'REPRODUCTION_SPP.json');repro['scannetppv2']=spp
    write(OUT/'REPRODUCTION.json',repro)
    manifest={m['scene']:m for m in read(ROOT/'DEVS1_MANIFEST.json')['captures']}
    results={};futures={}
    with ProcessPoolExecutor(max_workers=4) as pool:
        for dataset,ids in TARGETS.items():
            for cid in ids:
                canonical=dataset+'/'+cid
                if not repro.get(dataset,{}).get('passed',False):
                    results[canonical]=dict(built=False,reason='dataset reference has not passed reproduction');continue
                futures[pool.submit(job,dataset,cid,manifest[canonical]['anchor_indices'])]=canonical
        for future in as_completed(futures):
            c=futures[future];results[c]=future.result()
            write(OUT/'BUILDS.json',results)
            print(c,results[c]['built'],results[c].get('error'),round(results[c].get('seconds',0),1),flush=True)
    write(OUT/'BUILDS.json',results)

if __name__=='__main__':main()
