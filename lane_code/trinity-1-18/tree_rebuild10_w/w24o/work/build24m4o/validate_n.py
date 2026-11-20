from common import *
import copy,shutil
from launch_r1.build import verify
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
base=J.load(D/'BASELINE.json')
assert digest(inventory(T))==base['tree']=='de202f58b31793608f886360a9fdfb5f58c24932e35976efcf74acead62e3cfe'
seals={n:verify(kit(n)) for n in NAMES}
current={n:{str(p.relative_to(kit(n))):dict(sha256=J.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in kit(n).rglob('*') if p.is_file()} for n in NAMES}
for n in ('q','n','n_go'):
 assert seals[n]==base['kits'][n] and current[n]==base['files'][n],n
changed=[p for p in sorted(current['qd'].keys()|base['files']['qd'].keys()) if current['qd'].get(p)!=base['files']['qd'].get(p)]
assert changed==['BUILD.json','SHA256SUMS.txt','b/a.py','b/f0.py'],changed
assert J.load(kit('qd')/'k/a.json')['GO'] is False
assert J.load(kit('qd')/'k/a.json')['discovery'] is True
for rel in ('k/c.json','k/n.json'):assert J.load(kit('qd')/rel)==J.load(kit('n')/rel)
a=L/'attic/build24m4o/out/kit_qd/b/a.py';expected=a.read_text().replace("    r=run(request,root/'q',stage=stage)","    from f0 import recording\n    with recording(kit,root.parent,os.environ['SLURM_JOB_ID']):\n     r=run(request,root/'q',stage=stage)")
assert (kit('qd')/'b/a.py').read_text()==expected
old=J.load(L/'attic/build24m4o/out/kit_qd/BUILD.json');new=J.load(kit('qd')/'BUILD.json');old['kit_sha256']=new['kit_sha256'];assert old==new
assert seals==J.load(D/'SEALS.json')
runs=J.load(D/'TEST_RUNS.json');assert len(runs)==16 and all(v['returncode']==0 for v in runs if v['name']!='scans')
remaining=J.load(D/'REMAINING_CHECKS.json');assert len(remaining)==2 and all(v['returncode']==0 for v in remaining)
for n in NAMES:
 v=J.load(D/('SCAN_'+n+'.json'));assert v['status']=='PASS' and v['kit_seal']==seals[n]
assert J.load(D/'RECORDER_TESTS.json')['status']=='PASS'
assert J.load(D/'QD_STEP1_TESTS.json')['status']=='PASS'
final=copy.deepcopy(runs)
for v in final:
 v['log']='work/build24m4o/'+v['name']+'.log'
 if v['name']=='scans':v.update(returncode=0,log='work/build24m4o/qd_scan_final.log',other_kit_evidence=['SCAN_q.json','SCAN_n.json','SCAN_n_go.json'])
J.write(D/'FINAL_TEST_RUNS.json',final)
# Only the test helper's local source/support paths differ from the delivered arming helper.
source=(L/'out/arm_routing.py').read_text().replace('L=Path(__file__).resolve().parents[1]','L=Path('+repr(str(L))+')').replace('work/build24m4m','work/build24m4o')
assert (D/'arm_fixture.py').read_text()==source
entries=[]
for name in changed:
 p=kit('qd')/name;info=current['qd'][name]
 entries.append(dict(name='qd/'+name,local_path=str(p),sha256=info['sha256'],bytes=info['bytes'],mode=format(info['mode'],'04o'),action='replace' if name in base['files']['qd'] else 'add',transfer='local-upload'))
up=dict(schema='qd-delta-v1',baseline='qd at 24m4m',baseline_kit_seals={'qd':base['kits']['qd']},kit_seals={'qd':seals['qd']},unchanged_kit_seals={n:seals[n] for n in ('q','n','n_go')},files=entries,total_files=len(entries),total_bytes=sum(r['bytes'] for r in entries),GO=False,uploaded=False)
J.write(L/'out/UPLOADS_24M4N.json',up);(L/'out/UPLOADS_24M4N.list').write_text(''.join(v['name']+'\n' for v in entries))
# Replay the exact qd delta in a fresh kit and verify its final seal.
replay=D/'delta_replay';replay.mkdir()
for n,v in base['files']['qd'].items():
 src=kit('qd')/n
 if n in changed:src=L/'attic/build24m4o/out/kit_qd'/n
 assert J.sha(src)==v['sha256']
 dst=replay/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);dst.chmod(v['mode'])
for e in entries:
 dst=replay/e['name'].split('/',1)[1]
 if dst.exists():
  backup=L/'attic/build24m4o/delta_replay'/dst.relative_to(replay);backup.parent.mkdir(parents=True,exist_ok=True);dst.rename(backup)
 shutil.copyfile(e['local_path'],dst);dst.chmod(int(e['mode'],8))
assert verify(replay)==seals['qd']
J.write(D/'UPLOAD_REPLAY.json',dict(status='PASS',baseline=base['kits']['qd'],result=seals['qd'],changed=changed))
failures=[dict(path='work/build24m4o/scans.log',output=(D/'scans.log').read_text(),resolved_by='Explicit attribute accesses and native function signatures; qd_scan_final.log passes with unchanged scanner.')]
J.write(D/'FAILURES.json',dict(status='RESOLVED',records=failures,cluster_kill=False))
v=dict(status='PASS',tree_sha256=base['tree'],kits=seals,unchanged=['tree','q','n','n_go'],qd_changed=changed,suites=final,recorder=J.load(D/'RECORDER_TESTS.json'),step1_rows=288,delta_files=len(entries),delta_bytes=up['total_bytes'],GO=False,production_executed=False,uploaded=False,launched=False,arming_fixture_scope='Delivered arming helper with only local root and support directory relocated; production helper unchanged.',retained_report_comparisons='The user explicitly requested unchanged seals and a delta against 24m4m.')
J.write(D/'VALIDATION.json',v)
lines=[f"qd {seals['qd']}; unchanged q {seals['q']}, n {seals['n']}, n_go {seals['n_go']}.",
 f"C″ remains {base['tree']}; only qd b/a.py, b/f0.py, SHA256SUMS.txt and BUILD.json differ from 24m4m.",
 'qd publishes o/<job>/live/f1.json with per-stream rows, frame counts, processor attributes, observed pixel bounds, token counts and loss/finiteness from the same processor object; no reconstruction.',
 'Four recorder fixtures pass: default and explicit bounds preserve encoded tensor bytes/audits; native failures persist, publication failure adds no refusal, and wrappers restore.',
 'All 16 kit, scan, naming, resolver, guard and arming suites pass; the native sampling fixture verifies 288 step-1 selections. qd remains GO=false and exits before training.',
 f"UPLOADS_24M4N.json/.list contain the qd-only delta against 7d358ff5: {len(entries)} files, {up['total_bytes']} bytes; replay reproduces the new seal.",
 'work/build24m4o/VALIDATION.json records checks; FAILURES.json preserves the resolved scanner failure and its exact output. Real rows, processor assets and GPU forwards were not tested.',
 'DELIVERY_24M4N.json and work/build24m4o/PACKAGE_CHECK.json identify the archive, checksum and verified members; superseded bytes remain in attic. No network, SSH, Orchard, Git, scheduler or other-agent work ran.'
]
assert len(lines)<10
(L/'out/BUILD24M4N_REPORT.md').write_text('\n'.join(lines)+'\n')
print('VALIDATED',seals,'delta',up['total_files'],up['total_bytes'],flush=True)
