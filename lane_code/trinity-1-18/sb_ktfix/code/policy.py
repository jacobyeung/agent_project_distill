"""Pinned populations and durable one-look controls. No official-item reader exists."""
from common import *

ROWSETS=ROOT/'inputs/K1_ROWSETS'

def lines(name):
 p=ROWSETS/name;expected=read_json(ROOT/'inputs/V2_SOURCES.json')['input_sha256'][str(p)]
 assert sha(p)==expected
 xs=p.read_text().splitlines()
 assert len(xs)==len(set(xs));return set(xs)

def capture_ids(split):
 return lines('K1_CAPTURES_TRAIN_239.txt' if split=='train' else 'K1_CAPTURES_HELDOUT_57.txt')

def row_ids(split):
 return lines('K1_TRAIN_1037.txt' if split=='train' else 'K1_HELDOUT_216.txt')

def captures(split=None):
 allowed=capture_ids('train')|capture_ids('heldout') if split is None else capture_ids(split)
 result=[c for c in manifest()['captures'] if c['canonical'] in allowed]
 assert {c['canonical'] for c in result}==allowed
 return result

def numbering():
 checks=[]
 for c in captures():
  slots=c['anchor_slots'];dense=c['dense_frames'];frames=c['model_row']['student_input']['frames']
  assert len(dense)==64 and len(slots)==len(frames)==32
  assert all(0<=a<b<64 for a,b in zip(slots,slots[1:])),c['canonical']
  assert all(dense[s]['sha256']==f['sha256'] for s,f in zip(slots,frames)),c['canonical']
  assert [dense[s]['index'] for s in slots]==c['anchor_indices']
  checks.append(c['canonical'])
 return dict(status='PASS',captures=len(checks),train=len(capture_ids('train')),heldout=len(capture_ids('heldout')),frame_sha256_assertions=32*len(checks),scope='Manifest hashes only; held-out values unopened')

def consume_once(path,receipt):
 """Create before opening protected data. A crash consumes the look."""
 path=Path(path).resolve();assert path.is_relative_to(ROOT)
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x') as f:json.dump(dict(receipt,input_sha256=dict(INPUTS)),f,sort_keys=True)

def read_r0dev_once(category,path):
 frozen=ROOT/'configs/PRIMARY_ARMS.json';d=read_json(frozen)
 if d.get('status')!='FROZEN' or d.get('selection_split')!='K1_train':raise ValueError('PRIMARY_ARMS.json must be frozen on K1 train before R0-dev')
 arm=d['categories'][category]
 if len(arm)!=2 or arm[0]==arm[1]:raise ValueError('Exactly one baseline/treatment comparison per category')
 if not category.replace('_','').isalnum():raise ValueError('invalid category')
 p=local(path)
 if p.name not in d['input_files']:raise ValueError('Unbound R0-dev input')
 consume_once(ROOT/'out/looks'/('R0dev_'+category+'.json'),dict(category=category,arms=arm,primary_sha256=sha(frozen)))
 data=read_json(p)
 if INPUTS[str(p)]!=d['input_files'][p.name]:raise ValueError('R0-dev hash mismatch')
 return data

def consume_heldout():
 d=read_json(ROOT/'out/tower_frames/DECISION.json')
 if not d.get('train_complete'):raise ValueError('Train DECISION.json must be frozen before held-out')
 consume_once(ROOT/'out/looks/HELDOUT_once.json',dict(decision_sha256=sha(ROOT/'out/tower_frames/DECISION.json')))
