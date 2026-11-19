"""CPU-only featuriser contract probe; these are synthetic tracks, not tracker outputs."""
from common import *
from ground import TrackSource,decode

def check():
 import torch
 torch.set_num_threads(8)
 from e2e_reader.geometry import from_npz
 from student_pilot.routed_features import rle,resize
 m=js(ROOT/'inputs/local/K1_MANIFEST.json');c=next(c for c in m['captures'] if c['k1_split']=='train' and c['canonical']=='scannetpp/067e2e4e61')
 key=digest(c['canonical'])[:16];folder=Path('/scratch/jjyeung/k1/run_convert_2')/key
 cache=js(folder/'candidates.json');sha(folder/'geometry.npz');geo=from_npz(folder/'geometry.npz')
 name=cache['phrases'][0];frames=[]
 for i in range(32):
  entries=cache['frames'][str(i)]['phrases'][name]['instances']
  if entries:
   e=max(entries,key=lambda e:e['score']);frames.append(dict(frame=i+1,score=e['score'],mask=rle(resize(decode(e['mask']),(80,112)))))
 source=TrackSource({name:[dict(id='synthetic_contract_probe',frames=frames)]},geo,probe=True)
 result=source(name);assert result['entries']
 selection=result['selection']['selection']
 write(ROOT/'out/TRACK_SELECTION.json',dict(status='PASS',selection=selection,synthetic=True,probe_capture=c['canonical'],reason=result['selection']['reason'],K1_tracker_numbers_read=0,policy='Frozen before K1 tracker inference; runtime featuriser failure refuses instead of changing selector'))
 return dict(status='PASS',selection=selection,synthetic=True)
if __name__=='__main__':check()
