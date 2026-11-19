"""Strict checkpoint and real 8-frame tracker audit, on CPU only."""
from pathlib import Path
import json, sys, time, resource, hashlib
import numpy as np
import torch
torch.set_num_threads(8)
HERE=Path(__file__).resolve().parent
ROOT=Path('/scratch/jjyeung/orch_n30/sb_mask_carry')
sys.path.insert(0,str(ROOT/'kit_v2'))
import mc_common as C
import mc_tracker as MT
import mc_track_io as IO
import mc_track_pass as TP
C.code_pins();C.pin(__file__)
calls=[]
original=torch.nn.Module.load_state_dict
def observe(self,state_dict,*args,**kwargs):
    result=original(self,state_dict,*args,**kwargs)
    calls.append(dict(class_name=type(self).__name__,strict=kwargs.get('strict',args[0] if args else True),keys=len(state_dict),backbone_keys=sum(k.startswith('detector.backbone.') for k in state_dict),tracker_keys=sum(k.startswith('tracker.') for k in state_dict),missing=list(result.missing_keys),unexpected=list(result.unexpected_keys)))
    return result
torch.nn.Module.load_state_dict=observe
t0=time.monotonic()
tracker=MT.Sam3Carry('cpu')
capture='arkitscenes/41048124'
fs=C.frame_sets()['captures'][capture]
seeds=C.read_json(C.OUT/'seeds/SEEDS.json')
entry=next(r for r in seeds['captures'] if r['capture']==capture)
masksets=IO.load_seeds(capture)
lead=next(o for o in entry['objects'] if o['S_A0']['status']=='OK')
slots=TP.window(64,fs['A32'][lead['S_A0']['slot']-1],8)
images=tracker.frames([fs['dense'][i]['path'] for i in slots],[fs['dense'][i]['sha256'] for i in slots])
for i in slots:C.pin(fs['dense'][i]['path'])
te=time.monotonic();cache,hw=tracker.embed(images);embed=time.monotonic()-te
loc={d:j for j,d in enumerate(slots)}
records=[]
for tag in ['S_A0/D64','S_GT/D64','S_A0/A32','S_GT/A32']:
    ss,frame_set=tag.split('/')
    frames=slots if frame_set=='D64' else [i for i in fs['A32'] if i in loc]
    sub={j:cache[loc[d]] for j,d in enumerate(frames)}
    positions={d:j for j,d in enumerate(frames)}
    anchor_pos=[positions.get(d) for d in fs['A32']]
    reference=C.read_json(C.OUT/'dry/track_cpu'/tag.replace('/','_')/(C.stub(capture)+'.json.gz'))
    for o in entry['objects']:
        seed=o[ss]
        if seed['status']!='OK' or anchor_pos[seed['slot']-1] is None:continue
        mask=masksets[f"{ss}_{o['k']}"]
        ts=time.monotonic();result=tracker.track(sub,anchor_pos[seed['slot']-1],mask);elapsed=time.monotonic()-ts
        rec=IO.object_record(o['k'],o['name'],o['instance'],seed['slot'],frames,anchor_pos,result,mask)
        ref=next(x for x in reference['objects'] if x['name']==o['name'])
        added=[a for a in rec['anchors'] if a['carried'] and not a['seed']]
        records.append(dict(tag=tag,name=o['name'],frames=len(frames),seconds=elapsed,added=len(added),changed_from_seed=sum(not np.array_equal(C.rle_decode(a['rle']),mask) for a in added),all_anchor_masks_equal_original=all(a['rle']==b['rle'] for a,b in zip(rec['anchors'],ref['anchors'])),anchors=rec['anchors']))
modules=[str(Path(m.__file__).resolve()) for m in list(sys.modules.values()) if getattr(m,'__file__',None)]
old_imports=[p for p in modules if p.startswith(str(ROOT/'kit')+'/') or p.startswith(str(ROOT/'tests')+'/')]
result=dict(command='bash review_run.sh sam3 model_audit.py',device='cpu',threads=torch.get_num_threads(),checkpoint_sha256=C.PINS[str(C.CHECKPOINT)],load_state_dict_calls=calls,model=type(tracker.model).__name__,tracker=type(tracker.tracker).__name__,shims=tracker.shims,load_seconds=tracker.load_seconds,embed_seconds=embed,seconds=time.monotonic()-t0,peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20,modules_outside_scratch=tracker.outside,superseded_imports=old_imports,records=records,input_sha256=C.all_pins())
(HERE/'MODEL_AUDIT.json').write_text(json.dumps(C.clean(result),indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('records','input_sha256')},indent=2))
print(json.dumps([{k:v for k,v in r.items() if k!='anchors'} for r in records],indent=2))
(HERE/'STATUS.md').write_text('The strict checkpoint and real CPU tracker audit is complete. MODEL_AUDIT.json records checkpoint coverage, carried-mask comparisons, timings, source hashes, and import locations. The launcher and phrase contract still require fixes before a GPU pass.\n')
