import sys,subprocess,sqlite3,shlex,json,re,time
from pathlib import Path
from collections import Counter
import route as R
from route import ROOT,BASE,TREE,load,pin,write,rows,status
R.COMMAND=R.PREFIX+'work/audit.py'
pin(__file__);pin(ROOT/'work/route.py')
CHECK=BASE/'sb_auditfix2'
config=load(BASE/'tree_rebuild10_w/w24/out/N_LAUNCH_CONFIG.json')
from student_pilot.row_removals import Removals
for p in config['remove_files']:pin(p['path'],p['sha256'])
rem=Removals(config['remove_files'])
acc=load(ROOT/'out/EXCLUSION_ACCOUNTING.json');load(ROOT/'out/INTAKE_RESULTS.json')
files=set()
for folder in ('out/rows','out/variant_R','out/shards'):
 files.update((ROOT/folder).rglob('*.jsonl'))
files.update(Path(s['rows']['path']) for s in acc['slices'].values())
result={};bad=[]
pattern=re.compile(r'<ground\b[^>\n]*\bobj\s*=\s*(?:[\"\x27]remove[\"\x27]|remove(?=\s|>))',re.I)
def placeholder(v):
 if isinstance(v,str):return v.strip().casefold()=='remove' or bool(pattern.search(v))
 if isinstance(v,list):return any(placeholder(x) for x in v)
 if isinstance(v,dict):return any(placeholder(x) for x in v.values())
 return False
for i,p in enumerate(sorted(files)):
 source=pin(p);label=f'{i:02d}_'+p.stem+'_'+source['sha256'][:12]
 dest=ROOT/'out/audits'/label
 cmd=['nice','-n','10',R.PYTHON,'-B',str(CHECK/'store_room_audit.py'),'--store',str(p),'--tree',str(TREE),'--lists',str(CHECK/'inputs/lists'),'--out',str(dest)]
 t=time.monotonic();run=subprocess.run(cmd,capture_output=True,text=True)
 (dest/'command.log').write_text(shlex.join(cmd)+'\n'+run.stdout+run.stderr)
 report=load(dest/'audit.json');INPUT=report.get('inputs',{})
 for f,v in INPUT.items():
  # The checker records exact hashes for its own tree and list reads.
  if str(f).startswith(str(TREE)):pin(f,v['sha256'])
 k1=set()
 if (dest/'rows.sqlite').is_file():
  with sqlite3.connect((dest/'rows.sqlite').as_uri()+'?mode=ro&immutable=1',uri=True) as con:
   k1={qid for qid,hits in con.execute('SELECT row_id,hits FROM rows') if 'K1' in json.loads(hits)}
 unmatched=[];remove_labels=[];count=0
 for r in rows(p):
  count+=1
  if r['qid'] in k1 and not rem.match(r):unmatched.append(r['qid'])
  if placeholder(r):remove_labels.append(r['qid'])
 good=run.returncode==0 and report.get('complete') and not unmatched and not remove_labels and all(report.get('hits',{}).get(n)==0 for n in ['R0','dev-S1','BENCH v2','withheld-80'])
 result[str(p)]=dict(source=source,row_count=count,audit=pin(dest/'audit.json'),row_records=pin(dest/'rows.sqlite') if (dest/'rows.sqlite').is_file() else 'MISSING',hits=report.get('hits'),K1_unmatched_existing_removals=unmatched,placeholder_remove_rows=remove_labels,status='PASS' if good else 'FAIL',command=shlex.join(cmd),elapsed_seconds=time.monotonic()-t)
 if not good:bad.append(str(p))
 print(i,p.relative_to(ROOT) if p.is_relative_to(ROOT) else p,report.get('hits'),len(remove_labels),'PASS' if good else 'FAIL',flush=True)
write('out/AUDIT_RESULTS.json',dict(files=result,failures=bad,scope='Every new training row file, every shard, and every final source ran the exact sb_auditfix2 checker. Variant R and unselected intermediate files are audited but never production-admitted. K1 hits in diagnostic variants must match actual existing removal predicates. The placeholder test checks ground obj=remove and any exact remove string value.'))
status(6,f'The checker audited {len(result)} row files. Failures: {len(bad)}. Every final file, diagnostic variant and shard has recorded hashes, row counts, exclusion hits and placeholder-label results.')
