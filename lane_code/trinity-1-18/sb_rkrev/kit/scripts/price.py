"""S3 CPU conversion and scoring of completed DA3 receipts."""
from adapter import *
import score_room_pricing as scorer
from gates import run_code_hashes
root=W/'out/room_pricing';manifest_path=W/'configs/R0DEV_ROOM_MANIFEST.json';manifest=read(manifest_path);rows=[];ins={str(manifest_path):sha(manifest_path),**input_code()}
for arm in ['da3_f32','da3_u94']:
 missing=[];arm_rows=[]
 for item in manifest['items']:
  p=root/'pred'/arm/item['scene']/'pred.npz';d=p.parent/'DONE.json'
  if not p.is_file() or not d.is_file():missing.append(item['id']);continue
  rec=read(d);assert sha(p)==rec['pred_sha256'];verify=rec['binding']
  assert verify['code_sha256']==run_code_hashes(),'stale inference code'
  assert verify['manifest_sha256']==sha(manifest_path),'stale manifest'
  expected=item['frame_indices'] if arm=='da3_f32' else item['union_indices']
  assert verify['frames']==expected and verify['item_slots']==[expected.index(i) for i in item['frame_indices']]
  ins[str(p)]=sha(p);ins[str(d)]=sha(d)
  for rule in ['R0','T10']:
   result=pipeline(p,root/'geom'/arm/(item['scene']+'.npz'),rule)
   row=dict(id=item['id'],arm=arm+'+'+rule,**result,input_sha256={str(p):sha(p),str(d):sha(d),**input_code()})
   if result.get('floor_cells'):row['supported_to_filled']=result['supported_cells']/result['floor_cells']
   arm_rows.append(row)
 if missing:
  if arm=='da3_f32':raise RuntimeError('missing primary items: '+str(missing))
  if not (root/'SECONDARY_DROPPED.json').exists():raise RuntimeError('missing secondary items without OOM drop receipt')
  continue
 rows.extend(arm_rows)
output=root/'ROOM_PRED.jsonl';output.write_text(''.join(json.dumps(r,allow_nan=False)+'\n' for r in rows))
direct=W/'evidence/direct_m200_room134.json';assert sha(direct)==BASE;ins[str(direct)]=BASE;ins[str(output)]=sha(output)
table=scorer.score(read(direct)['rows'],rows,'da3_f32+R0',5)
# Paired report-only comparison and cell-support diagnostics.
by={(r['id'],r['arm']):r for r in rows};base={r['id']:r for r in read(direct)['rows']}
if all((i['id'],'da3_u94+R0') in by for i in manifest['items']):
 pairs=[]
 for item in manifest['items']:
  ident=item['id'];b=base[ident];a=by[ident,'da3_u94+R0'];c=by[ident,'da3_f32+R0']
  pairs.append((b['room'],scorer.mra(scorer.answer(a['area_m2'],b['unit']),b['gt'])-scorer.mra(scorer.answer(c['area_m2'],b['unit']),b['gt'])))
 table['secondary_minus_primary']=scorer.bootstrap(pairs)
table['primary_median_supported_to_filled']=float(np.median([r['supported_to_filled'] for r in rows if r['arm']=='da3_f32+R0' and 'supported_to_filled' in r])) if any('supported_to_filled' in r and r['arm']=='da3_f32+R0' for r in rows) else None
table['interpretation']='PASS/FAIL evaluates this complete measurement pipeline against R0 mesh labels, not geometry quality alone.'
write(root/'PRICING_TABLE.json',table,ins);(root/'PRICING_TABLE.txt').write_text(scorer.render(table))
print(scorer.render(table))
