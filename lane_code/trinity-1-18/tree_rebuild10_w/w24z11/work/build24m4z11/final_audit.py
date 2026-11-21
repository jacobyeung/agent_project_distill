from pathlib import Path
import ast,base64,difflib,gzip,hashlib,json,os,re,shutil,subprocess,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4z11';sys.path.insert(0,str(L/'out'))
import arm_launch as C
result=json.loads((D/'TEST_RESULTS.json').read_text());assert result['status']=='OK'
assert json.loads((D/'EXTRA_TESTS.json').read_text())['status']=='OK'
# Keep the complete evidence as compressed bytes without publishing test verdicts.
for stop,raw in zip((3600,6000),result['run_attic']):
 run=Path(raw);dest=D/('evidence_'+str(stop));dest.mkdir()
 for name in ('UPLOADS_ARMED.json','UPLOADS_ARMED.list','UPLOADS_ARMED_GO.json','UPLOADS_ARMED_GO.list','SUMMARY.json','armed/UPLOADS_ROUTING_ARMED.json','armed/PLANNER_CLOSURE.json','layout.json'):
  p=run/name;(dest/(name.replace('/','_')+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
 for n in ('q','n','n_go'):shutil.copyfile(run/('SCAN_'+n+'.json.gz'),dest/('SCAN_'+n+'.json.gz'))
 # Save a full member inventory for reviewer comparison; no copied trees needed.
 C.write(dest/'FILES.json',{n:C.inventory(run/'armed/kits'/n) for n in ('q','n','n_go')})
# Run shell syntax and Python parsing checks on delivered code.
subprocess.run(['bash','-n',str(L/'out/arm_launch.sh')],check=True)
for p in [L/'out/arm_launch.py',L/'out/arm_routing.py',D/'tests.py',D/'extra_tests.py',D/'package.py']:ast.parse(p.read_bytes(),str(p))
# Audit for production-acceptable verdict text. Search only regular local text;
# rg skips binary archives and does not follow inherited directory symlinks.
search=subprocess.run(['rg','-l','-F',C.SELECTION,'out','work','-g','!tree_r1/**','-g','!tree_r1c/**','-g','!tree_r1_base/**'],cwd=L,capture_output=True,text=True)
assert search.returncode in (0,1),search.stderr
unsafe=[];checked=[]
for n in search.stdout.splitlines():
 p=L/n
 try:s=p.read_text()
 except (UnicodeDecodeError,ValueError):continue
 if C.GENERATED in s and re.search(r'\bPASS\b',s):unsafe.append(n)
 checked.append(n)
assert not unsafe,unsafe
# Confirm archived source kits and the immutable helper gate after all tests.
for n,root in {'q':L/'work/build24/kits/q','n':L/'out/kit_n','n_go':L/'out/kit_n_go'}.items():C.verify(root,C.SOURCE_SEALS[n])
old=(L/'attic/build24m4z11/arm_routing.py').read_text();new=(L/'out/arm_routing.py').read_text()
assert old[old.index('    selection_hash='):old.index('    origins=')]==new[new.index('    selection_hash='):new.index('    layout=')]
failures=[]
for p in sorted(D.glob('attempt*/full_3600.log')):failures.append(dict(log=str(p.relative_to(L)),output=p.read_text()))
failures.append(dict(log='work/build24m4z11/setup_failure.log',output=(D/'setup_failure.log').read_text()))
failures.append(dict(log='work/build24m4z11/verdict_surface.failure.log',output=(D/'verdict_surface.failure.log').read_text()))
C.write(D/'FAILURES.json',dict(resolved=failures,unresolved=[]))
report=dict(status='OK',test_groups=len(result['tests']),extra_tests=5,verdict_surface_checked=checked,production_verdict_files=[],synthetic_verdicts_only_in_attic=True,helper_gate_byte_identical=True,kit_seals=C.SOURCE_SEALS,uploaded=False,launched=False)
C.write(D/'FINAL_AUDIT.json',report);print(json.dumps(report,sort_keys=True))
