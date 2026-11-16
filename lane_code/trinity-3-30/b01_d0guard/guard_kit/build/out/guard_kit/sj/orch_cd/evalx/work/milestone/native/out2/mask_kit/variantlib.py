"""Frozen, label-free experiment settings and cache extension contract."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import copy,json,hashlib
WORK=Path(__file__).resolve().parent
BASE=dict(joint_floor=.2,cap=10,prompts='P0 only',mask_threshold=.5,resolution=1008,dtype='bf16',link_instance_floor=.3)
SPECS={
 'baseline':dict(mode='reuse',floor=.2,cap=10,link_floor=.3),
 'dense':dict(mode='dense',floor=.05,cap=30,link_floor=.3),
 'dense_link05':dict(mode='dense',floor=.05,cap=30,link_floor=.05),
 'aliases':dict(mode='aliases',floor=.2,cap=10,link_floor=.3),
 'tiles':dict(mode='tiles',floor=.05,cap=10,link_floor=.3,max_slots=4),
 'dense_aliases':dict(mode='dense_aliases',floor=.05,cap=30,link_floor=.3),
 'dense_tiles':dict(mode='dense_tiles',floor=.05,cap=10,link_floor=.3,max_slots=4),
 'student_tiles':dict(mode='student_tiles',floor=.05,cap=10,link_floor=.3,max_slots=4,p_yes_threshold=.5),
}
# Frozen language-only dictionary. No held-out annotation or label enters prompt construction.
ALIASES={'counter':['kitchen counter'],'ceiling light':['ceiling lamp','light fixture'],'heater':['radiator','space heater'],'coat hanger':['coat rack','clothes hanger'],'chair':['seat'],'office chair':['chair','desk chair'],'armchair':['chair','arm chair'],'table':['desk'],'coffee table':['table','cocktail table'],'dining table':['table'],'sofa':['couch'],'couch':['sofa'],'tv':['television'],'television':['tv'],'refrigerator':['fridge'],'fridge':['refrigerator'],'cabinet':['cupboard'],'kitchen cabinet':['cabinet','cupboard'],'bookshelf':['bookcase','shelf'],'shelf':['shelving'],'trash can':['waste bin','bin'],'trash bin':['trash can','bin'],'bed':['bed frame'],'lamp':['light'],'floor lamp':['lamp'],'monitor':['computer monitor'],'sink':['washbasin'],'bathtub':['bath tub'],'stool':['seat'],'nightstand':['bedside table'],'picture':['wall picture'],'whiteboard':['white board']}

def aliases(ph):
 return sorted(set(ALIASES.get(ph,[]))-{ph})

def contract(spec):
 return dict(BASE,joint_floor=spec['floor'],cap=100 if spec['mode'] in ('dense_aliases','dense_tiles') else 70 if spec['mode'] in ('aliases','tiles','student_tiles') else spec['cap'],prompts=spec['mode'],link_instance_floor=spec['link_floor'])

COMBOS=('dense_aliases','dense_tiles')
# Inference code a combo pins: the dense source must have run with the same bytes, and the combo runs with them.
CODE=('variant_cache.py','cache_masks.py','kitlib.py','variantlib.py','vendor/sam_backend.py','vendor/sam3_tower.py','vendor/phrase.py','vendor/stub_backend.py')
DENSE_KEYS={'manifest_sha256','complete_sha256','binding_sha256','npz_sha256','code_sha256','receipt_sha256','checkpoint_sha256','baseline_cache_sha256','contract','stub'}

def _sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def code_pins():return {n:_sha(WORK/n) for n in CODE}

def dense_source(candidates):
 """Pin a completed dense run: its manifest, completion and binding receipts, every NPZ, code, SAM receipt and checkpoint."""
 d=Path(candidates);mp=d.parent/'MANIFEST.json';sm=json.loads(mp.read_text());msha=_sha(mp)
 complete=json.loads((d/'COMPLETE.json').read_text());binding=json.loads((d/'BINDING.json').read_text())
 if sm.get('schema')!='mask-recall-variant-v1' or sm['experiment']['name']!='dense':raise ValueError('Dense source is not a dense variant')
 if complete['manifest_sha256']!=msha or binding.get('manifest_sha256')!=msha or complete['captures']!=len(sm['captures']):raise ValueError('Dense source incomplete or bound to another manifest')
 if not binding.get('code_sha256'):raise ValueError('Dense source binding lacks code pins')
 return dict(manifest_sha256=msha,complete_sha256=_sha(d/'COMPLETE.json'),binding_sha256=_sha(d/'BINDING.json'),npz_sha256={c['scene']:_sha(d/(c['scene'].replace('/','__')+'.npz')) for c in sm['captures']},code_sha256=binding['code_sha256'],receipt_sha256=sm['receipt_sha256'],checkpoint_sha256=sm['checkpoint_sha256'],baseline_cache_sha256=sm['experiment']['baseline_cache_sha256'],contract=sm['density'],stub=binding['stub'])

def make_manifest(base,name,base_sha,baseline_pins,presence_sha=None,dense=None):
 spec=SPECS[name];m=copy.deepcopy(base)
 if name=='baseline':return m
 m['schema']='mask-recall-variant-v1';m['density']=contract(spec);m['experiment']=dict(name=name,spec=spec,baseline_manifest_sha256=base_sha,baseline_cache_sha256=baseline_pins,presence_sha256=presence_sha,prompt_expansions={ph:aliases(ph) for c in base['captures'] for ph in c['phrases']})
 if name in COMBOS:
  if dense is None:raise ValueError('Combo manifest requires a pinned dense source')
  if (dense['receipt_sha256'],dense['checkpoint_sha256'])!=(base['receipt_sha256'],base['checkpoint_sha256']):raise ValueError('Dense source SAM receipt/checkpoint differs')
  if dense['baseline_cache_sha256']!=baseline_pins:raise ValueError('Dense source baseline pins differ')
  if dense['contract']!=contract(SPECS['dense']) or set(dense['npz_sha256'])!={c['scene'] for c in base['captures']}:raise ValueError('Dense source contract/captures differ')
  if dense['code_sha256']!=code_pins():raise ValueError('Dense source ran with other inference code')
  m['experiment'].update(dense_source=dense,inference_code_sha256=code_pins())
 for c in m['captures']:c['cache_contract']=m['density']
 return m

def check_manifest(m):
 if m['schema']=='devs1-mask-manifest-v1':return m['density']==BASE
 if m['schema']!='mask-recall-variant-v1':return False
 e=m['experiment'];n=e['name']
 ok=n in SPECS and e['spec']==SPECS[n] and m['density']==contract(SPECS[n]) and all(c.get('cache_contract')==m['density'] for c in m['captures']) and e['prompt_expansions']=={ph:aliases(ph) for c in m['captures'] for ph in c['phrases']}
 if ok and n in COMBOS:
  d=e.get('dense_source')
  ok=isinstance(d,dict) and set(d)==DENSE_KEYS and set(d['npz_sha256'])=={c['scene'] for c in m['captures']} and d['contract']==contract(SPECS['dense']) and d['baseline_cache_sha256']==e['baseline_cache_sha256'] and (d['receipt_sha256'],d['checkpoint_sha256'])==(m['receipt_sha256'],m['checkpoint_sha256']) and isinstance(e.get('inference_code_sha256'),dict) and set(e['inference_code_sha256'])==set(CODE) and d['code_sha256']==e['inference_code_sha256']
 return ok

def selected_slots(raw,phrase,spec,presence=None,scene=None):
 absent=[k for k in range(32) if not raw['frames'][str(k)]['phrases'][phrase]['instances']]
 if spec['mode']=='student_tiles':
  absent=[k for k in absent if presence[scene,phrase,k]>spec['p_yes_threshold']]
  key=lambda k:(-presence[scene,phrase,k],k)
 else:key=lambda k:(-raw['frames'][str(k)]['phrases'][phrase]['presence'],k)
 return sorted(absent,key=key)[:spec['max_slots']]

def tile_boxes(hw):
 h,w=hw;th,tw=round(h*.6),round(w*.6)
 return [(x,y,x+tw,y+th) for y in (0,h-th) for x in (0,w-tw)]
