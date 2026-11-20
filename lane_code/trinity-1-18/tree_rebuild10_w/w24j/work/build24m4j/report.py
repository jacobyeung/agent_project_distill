import sys,datetime,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
# The relocated helper's default base receipt remains available under its local input directory.
base=J.load(kit('q')/'k/r.json')['routing_base'];target=D/'inputs'/base['sha256']
if not target.exists():target.write_bytes(input_file(base['sha256']).read_bytes())
assert J.sha(target)==base['sha256']
p=L/'out/ARM_ROUTING_USAGE.md';s=p.read_text().replace(str(W/'w24h'),str(L)).replace('work/build24m4h','work/build24m4j')
a=s.index('Apply `UPLOADS_24M4H.json`');b=s.index('\n\n',a)
s=s[:a]+'Apply `UPLOADS_24M4I.json` against the supplied Orchard 24m4h kit state before an armed delta. `UPLOADS_24M4I.list` names the 24 local delta files. The GO delta remains separate in `UPLOADS_24M4I_GO.json`.'+s[b:]
replace(p,s)
failures=[]
for rel in ('attic/edit24i_import_failure.log','attic/dry_count_p_pretty_receipt_failure.log','attic/dry_count_p_seed_failure.log','attic/build24m4i/resolver600_first/resolver600_tests.log'):
 p=L/rel;failures.append(dict(output_file=rel,sha256=J.sha(p),output=p.read_text(),cluster_kill=False,resolved=True))
failures += [
 dict(stage='Initial capsule inspection',output='json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)',cause='k/j.json decodes to shell text, not JSON',resolution='Inspection skips non-JSON capsules; the full naming scanner separately checks shell capsules',cluster_kill=False,resolved=True),
 dict(stage='Test setup heredoc',output="sys,runpy,json,atexit: line 48: warning: here-document at line 0 delimited by end-of-file (wanted `EOF')\n/bin/bash: line 49: from: command not found\n/bin/bash: -c: line 50: syntax error near unexpected token `('\n/bin/bash: -c: line 50: `L=Path(__file__).resolve().parents[2];W=L.parent'",resolution='Preserved partial script in attic/setup_tests24i_shell_failure.py; wrote setup using a quoted heredoc without outer shell-string nesting',cluster_kill=False,resolved=True),
 dict(stage='Named source probes',output="sed: can't read w24i/work/build24m4h/finalize.py: No such file or directory\nsed: can't read w24i/work/build24m4h/run_tests.py: No such file or directory\nrg: w24i/work/tree_r1/student_pilot/type_mix*.py: No such file or directory (os error 2)\nsed: can't read w24i/work/tree_r1/student_pilot/type_mix.py: No such file or directory",resolution='Read the supplied run_suites.py/delivery_prep.py and the authenticated P tree type_mix.py',cluster_kill=False,resolved=True)
]
J.write(D/'FAILURES.json',failures)
seals=J.load(D/'SEALS.json');identities=J.load(D/'CONFIG_IDENTITIES.json');up=J.load(L/'out/UPLOADS_24M4I.json');tests=J.load(D/'TEST_RUNS.json')
assert len(tests)==16 and all(r['returncode']==0 for r in tests)
for n in NAMES:assert J.load(D/('SCAN_'+n+'.json'))['kit_seal']==seals[n]
assert J.load(D/'EXACT_CONFIG_DELTA.json')['status']=='PASS'
assert J.load(D/'INVARIANTS.json')['status']=='PASS'
assert J.load(D/'UPLOAD_RECONSTRUCTION.json')['status']=='PASS'
assert J.load(D/'NATIVE_ARM_TESTS.json')['source_seals']==seals
validation=dict(status='PASS',scope='Configured-plan dry counts, kit invariants, scans, naming/resolver/guard and arming fixtures; no production preparation or training',kits=seals,tree_sha256=J.load(D/'INVARIANTS.json')['tree_sha256'],test_suites=tests,all_b_unchanged=True,all_tree_archives_unchanged=True,case='b',room_rows_per_step=dict(P=1.7,N=1.7),draw_count_steps=200,dry_count_successful_passes=dict(P=1,N=1),P_early_failures='Both failures occurred before the sampler loop: reformatted receipt bytes, then seed lookup. Exact pinned receipts and recipe seed were used in the successful pass.',N_production_counts_available=False,N_dry_counts_basis=J.load(D/'N_DRY_COUNT.json')['counts_basis'],underlying_N_routing_type_rates_available=False,native_arming_negatives=len(J.load(D/'NATIVE_ARM_TESTS.json')['negative']),host_read_only=True,only_writable_workspace=str(L),superseded_workspace_code_execution_blocked=True,import_guard='work/build24m4j/bootstrap.py',no_cluster_kill=True,uploaded=False,launched=False,failures='work/build24m4j/FAILURES.json',default_arm_base_verified=base,style_exception='Before/after identities and retained failure output are required audit evidence for this task; inherited room_rule text is retained to obey the draw-only config delta.')
J.write(D/'VALIDATION.json',validation)
c=identities['n_go']['k/c.json']
lines=[
 'CASE b; q '+seals['q']+'; n '+seals['n']+'; n_go '+seals['n_go']+'; qd '+seals['qd']+'; kit_n_go k/c.json decoded payload sha256 '+c['payload_sha256']+'; identity '+c['after']+'.',
 'The zero room draw persisted for the whole job: r1_mix.py:24/35/90 fixes allocation; r1_population.py:202 binds indices; r1_loader.py:51/62 only audits. out/CASE_24M4I.md gives full file:line paths.',
 'ORCH 0511Z sets room_size and room_rows_per_step from 0 to 1.70 and direction from 36.866 to 35.166, preserving 128 VQA rows/step; all other card values are unchanged.',
 'Tree C remains 0c7614c8eff74201db275489af9c3fa11f3b418693a0239b793e6322685298de; every b/ file is unchanged; EXACT_CONFIG_DELTA.json verifies only draw entries and dependent identities/seals.',
 'kit_n_go config identity '+c['before']+' -> '+c['after']+'; CONFIG_IDENTITIES.json records before/after identities and payload hashes for all four kits.',
 'DRAW_TABLE_24M4I.md/.json report 31 plan families over 200 steps: P=N=340 room rows (1.70/step); N counting −0.175 and direction +0.175 follow K1 and the repeat cap.',
 'N routing_base supplies 64 rows/step; its underlying native type split remains unknown. Unexplained routing allocation differences and the six-row relative-distance census gap are marked UNATTRIBUTED.',
 'P uses authenticated native populations; N uses configured ceiling counts and explicit synthetic offsets. No production admission, native N population, frame loading or training is claimed.',
 'All 16 scan, kit, naming, resolver, guard and arming suites pass; native arm_routing checks and seven refusals pass on the new seals. ARM_ROUTING_USAGE.md uses the local runner and updated scanners.',
 'UPLOADS_24M4I.json/.list contain '+str(up['total_files'])+' files ('+str(up['total_bytes'])+' bytes), exactly against 24m4h Orchard kit state; UPLOADS_24M4I_GO.json is separate; GO is false except out/kit_n_go.',
 'FAILURES.json retains exact failure output; the resolver fixture omission is resolved. All tests mount the host read-only with only w24i writable and block imports from superseded workspaces.',
 'The inert room_rule annotation remains unchanged to honor the draw-only delta; executable draw entries govern. No SSH, network, Orchard, GPU, Git, scheduler, other agents, upload or launch ran.',
 'DELIVERY_24M4I.json and PACKAGE_CHECK.json record the full archive, checksum, member verification and storage below 25 GB.'
]
assert len(lines)<15
(L/'out/BUILD24M4I_REPORT.md').write_text('\n'.join(lines)+'\n')
print('VALIDATION PASS; report',len(lines),'lines; default arming base',base['sha256'])
