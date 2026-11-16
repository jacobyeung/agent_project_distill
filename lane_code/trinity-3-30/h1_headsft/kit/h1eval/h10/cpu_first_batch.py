"""Three dev-S1 items through b04 make_real on CPU; no model loading here."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
if not __package__:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]));__package__='h1eval.h10'
from h1eval.items import load_manifest, K, sha
from h1eval.cli import modes
from h1eval.modes import applies
from .launch import reader_factory


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('export','heads','reader-root','artifact-manifest'):p.add_argument('--'+key,required=True)
    p.add_argument('--items',default=str(K/'items/devs1_routed.json'))
    p.add_argument('--mode',default='scale_scene:2');p.add_argument('--reader-entry',default='e2e_reader.real:make_real')
    a=p.parse_args(argv)
    try:
        if os.environ.get('CUDA_VISIBLE_DEVICES')!='':raise ValueError('Run through cpu.sh with CUDA hidden')
        maker=reader_factory(a.reader_root,a.reader_entry)
        manifest=load_manifest(a.items)
        if manifest['name']!='devs1_routed':raise ValueError('CPU diagnostic requires devs1_routed')
        selected=[next(r for r in manifest['items'] if r['question_type']==kind)
                  for kind in ('camera_displacement','camera_rotation','object_abs_distance')]
        head_sha=sha(a.heads);artifact=json.loads(Path(a.artifact_manifest).read_text())
        def pinned(v):
            if isinstance(v,dict):return v.get('sha256')==head_sha or any(pinned(x) for x in v.values())
            if isinstance(v,list):return any(pinned(x) for x in v)
            return False
        if not pinned(artifact):raise ValueError('--heads SHA256 is not bound in --artifact-manifest')
        perturbations=modes(a.mode)
        if len(perturbations)!=1:raise ValueError('Choose exactly one perturbation')
        from .perception_own import configured
        from h1eval.scorers import records
        for mode in [{'name':'none'},*perturbations]:
            generator=maker(Path(a.export),Path(a.artifact_manifest),selected,
                            perception_factory=configured(mode),device='cpu')
            try:
                for item in selected:
                    if not applies(mode,item):continue
                    t=time.perf_counter();output=generator(item)
                    print(json.dumps(dict(id=item['id'],type=item['question_type'],mode=mode,
                        heads_sha256=head_sha,calls=records(output),response=output['text'],
                        finish=output['finish'],seconds=time.perf_counter()-t,
                        timings=output.get('timings',{})),allow_nan=False),flush=True)
            finally:
                if callable(getattr(generator,'close',None)):generator.close()
                del generator
        return 0
    except (ValueError,FileNotFoundError,ImportError) as e:p.exit(2,str(e)+'\n')

if __name__=='__main__':raise SystemExit(main())
