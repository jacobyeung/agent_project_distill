from pathlib import Path
import ast,datetime,difflib,hashlib,json,os,re,sys,tarfile
if '--g5' in sys.argv:
    import runpy
    runpy.run_path(str(Path(__file__).with_name('g5_seal.py')),run_name='__main__')
    raise SystemExit(0)
if '--g4' in sys.argv:
 import runpy
 runpy.run_path(str(Path(__file__).with_name('g4_seal.py')),run_name='__main__')
 raise SystemExit(0)
if '--g3' in sys.argv:
 import runpy
 runpy.run_path(str(Path(__file__).with_name('g3_seal.py')),run_name='__main__')
 raise SystemExit(0)
B=Path(__file__).resolve().parents[1];O=B/'out';K=O/'guard_kit';W=B.parents[1]/'work';OLD=B.parent/'build/out'
sys.path.insert(0,str(K));from guard_core import read,write,sha,digest
sources=[]
for root,label in [(W/'c8r_code','C8r'),(OLD/'guard_kit/reviewed','reviewed')]:
 for p in sorted(root.rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(root);target=K/rel if label=='C8r' else K/'reviewed'/rel
  sources.append(dict(source=str(p),file=str(target.relative_to(B)),sha256=sha(p),current_sha256=sha(target),equal=p.read_bytes()==target.read_bytes(),scope=label))
if not all(x['equal'] for x in sources):raise ValueError('Inherited source differs')
write(O/'SOURCE_IDENTITY.json',dict(status='PASS',files=sources,all_equal=True))
archives=[]
for filename,root in [('code_g2.tar',K),('inputs_g2.tar',O/'inputs')]:
 dest=O/filename;members={}
 with tarfile.open(dest,'w',dereference=True) as tar:
  for p in sorted(root.rglob('*')):
   if not p.is_file():continue
   if p.is_symlink():raise ValueError('Package source has a link')
   name=str(p.relative_to(root));m=tarfile.TarInfo(name);m.size=p.stat().st_size;m.mode=0o755 if p.suffix=='.sh' else 0o644
   with p.open('rb') as inp:tar.addfile(m,inp)
   members[name]=dict(bytes=p.stat().st_size,sha256=sha(p))
 from transport import regular_tar
 regular_tar(dest)
 result=dict(file=str(dest.relative_to(B)),sha256=sha(dest),bytes=dest.stat().st_size,members=members,
             hard_links=0,regular_only=True,deterministic_metadata=True)
 write(O/('CODE_MANIFEST.json' if filename.startswith('code') else 'INPUT_MANIFEST.json'),result);archives.append(result)
# Report immutable source checks and all executed test-suite totals.
suites=[]
for name,filename in [('C8r','C8R_TESTS.json'),('G2','G2_TESTS.json'),('processes','PROCESS_TESTS.json'),('returns','RETURN_TESTS.json'),('report','REPORT_TESTS.json')]:
 r=read(O/filename);suites.append(dict(name=name,path='out/'+filename,tests=r['tests'],failures=r['failures'],errors=r['errors']))
for name,filename in [('G1','g1_tests_02.log'),('stager','stage_tests.log')]:
 text=(O/filename).read_text();n=int(re.search(r'Ran (\d+) tests',text)[1]);suites.append(dict(name=name,path='out/'+filename,tests=n,failures=0 if '\nOK\n' in text else 1,errors=0))
write(O/'TESTS.json',dict(status='PASS' if all(not r['failures'] and not r['errors'] for r in suites) else 'FAIL',
    tests=sum(r['tests'] for r in suites),suites=suites,metadata='out/RESTORATION_TEST.json',
    tensor_fixture='out/rehearsal/whole/TENSOR_CHECKS.json',process_fixture='out/PROCESS_TEST.json',
    whole_worker='out/rehearsal/whole/sandbox/RESULT.json',mutants='out/MUTANTS.json'))
blockers=[dict(id='naming',status='OPEN',description='Runtime item keys, signed metadata paths and trainer members still expose prohibited names.',evidence='out/NAMING.json'),
 dict(id='whole_worker',status='OPEN',description='Namespace-dependent worker path has not executed; the runnable fixture also uses pre-staged assets and allocation/model boundaries, so a transport-only full-packet rehearsal remains unproven.',evidence='out/rehearsal/whole/sandbox/RESULT.json'),
 dict(id='production_review',status='OPEN',description='New coordinator, single-arm admission and checker namespace adapter need independent review and live runtime validation.',evidence='out/DIFF.md'),
 dict(id='candidate_authority',status='WAITING_FOR_OPERATOR',description='Each production milestone needs its own closure, completed export, matching review and exact ORCH GO.',evidence='out/RUN.md')]
write(O/'RELEASE_BLOCKERS.json',dict(status='NOT_READY',production_packet_authorized=False,blockers=blockers,
    g1_blocker_status={'1':'CLOSED_FOR_REAL_METADATA; actual tensor restore remains in-job',
                       '2':'IMPLEMENTED_AND_COMPONENT_TESTED; not validated end-to-end',
                       '3':'OPEN; outer archive aliases and projections only',
                       '4':'OPERATOR_COMMAND_DELIVERED; namespace run blocked'},
    not_checked=['Real candidate export weights','GPU restore/parity/token identity','Whole-worker execution',
                 'Orchard allocation and resource admission','Live GCS generations/credentials and publication',
                 'Live result-pool state','Installed ossh/governor CLI','Complete runtime naming migration']))
sizing=read(OLD/'SIZING.json');sizing.update(candidate_metadata_bytes=(O/'candidate_m50/metadata.tar').stat().st_size,
    code_archive_bytes=(O/'code_g2.tar').stat().st_size,input_archive_bytes=(O/'inputs_g2.tar').stat().st_size,
    publication_reserve_seconds=300,source='Read-only G1 sizing derived from accepted return; no live throughput measurement',
    source_file=str(OLD/'SIZING.json'))
write(O/'SIZING.json',sizing)
(O/'SIZING.md').write_text('''# Time and storage

The requested limit is `05:00:00` (`SIZING.json`, `FAMILY.json`). The inherited measured estimate needs 12259.5 seconds with 4290.8 seconds of margin (`SIZING.json`; original measurements are listed in its `sources`). The coordinator reserves 300 seconds for publication (`guard_kit/worker.py`). Candidate duration and live transfer rates remain unmeasured.

The estimate covers shared staging, both exports, both geometry preparations, historical proof and the candidate arm. Canary rows are reused. It uses measured native item times rather than assuming that removing the scripted arm halves model time (`SIZING.json`).

The provisional job disk estimate is 250290030222 bytes (`SIZING.json`). The unchanged stager also requires its free-space reserve before copying (`guard_kit/sj/orch_cd/evalx/work/milestone/orchard_stage.py`). Actual candidate `.done` bytes must replace the reference-size assumption before launch; a larger export can invalidate the estimate.

Cloud publication has bounded subprocess deadlines, and a failed cloud attempt retains the verified result-pool copy (`guard_kit/transport.py`). The receipt acknowledgement cannot wait indefinitely for cloud publication. The reserve is provisional; live pool latency and archive compression time remain unmeasured.

Local archive sizes are recorded in `CODE_MANIFEST.json`, `INPUT_MANIFEST.json`, and `candidate_m50/CLOSURE.json`. The local build cap is 6000000000 bytes, and measured use is recorded in `BUILD_SIZE.json`. No large runtime, base-model or real export archive was expanded in this build.
''')
# Measure only the owned build tree; no shared filesystem inventory.
files=[p for p in B.rglob('*') if p.is_file() and not p.is_symlink()]
size=sum(p.stat().st_size for p in files)
if size>6_000_000_000:raise ValueError('Build cap exceeded')
write(O/'BUILD_SIZE.json',dict(bytes=size,files=len(files),limit_bytes=6_000_000_000,within_cap=True,root=str(B)))
print(json.dumps(dict(tests=sum(r['tests'] for r in suites),build_bytes=size,code_sha256=archives[0]['sha256'])))
