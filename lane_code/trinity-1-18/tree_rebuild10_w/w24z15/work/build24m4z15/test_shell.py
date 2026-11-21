import json,os,re,subprocess,sys
from pathlib import Path
J=Path.cwd();D=J/'work/build24m4z15';F=D/'shell';F.mkdir();B=F/'bin';B.mkdir()
shim=F/'shim.py';shim.write_text('''import json,os,subprocess,sys,time
from pathlib import Path
args=sys.argv[1:]
while args and args[0] in ('-I','-s','-B'):args.pop(0)
if args[0]=='-':
 if os.environ.get('MIRROR_FAIL')=='1':sys.exit(73)
 os.execv(sys.executable,[sys.executable,'-I','-s','-B',*args])
p=Path(args[0]);a=args[1:];F=Path(os.environ['FIXTURE'])
if p.name=='j8.py':
 if a[0]=='b':print(F/'bin/bw');sys.exit(0)
 if a[0]=='p':
  node=Path(a[1]);assert 'work exit '+os.environ['WORK_RC'] in (node/'j2.log').read_text()
  if os.environ.get('MIRROR_FAIL')!='1':
   state=json.loads((Path(a[2]+'_live')/'live.json').read_bytes());assert state['phase']=='final'
  os.execv(sys.executable,[sys.executable,'-I','-s','-B',str(p),*a])
if p.name in ('j2.py','v.py'):sys.exit(0)
if p.name=='resolve.py':
 Path(a[a.index('--output')+1]).write_text('{}');sys.exit(0)
if p.name=='l.py':sys.stdout.write(sys.stdin.read());sys.exit(0)
if p.name=='x.py':
 node=Path(a[2]);(node/'ev').mkdir(exist_ok=True)
 (node/'ev/q.log').write_bytes(b'q'*300000+b'END')
 (node/'ev/q.steps').write_text('done')
 (node/'ev/large').write_bytes(os.urandom(3600000))
 (node/'p/q/b').mkdir(parents=True);(node/'p/q/b/receipt.json').write_text('{"ok":true}')
 time.sleep(.15);sys.exit(int(os.environ['WORK_RC']))
if p.name=='dbb3.py':sys.exit(1)
raise AssertionError(args)
''')
(B/'python3').write_text('#!/bin/bash\nexec '+sys.executable+' -I -s -B '+str(shim)+' "$@"\n')
(B/'sleep').write_text('#!/bin/bash\nexec /usr/bin/sleep .02\n')
(B/'bw').write_text('#!/bin/bash\nexec /bin/bash "${@: -1}"\n')
for p in B.iterdir():p.chmod(0o755)
s=(J/'out/jd8.sh').read_text();results=[]
for name,rc,dead in [('normal',7,False),('dead_failure',7,True),('dead_success',0,True)]:
 f=F/name;f.mkdir();X=f/'x';X.mkdir();tmp=f/'tmp';tmp.mkdir();K=X/'qp_11386117';(K/'b').mkdir(parents=True)
 (K/'BUILD.json').write_bytes((J/'out/kit_qdp/BUILD.json').read_bytes());(K/'b/ep.sh').write_text(':\n')
 (X/'j8.py').write_bytes((J/'out/j8.py').read_bytes());(X/'rdiff.py').write_text('')
 script=f/'jd8.sh'
 text=s.replace('/project/community/jjyeung/okh7/x_22c714e1',str(X)).replace('O="$X/o/${SLURM_JOB_ID}"','O="$X/o/${SLURM_JOB_ID}"\nif [[ "${J7_INNER:-0}" == 1 ]]; then O="$N/ev"; fi')
 if dead:
  start=text.index('j8_loop() (');end=text.index('\nmkdir -p "$N"',start)
  text=text[:start]+'j8_loop() ( exit 73 )'+text[end:]
 script.write_text(text)
 for suffix in ('log','err'):(tmp/('q_22c714e1_123.'+suffix)).write_text('S'+suffix)
 env={**os.environ,'PATH':str(B)+':'+os.environ['PATH'],'FIXTURE':str(F),'WORK_RC':str(rc),'SLURM_JOB_ID':'123','SLURM_TMPDIR':str(tmp),'J7_NICE':'1','MIRROR_FAIL':str(int(dead))}
 r=subprocess.run(['bash',str(script)],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=20)
 (f/'run.log').write_text(r.stdout)
 assert r.returncode==rc,(name,r.returncode,r.stdout,(tmp/'q_22c714e1_123/j2.err').read_text())
 v=json.loads((X/'o/123/j7.json').read_bytes());assert v['returncode']==rc and v['skipped']
 assert any(row['name'].startswith('j7/e4.json') for row in v['files'])
 assert any(row['name'].startswith('j7/s.err') for row in v['files'])
 if not dead:
  live=json.loads((X/'o/123_live/live.json').read_text());assert live['phase']=='final'
 results.append(dict(case=name,work_exit=rc,wrapper_exit=r.returncode,loop_dead=dead,final_snapshot=not dead))
# Reverse exactly the allowed edits; all remaining wrapper bytes must be identical.
old=(J/'out/jd7.sh').read_text();new=s
start=new.index('# The batch shell owns this mirror');end=new.index('mkdir -p "$N"',start)
new=new[:start]+new[end:]
new=new.replace('if [[ "${J7_INNER:-0}" != 1 ]]; then j8_loop & J8_LIVE=$!; fi\n','')
new=new.replace('timeout -k 1 30 touch "$N/j8.stop" || true\nwait "$J8_LIVE" || true\nj8_snapshot final\n','')
new=new.replace(' "$rc" "${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID}.log" "${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID}.err" || rc=1',' "$rc" || rc=1')
new=new.replace('$X/j8.py','$X/j7.py')
new=re.sub(r'(?<=--job-name=a15_cot_ap)[0-9a-f]{12}',re.search(r'--job-name=a15_cot_ap([0-9a-f]{12})',old)[1],new)
assert new==old
assert re.search(r'^#SBATCH --mem=800G$',s,re.M) and s.splitlines().index('#SBATCH --mem=800G')+1==8
for p in (J/'out/jd7.sh',J/'out/jd8.sh'):subprocess.run(['bash','-n',str(p)],check=True)
result=dict(status='OK',cases=results,wrapper_scope_exact=True,syntax=True,mem_line=8,fixture_scope='Real shell and publisher; namespace, kit execution, j2, and sleeps replaced by explicit offline fixtures. No bwrap or workload run.')
(D/'SHELL_TESTS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
