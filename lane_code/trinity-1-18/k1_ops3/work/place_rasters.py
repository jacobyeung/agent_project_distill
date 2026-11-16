import json,hashlib,os,shutil,sys
from pathlib import Path
DRY=len(sys.argv)>1 and sys.argv[1]=='dry'
m=json.load(open('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json'))
SRC=[Path('/scratch/jjyeung/orch_n30/gt_build/out/dose_pool/out'),Path('/scratch/jjyeung/orch_n30/gt_build2/out/dose_pool/out')]
def sha(p):
  h=hashlib.sha256()
  with open(p,'rb') as f:
    for b in iter(lambda:f.read(1<<20),b''):h.update(b)
  return h.hexdigest()
rows=[];cnt={}
for c in m['captures']:
  t=Path(c['gt']['path']);pin=c['gt']['sha256'];sub=t.parent.parent.name
  srcs=[s/sub/'gt'/t.name for s in SRC if (s/sub/'gt'/t.name).exists()]
  if t.exists():
    st='present_match' if sha(t)==pin else 'present_MISMATCH_left'
  else:
    ok=[s for s in srcs if sha(s)==pin]
    if not ok: st='no_pin_equal_source'
    elif DRY: st='would_copy'
    else:
      tmp=t.with_name('.'+t.name+'.part');shutil.copyfile(ok[0],tmp)
      if sha(tmp)!=pin: st='copy_hash_FAIL';os.rename(tmp,t.with_name(t.name+'.badcopy'))
      else: os.rename(tmp,t);st='copied'
  cnt[st]=cnt.get(st,0)+1
  rows.append('\t'.join([c['canonical'],str(t),pin,st,str(srcs[0]) if srcs else '']))
out='/scratch/jjyeung/orch_n30/k1_ops3/work/RASTER_PLACEMENT'+('_DRY' if DRY else '')+'.tsv'
open(out,'w').write('canonical\ttarget\tpin\tstatus\tsource\n'+'\n'.join(rows)+'\n')
print(cnt,out)
