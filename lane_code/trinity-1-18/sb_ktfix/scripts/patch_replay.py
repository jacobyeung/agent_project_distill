from pathlib import Path
p=Path('code/replay.py');s=p.read_text()
s=s.replace("return S()", "return S()")
s=s.replace("class S(Session):\n  def __init__",'''class Provider(MinAreaBoxProvider):
  def __call__(self,name,obj,geometry,best):
   if '_dense_box' in obj:return obj['_dense_box']
   return super().__call__(name,obj,geometry,best)
 class S(Session):
  def __init__''')
s=s.replace('box_provider=MinAreaBoxProvider())','box_provider=Provider())')
s=s.replace("r=dict(r,instance_id=e['instance_id'],first=int(min(members)))\n    if anchor_slots is not None:r['printed_anchor_frames']=printed_frames(members,anchor_slots)",'''r=dict(r,instance_id=e['instance_id'],first=min(r['frames']))
    if anchor_slots is not None:
     mapping={int(slot)+1:i+1 for i,slot in enumerate(anchor_slots)}
     shared=[f for f in r['frames'] if f in mapping]
     if not shared:continue
     dense_best=min(r['visible'],key=lambda f:(-r['areas'][str(f)],f))
     if dense_best not in r['frames']:continue
     box=MinAreaBoxProvider()(name,r,geometry,dense_best)
     r=dict(r,_dense_box=box,frames=[mapping[f] for f in shared],visible=[mapping[f] for f in shared],
       areas={str(mapping[f]):r['areas'][str(f)] for f in shared},points={},first=min(mapping[f] for f in shared))''')
s=s.replace("min_member_frames=min(map(len,members))))", "min_member_frames=min(map(len,members)),box_records=copy.deepcopy(session.box_registry.records),box_bindings=copy.deepcopy(session.box_registry.bindings),names=names))")
start=s.index('\ndef fused_flagged_socket(')
s=s[:start]+'''
def flagged_row(base,dense):
 """Use each operand's dense box iff its baseline printed response has <3 frames."""
 from trace_format.box_v313 import Registry
 registry=Registry();chosen=[]
 for name,btext,dtext in zip(base['names'],base['ground'],dense['ground'],strict=True):
  m=re.search(r': frames ([0-9,]+)',btext)
  count=len(m[1].split(',')) if m else 0
  source=dense if count<3 else base
  labels=source['box_bindings'].get(name,[])
  if not labels:registry.invalidate(name);chosen.append(count<3);continue
  record=source['box_records'][labels[0]]
  from trace_format.box_v313 import serialize
  text=serialize(name,'B'+str(len(registry.records)+1),record['frames'],record['best'],record['value'])
  registry.ingest(text,record['value']);chosen.append(count<3)
 text,_=registry.gap(base['names'][0],[base['names'][1]],'box_grid_5cm')
 match=re.fullmatch(r'distance ([0-9]+\\.[0-9]{2}) m',text)
 return dict(base,response=text,prediction=float(match[1]) if match else None,dense_operands=chosen)
'''
s=s.replace('from trace_format.box_v313 import Registry','from trace_format.box_v313 import BoxRegistry as Registry')
p.write_text(s)
