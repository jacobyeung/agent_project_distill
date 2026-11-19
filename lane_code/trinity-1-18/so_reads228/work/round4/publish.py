"""Publish the verified adapter, exact outputs and authenticated delivery manifest."""
from pathlib import Path
import hashlib,json,os,re,shutil,stat,subprocess
L=Path('/scratch/jjyeung/orch_n30/so_reads228');W=L/'work/round4';K=W/'kit';O=L/'out'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def workspace():
 total=count=0
 for base,dirs,names in os.walk(str(L),followlinks=False):
  for name in names:
   info=os.lstat(str(Path(base)/name))
   if stat.S_ISREG(info.st_mode):total+=info.st_size;count+=1
 return total,count
now=subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],universal_newlines=True).strip();print(now)
manifest=read(K/'patches/MANIFEST.json')
for name,digest in manifest['files'].items():
 assert sha(K/name)==digest and sha(W/'applied_release/read228'/name)==digest,name
assert sha(K/'patches'/manifest['patch']['path'])==manifest['patch']['sha256']
for label in ('release','patch'):
 records=read(W/'checks'/(label+'_RUNS.json'))
 assert len(records)==8 and all(r['returncode']==0 for r in records)
 assert sum(int(re.search(r'Ran (\d+) tests',r['summary']).group(1)) for r in records)==140
old=read(L/'out_round3/DELIVERY_MANIFEST.json')
for name,spec in old['files'].items():
 assert sha(L/'out_round3'/name)==spec['sha256'],name
 assert sha(O/name)==spec['sha256'],'out changed before publication: '+name
checks=K/'checks/round4';checks.mkdir(parents=True,exist_ok=True)
selected=['release_RUNS.json','patch_RUNS.json','RELEASE_PATCH_INTEGRITY.json','bootstrap_version.txt',
 'fix4_before_actual.txt','headers_debug.txt','cr2_replay.txt','cr3_replay.txt','release_patch_build.txt',
 'release_patch_integrity_driver.txt','report_generation.txt']
for label in ('release','patch'):
 selected.extend(r['output'] for r in read(W/'checks'/(label+'_RUNS.json')))
selected.extend('release_patch_command_'+str(i)+'.txt' for i in range(3))
for name in selected:shutil.copyfile(W/'checks'/name,checks/name)
for name in ('cr2_replay','cr3_replay'):shutil.copytree(W/'checks'/name,checks/name,dirs_exist_ok=True)
report=(K/'REPORT.md').read_text()
assert report.startswith('VERDICT: DONE ')
assert '## Target refusal: finding -> fix -> test' in report
assert (K/'COORDINATOR.md').read_text().split('\n',1)[1] in report
# Check report links after evidence has been copied; the final receipt is created below.
for target in re.findall(r'\]\(([^)]+)\)',report):
 if '://' not in target and not target.startswith('/') and target!='checks/round4/DELIVERY_INTEGRITY.json':
  assert (K/target).is_file(),target
before,n=workspace();assert before<2_950_000_000,(before,n)
shutil.copytree(K,O,dirs_exist_ok=True)
for name,digest in manifest['files'].items():assert sha(O/name)==digest,name
for name,spec in old['files'].items():assert sha(L/'out_round3'/name)==spec['sha256'],name
size,count=workspace();assert size<3_000_000_000,(size,count)
evidence=dict(utc=now,workspace_regular_file_bytes=size,workspace_regular_files=count,
 measurement='Sum of regular-file lstat sizes under L after publication, before this receipt and final manifest; no traversal outside L.',
 workspace_limit_bytes=3_000_000_000,direct_tests_passed=140,applied_patch_tests_passed=140,
 target_regression_cases_fail_before=21,before_assertion_failures_including_subtests=23,
 real_list_headers=115837,runtime_part_bytes=10497433600,runtime_expanded_file_bytes_from_lists=10371055588,
 round3_preserved_files=len(old['files']),base_original_files_unchanged=944,patch_files_match=True,
 patch_sha256=manifest['patch']['sha256'],actual_target_runs=0,actual_gpu_runs=0,git_calls=0,ssh_calls=0,
 standalone_timed_diagnostic=dict(exit_code=139,retried=False,evidence='headers_debug.txt'),
 bootstrap_python='/usr/bin/python3',bootstrap_version='3.6.8')
write(O/'checks/round4/DELIVERY_INTEGRITY.json',evidence)
files={}
for p in sorted(O.rglob('*')):
 if p.is_file() and p!=O/'DELIVERY_MANIFEST.json':
  assert not p.is_symlink(),p
  files[str(p.relative_to(O))]=dict(bytes=p.stat().st_size,sha256=sha(p))
write(O/'DELIVERY_MANIFEST.json',dict(schema=5,utc=now,files=files,bytes=sum(v['bytes'] for v in files.values()),
 excludes=['DELIVERY_MANIFEST.json'],reference_job='173060',step=400,run='6ed2c7aa',
 patch_sha256=manifest['patch']['sha256'],source_tree_modified=False,target_kit='/scratch/jjyeung/orch_n30/reads228/kit2'))
actual={str(p.relative_to(O)) for p in O.rglob('*') if p.is_file() and p!=O/'DELIVERY_MANIFEST.json'}
assert actual==set(files)
for name,spec in read(O/'DELIVERY_MANIFEST.json')['files'].items():
 assert (O/name).stat().st_size==spec['bytes'] and sha(O/name)==spec['sha256'],name
size2,count2=workspace();assert size2<3_000_000_000,(size2,count2)
(L/'work/STATUS.md').write_text(now+'\nDONE: Published fix4 to out/ for kit2. All six decisions are implemented. '
 '140 direct and 140 applied-patch tests pass; all 21 target regression cases fail before. '
 'Full 115837-header fixtures pass, and late unknown members refuse without runtime writes. '
 'Native control uses private_rt; real namespace fixture proves private runtime/logical binds and x exclusion. '
 'Python 3.6.8 bootstrap and sealed process guard pass. Patch preserves all 944 authenticated inputs; '
 'out_round3 preserves all 1161 shipped files. Delivery manifest verified for '+str(len(files))+' files. '
 'Workspace measured '+str(size2)+' regular-file bytes after final manifest, below 3 GB. '
 'Target stage/preparation/one-card run remain coordinator work. Standalone timed stack-dump diagnostic crashed with SIGSEGV and was not retried; both final suites pass. '
 'No Git, SSH, GPU, download, deletion, paid API or stopping of other work.\n')
print(json.dumps(dict(verdict='DONE',delivery_files=len(files),delivery_bytes=sum(v['bytes'] for v in files.values()),
 manifest_verified=True,workspace_regular_file_bytes=size2,patch_sha256=manifest['patch']['sha256']),sort_keys=True))
