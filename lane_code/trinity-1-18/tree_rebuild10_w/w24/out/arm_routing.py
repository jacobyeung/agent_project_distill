"""Bind a reviewed native routing selection to fresh local q and GO kits."""
from pathlib import Path
import sys,json,base64,hashlib,shutil,importlib.util

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: arm_routing.py reviewed-routing_selection.json')
 L=Path(__file__).resolve().parents[1]
 sys.path[:0]=[str(L/'work/build24'),str(L/'work/build24f'),str(L/'work/tree_r1'),str(L/'work/build21')]
 import joblib as J
 from kit24f import reseal
 from launch_r1.build import verify
 import environment21f as E
 from unittest.mock import patch
 source=Path(sys.argv[1]).resolve();value=J.load(source);h=J.sha(source)
 digest=value.get('regenerated_sha256')
 if not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):raise ValueError('R1_ROUTING_SELECTION_PIN_INVALID')
 if type(value.get('rows')) is not int or value['rows']<=0 or not value.get('row_id_digest') or not value.get('inputs_pinned'):raise ValueError('R1_ROUTING_SELECTION_PIN_INVALID')
 if value.get('logical_output')!='/tmp/q_22c714e1/p/q/selection':raise ValueError('R1_ROUTING_SELECTION_PATH_DIFFERS')
 destination=L/'out/kits_routing_armed';upload=L/'out/upload_routing_armed'
 if destination.exists() or upload.exists():raise ValueError('R1_ARM_OUTPUT_EXISTS')
 destination.mkdir();upload.mkdir();rows=[];seals={}
 for name,origin,scan_name in (('q',L/'work/build24/kits/q','q'),('n',L/'out/kit_n_go','n_go')):
  target=destination/name;shutil.copytree(origin,target)
  for file in ('k/h.json','k/r.json'):
   p=target/file;doc=json.loads(p.read_text());obj=J.load(p);obj['routing_selection']=dict(path='u/'+h,sha256=h)
   raw=(json.dumps(obj,sort_keys=True,indent=2)+'\n').encode();doc.update(payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest());p.write_text(json.dumps(doc))
  seals[name]=reseal(target);assert verify(target)==seals[name]
  spec=importlib.util.spec_from_file_location('armed_'+name,L/'work/build24k'/('naming24k_'+scan_name+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  with patch.object(E,'__file__',str(L/'work/build24k/scanners'/scan_name/'environment21f.py')):assert module.scan_decoded(target)['status']=='PASS'
  base=L/'work/build24/kits'/name
  for p in sorted(target.rglob('*')):
   if p.is_file() and (not (base/p.relative_to(target)).exists() or J.sha(p)!=J.sha(base/p.relative_to(target))):
    label=name+'/'+str(p.relative_to(target));out=upload/label;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
    rows.append(dict(name=label,local_path=str(out),bytes=out.stat().st_size,sha256=J.sha(out)))
 out=upload/'u'/h;out.parent.mkdir();shutil.copyfile(source,out);rows.append(dict(name='u/'+h,local_path=str(out),bytes=out.stat().st_size,sha256=h))
 J.write(L/'out/UPLOADS_ROUTING_ARMED.json',dict(files=rows,total_files=len(rows),total_bytes=sum(r['bytes'] for r in rows),stream_root=str(upload),kits=seals,
    routing_selection_sha256=h,regenerated_sha256=digest,upload_authorized=False,launch_authorized=False,review_path='<n_root>/n_r/review.json'))
 (L/'out/UPLOADS_ROUTING_ARMED.list').write_text(''.join(r['name']+'\n' for r in rows))
 print(json.dumps(dict(kits=seals,files=len(rows),uploaded=False,launched=False)))

if __name__=='__main__':main()
