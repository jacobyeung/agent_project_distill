import sys,ast,os,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from launch_r1.build import verify
from student_pilot.p3_provenance import digest
seals={n:verify(kit(n)) for n in NAMES};assert seals==J.load(D/'SEALS.json')
for n in NAMES:assert J.load(D/('SCAN_'+n+'.json'))['kit_seal']==seals[n]
tests=J.load(D/'TEST_RUNS.json');assert len(tests)==15 and all(r['returncode']==0 for r in tests)
for name in ('OFFLINE','INTEGRATION','NATIVE_ARM_TESTS','NATIVE_CLI','INVARIANTS','UPLOAD_RECONSTRUCTION'):
 assert J.load(D/(name+'.json'))['status']=='PASS',name
assert J.load(D/'NAMESPACE_TEST.json')['returncode']==0
assert J.load(D/'NATIVE_ARM_TESTS.json')['source_seals']==seals
assert J.load(L/'out/UPLOADS_24M4H.json')['kits']=={n:seals[n] for n in ('q','n','qd')}
# Keep the active child source as the standalone build input too.
replace(D/'rb.py',(kit('n')/'b/rb.py').read_bytes())
failures=J.load(D/'FAILURES.json')
for rel in ('attic/build24m4h/offline_attempt1.log','attic/build24m4h/offline_attempt2.log','attic/build24m4h/offline_attempt3.log','attic/build24m4h/offline_attempt4.log','attic/build24m4h/test_pass1/suites.log','attic/build24m4h/audit_attempt1.log','attic/build24m4h/namespace_project_attempt1.log'):
 p=L/rel;failures.append(dict(output_file=rel,sha256=J.sha(p),output=p.read_text(),cluster_kill=False))
failures.append(dict(stage='Named-file probes',output='sed: cannot read b/q.py: No such file or directory; sed: cannot read out/N_CARD_KIT_ROWS_24M4D.md: No such file or directory; rg: carrier_c1_model.py: No such file or directory',cluster_kill=False))
replace(D/'FAILURES.json',json.dumps(failures,sort_keys=True,indent=2)+'\n')
size=sum(p.stat().st_size for p in L.rglob('*') if p.is_file());assert size<25_000_000_000,size
incident=J.load(D/'WRITE_BOUNDARY_INCIDENT.json')
record=dict(status='PASS',kits=seals,tree_sha256=J.load(D/'INVARIANTS.json')['tree_sha256'],test_suites=tests,guard_mutations=len(J.load(D/'OFFLINE.json')['guard_mutations']),mode_guard_build_calls=[v['build_calls'] for v in J.load(D/'INTEGRATION.json')['records']],native_arm_refusals=len(J.load(D/'NATIVE_ARM_TESTS.json')['negative']),all_changed_b_identical=True,namespace_smoke='Real isolated Python/P tree in private filesystem, including /project logical input paths',production_not_exercised=['Original P archive bytes','Full P database reconstruction and 4e8e6c04 hash','Complete N preparation and routing row count','Production frame/model/row-body closure','Production admission, training and independent review'],fixture_limit='Native Pool construction and prepare require authenticated room-release list 7a910565; fixture lacks it, production row bodies and other pins listed in OFFLINE.json',write_boundary_incident='work/build24m4h/WRITE_BOUNDARY_INCIDENT.json',failures='work/build24m4h/FAILURES.json',workspace_apparent_bytes=size,workspace_cap_bytes=25_000_000_000,no_cluster_kill=True,uploaded=False,launched=False,style_exceptions=['Build identifiers, failure output and the write-boundary incident remain because the requested delivery requires reproducible provenance and failure reporting.'])
J.write(D/'VALIDATION.json',record)
up=J.load(L/'out/UPLOADS_24M4H.json')
lines=[
 'q '+seals['q']+'; n '+seals['n']+'; n_go '+seals['n_go']+'; qd '+seals['qd']+'.',
 'Tree C remains 0c7614c8eff74201db275489af9c3fa11f3b418693a0239b793e6322685298de; all changed b/ files match across the four kits.',
 'P reconstruction uses its sealed b83a8a35 tree in an isolated child, native relocation without preparation, and the complete 4e8e6c04 database-hash gate; ORCHARD_COPIES_24M4H.json binds the missing 9,963,520-byte e5be8157 archive.',
 'N keeps all 14 manifest entries and sets four source statuses to non-final; native policy evaluation matches P, including deferred SCENE_room_sppK and eligible U_Faithful, while preserving all 13 N removal entries.',
 'The kit enforces both named source refusals; 72 mutations and mode-r/mode-q checks pass before build. Native P implementation guards match all 204 entries.',
 'Full N preparation stops at missing authenticated room-release list 7a910565; production rows, frame inputs and full P database reproduction were not exercised (OFFLINE.json; BUILD24M4H_EVIDENCE.md).',
 'P retains its measured 47,898-row reference; N has no measured routing count. New input bindings change the config identity; INVARIANTS.json records both capsule identities and hashes.',
 'The kit publishes each raw materialization, receipt and refresh artifact independently under o/<job>, including partial failures; both publication fixtures pass.',
 'All 15 scan, kit, naming, resolver, guard and arming suites pass. The native arming helper authenticates receipt digest and reviewed database hash separately; seven negative cases and the unchanged native digest check pass.',
 'UPLOADS_24M4H.json/.list contain '+str(up['total_files'])+' delta names: '+str(up['local_upload_files'])+' local files ('+str(up['local_upload_bytes'])+' bytes) and one Orchard copy ('+str(up['orchard_copy_bytes'])+' bytes), against the supplied 24m4e state.',
 'GO is false except out/kit_n_go; the GO delta is separate. ARM_ROUTING_USAGE.md gives the native-receipt command, and N_CARD_KIT_ROWS_24M4H.md states the corrected routing row.',
 'An inherited test rewrote three files outside H before failing; WRITE_BOUNDARY_INCIDENT.json lists them, and k/s.json still matches its existing seal. Subsequent tests enforced a read-only host with only H writable.',
 'FAILURES.json retains exact failure output. No cluster kill, network, SSH, GPU work, Git, scheduler or other-agent operation ran; no upload or launch ran.',
 'DELIVERY_24M4H.json records the full archive, checksum, member verification and storage; VALIDATION.json distinguishes local fixture results from untested production inputs.'
]
assert len(lines)<15
(L/'out/BUILD24M4H_REPORT.md').write_text('\n'.join(lines)+'\n')
print('VALIDATION PASS',size,'apparent bytes; report',len(lines),'lines')
