"""Copy the reference camera rows (mode none) verbatim from authenticated returns into ref/."""
import hashlib,json
from pathlib import Path

KIT=Path(__file__).resolve().parent
O3=Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3')
H10=Path('/scratch/jjyeung/orch_n30/sb_ownread/work/h10own_170631')
CAMERA=(0,1,2)
SOURCES=dict(
 tower200=dict(job=172744,step=200,arm='tower',rule='candidates_argmax',package=str(O3/'A4'),
               journals=O3/'A4/ret/metadata/reads/0/metadata/journals'),
 tower544=dict(job=171253,step=544,arm='tower',rule='null_argmax',package=str(O3/'bases/b1'),
               journals=O3/'bases/b1/work/ret/metadata/reads/0/metadata/journals'),
 own544=dict(job=170631,step=544,arm='own',rule=None,package='/scratch/jjyeung/orch_n30/h10_stage/work/k330/kit',
             journals=H10/'metadata/journals',archive='/scratch/jjyeung/orch_n30/h10_stage/work/results/170631/result.tar.gz'))

def sha(b):return hashlib.sha256(b).hexdigest()

def main():
 out=KIT/'ref';out.mkdir(exist_ok=True);record={}
 for name,s in SOURCES.items():
  lines=[];journals=[]
  for t in CAMERA:
   p=s['journals']/str(t)/'0/items.jsonl';raw=p.read_bytes()
   journals.append(dict(path=str(p),sha256=sha(raw)))
   for line in raw.decode().splitlines():
    r=json.loads(line)
    if r['arm']==s['arm'] and r['mode']=='none':lines.append(line)
  data=('\n'.join(lines)+'\n').encode();(out/f'{name}.jsonl').write_bytes(data)
  env=json.loads((s['journals']/'0/0/environment.json').read_text())
  record[name]=dict({k:v for k,v in s.items() if k!='journals'},rows=len(lines),sha256=sha(data),source_journals=journals,
                    binding={k:env['binding'].get(k) for k in ('arms','step','lineage','stage1_select_rule','settings_sha256','reader_sha256',
                      'parity_code_sha256','evaluator_code_sha256','maker_sha256','artifact_manifest_sha256','export_sha256',
                      'items_sha256','item_set_sha256','perception_memo','perception_memo_modules','perception_memo_verify_ids','save_own_depth')})
  if name=='tower200':record[name]['settings']=env['settings']
 (out/'REFS.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
 print(json.dumps({k:dict(rows=v['rows'],sha256=v['sha256']) for k,v in record.items()}))

if __name__=='__main__':main()
