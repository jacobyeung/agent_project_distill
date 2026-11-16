"""Review exact-source line evidence. Exit nonzero for any uncovered change or full tail."""
import argparse,ast,difflib,hashlib,json,sys
from collections import Counter
from pathlib import Path
B=Path(__file__).resolve().parents[2];W=B.parents[1]/'work'
sys.path[:0]=[str(W/'pyextra'),str(W/'np226')]
import coverage
from coverage.parser import PythonParser
R=B/'out/c8r/sources/sj/orch_cd/evalx/work/milestone'
LOGICAL='/scratch/jjyeung/orch_cd/evalx/work/milestone/'
REL='sj/orch_cd/evalx/work/milestone/'
OLD=B.parent/'01_c8/out/c8/sources/sj/orch_cd/evalx/work/milestone'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read_data(path):
 if not path:return {}
 path=Path(path)
 if path.suffix=='.json':
  return {k:set(v.get('executed_lines',[])) for k,v in json.loads(path.read_text()).get('files',{}).items()}
 data=coverage.CoverageData(basename=str(path));data.read()
 return {k:set(data.lines(k) or []) for k in data.measured_files()}
def mapped(name):
 if name.startswith(LOGICAL):return R/name[len(LOGICAL):]
 if name.startswith(str(R)+'/'):return Path(name)
 if '/sj/orch_cd/evalx/work/milestone/' in name:return R/name.split('/sj/orch_cd/evalx/work/milestone/',1)[1]
 if name.startswith(str(W/'tree')+'/'):return Path(name)
 return None
def source_for(path,source):
 if path.is_relative_to(R):return source/path.relative_to(R)
 return path
def normalize(raw,source):
 output={};mapping=[]
 for name,lines in raw.items():
  current=mapped(name)
  if current is None or not current.is_file():continue
  prior=source_for(current,source)
  if not prior.is_file():continue
  a=prior.read_text().splitlines();b=current.read_text().splitlines()
  remap={}
  for block in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks():
   for offset in range(block.size):remap[block.a+offset+1]=block.b+offset+1
  accepted={remap[n] for n in lines if n in remap}
  output.setdefault(str(current),set()).update(accepted)
  mapping.append(dict(recorded=name,current=str(current),source=str(prior),source_sha256=sha(prior),
    current_sha256=sha(current),executed_mapped=len(accepted),unmapped=len(lines-set(remap))))
 return output,mapping
def statements(path):
 parser=PythonParser(filename=str(path));parser.parse_source();return set(parser.statements)
def labels(path):
 tree=ast.parse(path.read_text());result={};full=set()
 for node in ast.walk(tree):
  if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
   if path.name=='native_worker.py' and node.name in ('full','prepare_full_geometry'):
    for n in range(node.lineno,node.end_lineno+1):result[n]=('other mode only','full worker path')
    if node.name=='full':full.update(range(node.lineno,node.end_lineno+1))
   if path.name=='native_worker.py' and node.name=='pilot':
    for n in range(node.lineno,node.end_lineno+1):result[n]=('other mode only','pilot worker path')
  if isinstance(node,ast.If):
   condition=ast.unparse(node.test)
   # Only classify a branch as a refusal when that branch directly raises.
   if any(isinstance(s,ast.Raise) for s in node.body):
    for s in node.body:
     for n in range(s.lineno,s.end_lineno+1):result[n]=('error/refusal branch',condition)
   if isinstance(node.test,ast.Compare) and 'mode' in condition:
    for s in node.body:
     for n in range(s.lineno,s.end_lineno+1):result.setdefault(n,('other mode only',condition))
  if isinstance(node,ast.Raise):
   for n in range(node.lineno,node.end_lineno+1):result.setdefault(n,('error/refusal branch',ast.unparse(node)))
 # These alternate profile constructors are outside this family's scaled G3T contract.
 if path.name=='geometry_profiles.py':
  for node in ast.walk(tree):
   if isinstance(node,ast.FunctionDef) and node.name=='legacy_from_heads':
    for n in range(node.lineno,node.end_lineno+1):result[n]=('tool or family not used by dev-S1','legacy depth profile; family uses scaled_g3t_depth')
 return result,full
def compact(values):
 values=sorted(values)
 if not values:return '—'
 groups=[];start=last=values[0]
 for n in values[1:]:
  if n==last+1:last=n;continue
  groups.append(str(start) if start==last else f'{start}–{last}');start=last=n
 groups.append(str(start) if start==last else f'{start}–{last}')
 return ','.join(groups)
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--pilot',required=True);p.add_argument('--full');p.add_argument('--tests',required=True)
 p.add_argument('--pilot-source',type=Path,default=R);p.add_argument('--full-source',type=Path,default=R)
 p.add_argument('--output',type=Path,default=B/'out/coverage/UNEXECUTED.md')
 a=p.parse_args()
 if not a.output.resolve().is_relative_to(B):raise ValueError('Output must stay in this build')
 data={};maps={}
 for mode,path,source in [('pilot',a.pilot,a.pilot_source),('full',a.full,a.full_source),('tests',a.tests,R)]:
  data[mode],maps[mode]=normalize(read_data(path),source)
 files={str(p) for p in R.rglob('*.py')}
 for v in data.values():files.update(v)
 changes=json.loads((B/'out/CHANGED_LINES.json').read_text())
 rows=[];uncovered_changes={};uncovered_full={};counts=Counter()
 for name in sorted(files):
  path=Path(name);executable=statements(path);label,required=labels(path)
  covered={mode:data[mode].get(name,set()) & executable for mode in data}
  united=set().union(*covered.values())
  key=REL+str(path.relative_to(R)) if path.is_relative_to(R) else None
  changed=set().union(*(set(v) for v in changes.get(key,{}).values())) & executable
  if changed-united:uncovered_changes[name]=sorted(changed-united)
  if required & executable-covered['full']:uncovered_full[name]=sorted(required & executable-covered['full'])
  for mode in ('pilot','full'):
   other='full' if mode=='pilot' else 'pilot';groups={}
   for line in sorted(executable-covered[mode]):
    category,reason=label.get(line,('UNEXPLAINED','No verified branch explanation'))
    if line in covered[other]:category,reason='other mode only','executed by '+other
    elif category=='other mode only':
     # Do not label the expected mode's own missing body as an alternate mode.
     if reason.startswith(mode+' worker') or (mode=='full' and not a.full):
      category,reason='UNEXPLAINED','Required full rehearsal absent' if mode=='full' else 'Expected mode path unexecuted'
    tested=line in covered['tests']
    groups.setdefault((category,reason,tested),[]).append(line);counts[category]+=1
   for (category,reason,tested),lines in groups.items():
    rows.append(dict(file=name,mode=mode,lines=lines,classification=category,condition=reason,test_executed=tested))
 result=dict(pilot=str(a.pilot),full=str(a.full) if a.full else None,tests=str(a.tests),
  source_mapping=maps,rows=rows,classification_counts=dict(counts),
  uncovered_changed_lines=uncovered_changes,uncovered_full_lines=uncovered_full,
  missed_changed_count=sum(map(len,uncovered_changes.values())),missed_full_count=sum(map(len,uncovered_full.values())),
  full_rehearsal_supplied=bool(a.full),passed=not uncovered_changes and not uncovered_full and bool(a.full))
 a.output.with_suffix('.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 text=['# Coverage findings','',
  'Line evidence is mapped only across identical source lines. Test execution is separate from rehearsal execution. Missing full-worker statements fail the gate even when unit tests cover them.',
  '', '| File | Mode | Missed lines | Classification | Condition | Test executed |','|---|---|---|---|---|---|']
 for r in rows:
  text.append('| `'+r['file']+'` | '+r['mode']+' | '+compact(r['lines'])+' | '+r['classification']+' | '+r['condition'].replace('|','\\|').replace('\n',' ')+' | '+str(r['test_executed'])+' |')
 a.output.write_text('\n'.join(text)+'\n')
 summary={k:result[k] for k in ('passed','missed_changed_count','missed_full_count','full_rehearsal_supplied','classification_counts')}
 summary['record']=str(a.output.with_suffix('.json'));print(json.dumps(summary))
 return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
