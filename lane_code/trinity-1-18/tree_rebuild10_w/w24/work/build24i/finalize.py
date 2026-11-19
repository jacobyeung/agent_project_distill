from pathlib import Path
import ast,datetime,gzip,hashlib,io,json,sys,tarfile
L=Path(__file__).resolve().parents[2];D=L/'work/build24i'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1')]
import joblib as J
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from launch_r1.build import verify
base=J.load(D/'BASELINE.json');tree=inventory(L/'work/tree_r1');assert tree==base['tree']
tree_sha=digest(tree);assert tree_sha=='57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7'
for n,h in base['packages'].items():assert J.sha(L/'out'/n)==h
kits={n:L/('out/kit_n_go' if n=='n_go' else 'work/build24/kits/'+n) for n in ('q','n','n_go')}
seals={};changes={}
for n,k in kits.items():
 seals[n]=verify(k);current={str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file()}
 changes[n]=[f for f in sorted(set(current)|set(base['kits'][n])) if current.get(f)!=base['kits'][n].get(f)]
 assert J.load(k/'k/a.json')['GO']==(n=='n_go')
 assert 'review' not in J.load(k/'k/a.json')
 if n!='q':assert J.load(k/'k/a.json')['review_wait_seconds']==7200
 assert J.load(D/('SCAN_'+n+'.json'))['status']=='PASS'
 assert J.load(D/('SCAN_'+n+'.json'))['kit_seal']==seals[n]
 for cfg in ('k/c.json','k/c0.json','k/n.json','k/p.json','k/r.json','k/h.json'):
  assert current[cfg]==base['kits'][n][cfg]
assert changes['q']==[]
expected=['BUILD.json','SHA256SUMS.txt','b/h.py','b/rv.py','b/sr.py','b/z.py','k/a.json','k/j.json']
assert changes['n']==changes['n_go']==expected,changes
for name in expected[2:]:
 if name!='k/a.json':assert J.sha(kits['n']/name)==J.sha(kits['n_go']/name)
for name in ('identities','export_identity','metadata_closure','receipt600','checkpoint600','bound400','resolve','resolve600'):
 old=ast.parse((L/'attic/build24i/work/build24/kits/n/b/z.py').read_text());new=ast.parse((kits['n']/'b/z.py').read_text())
 node=lambda x:next(n for n in x.body if isinstance(n,ast.FunctionDef) and n.name==name)
 assert ast.dump(node(old))==ast.dump(node(new))
for name in ('REVIEW_TESTS','REVIEW_FINAL_COPY_TESTS','EVIDENCE_TESTS','RETAINED_EVIDENCE','PREP_FIELDS_TESTS','SECURITY_TESTS','ARM_TESTS','COPIER_TESTS','COPIER_GO_TESTS','SIGNAL_FINAL_TESTS','SESSION_TESTS'):
 assert J.load(D/(name+'.json'))['status']=='PASS',name
for name in ('LIVE_TESTS','RUNTIME_TESTS'):assert J.load(D/(name+'.json'))['passed']
for name in ('KIT_TESTS','NAMING_TESTS','RESOLVER_TESTS'):assert J.load(D/(name+'.json'))['successful']
for name in ('SUITES','VALIDATION'):assert all(v['returncode']==0 for v in J.load(D/(name+'.json')))
sequence=J.load(D/'SEQUENCE.json');assert set(sequence)=={'q','n'}
for n,v in sequence.items():
 assert v['status']=='BOUNDARY' and v['kit_bytes_unchanged']
 assert v['production_kit_seal']==seals[n]
 assert v['first_refusal'].startswith('ValueError: Missing or changed pinned input: /scratch/fsw/')
up=J.load(L/'out/UPLOADS_24I.json');assert up['total_files']==8
for r in up['files']:assert J.sha(r['local_path'])==r['sha256']
assert not (L/'out/kit_n_go_armed').exists() and not (L/'out/UPLOADS_ARMED.json').exists()
J.write(D/'INVARIANTS.json',dict(status='PASS',tree_sha256=tree_sha,tree_files=len(tree),changed_kit_files=changes,kits=seals,existing_packages_unchanged=True,configs_unchanged=True,resolver_identity_functions_unchanged=True,production_GO=False,production_host_receipt=False,production_review=False,production_admission='BLOCKED',excluded_rehearsal_paths_untouched=True,tests_use_synthetic_receipts_only=True))
rate=J.load(D/'EVIDENCE_RUNTIME.json');review=J.load(D/'REVIEW_TESTS.json');retained=J.load(D/'RETAINED_EVIDENCE.json')
card=[
'Vehicle N uses MINIMAL. Normal kits have GO=false; the GO template is not uploaded. Production remains blocked by the missing host-receipt producer (PRODUCTION_BLOCKERS.md).',
'Init is P\'s step-400 export 5083243c from run 6ed2c7aa through its authenticated export-only receipt. Nothing after P\'s step 400 initializes N.',
'Tree: `'+tree_sha+'`.',
'Kit n: `'+seals['n']+'`; kit q: `'+seals['q']+'`.',
'GO template: `'+seals['n_go']+'`. Seals and deltas: work/build24i/INVARIANTS.json and UPLOADS_24I_GO.json.',
'N requests advanced, four GPUs/four ranks, one launcher, 48 CPUs, 800G and 24:00:00. Slurm signals the batch shell with TERM 600 seconds before the limit.',
'TK_JOB_START records allocation-start epoch seconds and reaches bwrap, torchrun and train(). Shell preparation limits are 48; native admission and review evidence use 8 threads.',
'The job runs its own mode-q canary and room audit. h.py requires a genuine matching host result at Q_NS/p/host.json, then pins it and writes Q_NS/v.json.',
'Before training, both GO variants publish v.json (at most 50 MB), identity.txt, and evidence to <n_root>/o/<jobid>/live/. The identity comes from the sealed tree in the job view.',
'Evidence names are e0.json (pose), e1.json (VQA), e2.json (routing), e3.json (pointing), e4.json (d.py rooms.json bytes), and e5.json (its sha256 and size). Their combined cap is under 2 MB.',
'Each stream file reports every opened database hash, admitted count, question-type counts, full-store empty-reasoning and recorded trace-form counts, and 40 deterministic rows with frames, indices and timestamps omitted.',
'The native readers are carrier_c1_run.Rows.row and c1_pose_mix.PoseMix/RowSource. Samples use random.Random(20261119).sample over sorted admitted native row IDs.',
'Reasoning comes from the explicit reasoning field or target/suffix <think> body. Trace forms use routing.form, form, or answer_form; absent form metadata is reported as not_recorded.',
'Any nonzero answer-only count refuses R1_ANSWER_ONLY_ROWS before WAITING_REVIEW. The retained fixture refuses for 16,000 pose and 8,000 pointing rows; no production census is claimed.',
'The 79,971-row fixture took '+str(round(retained['elapsed_seconds'],1))+' seconds and produced '+str(retained['evidence_bytes'])+' bytes. Linear full-store estimate: about 6.1 minutes for at most 555,756 source rows; host timing is unmeasured (work/build24i/EVIDENCE_RUNTIME.json).',
'WAITING_REVIEW.json contains utc, identity, v_sha256 and deadline_utc. The wait is 120 minutes (k/a.json review_wait_seconds=7200), polling every 30 seconds; expected independent review time is 15–20 minutes.',
'n_review1 writes <n_root>/n_r/review.json. The directory must be owned by the job user and mode 0700; the file must be regular, non-symlink, owned by that user and mode 0600.',
'The JSON requires verdict PASS and config_identity equal to live/identity.txt. All additional fields belong under evidence. Missing files remain pending; unusable files, FAIL, wrong identity and timeout refuse.',
'Acceptance copies the receipt to Q_NS/p/rv.json, pins its sha256 as r1_training.review, synchronizes the preparation receipt pins, and writes REVIEW_ACCEPTED.json {utc,identity,review_sha256} before t.py.',
'Refusal writes REVIEW_REFUSED.json with utc, identity and refusal. No training starts; the final copier still runs. TERM/USR1 interrupts the review helper and follows the same cleanup path.',
'out/arm_go.py takes no review argument and emits only the three-file GO delta. Review is never embedded in k/a.json. Arming, independent review and orchestrator launch GO are separate.',
'PREP_FIELDS.json/.md list 33 exact preparation paths; prep_diff.py pre.json v.json rejects all others. N_IDENTITY.txt identifies only the localised input, not the prepared production config.',
'After verification, the batch shell copies log tails, metrics, attempt/run metadata, marker hashes and .steps every 600 seconds and at exit; each copy is capped at 50 MB with at most 40 MB of log tails.',
'Exports occur at steps 100, 200, 400, 600, 800, 1000 and at stop; a separate copier checks them every 10 seconds. SESSION_NAMES_24F.json fixes their unchanged four-part GCS object names and three once-claimed stop generations.',
'The copier reads <n_root>/n_s/sess.json (owner-private directory 0700; regular non-symlink file 0600). Missing/unusable sessions leave archives local with a named status; no credential is supplied.',
'Checkpoints occur at step 1, every 7,200 seconds and at stop. Timed checkpoints remain local; the final completed stop checkpoint goes to <n_root>/n_ck/<jobid>/ if size plus 50 GiB is free, otherwise GCS is attempted or a local-only marker remains.',
'Signal cleanup allows 420 seconds for the workload, 10 for copier shutdown and 155 for publication, leaving 15 of the 600-second warning. No KillWait grace is assumed; large-transfer completion is unproven.',
'Accepted loss: node loss between exports restarts the leg from the last export with a fresh optimizer. Small-file GCS mirroring awaits the orchestrator\'s credential ruling.',
'The declaration is r1_training.routing_slices=deferred_first_boundary; init_policy=step400_export_weights_fresh_v1. N starts a fresh optimizer, counter and schedule; its first 200 steps are local steps 1–200.',
'N keeps P\'s regenerated S1 routing base (receipt ca0616db, database 4e8e6c04); all six deferred routing cells contain zero new rows. Distance calls, unit conversions and camera wording receive no targeted new examples.',
'VQA adds 7,971 direction twins and removes 109 named-route matches (107 newly removed), leaving 55,808 direction and 8,562 route-planning rows (work/build24/CENSUS.json).',
'Held-out wording exclusions, K1 and room rules remain active; routing_opener_init=keep and the step-544 lineage stay pinned. Two absent head slots remain NOT_PRESENT; seven other slots remain DEFERRED and block official reads.',
'Relative-count rows, answer-prior weights, the frame-host alias and step-time patches wait for the first boundary. N has no tower-scale freeze; H3 can fire again at the first look.'
]
p=L/'out/N_CARD_KIT_ROWS.md';old=L/'attic/build24i/out/N_CARD_KIT_ROWS.md';old.parent.mkdir(parents=True,exist_ok=True)
if not old.exists():p.rename(old)
assert len(card)<40;p.write_text('\n'.join(card)+'\n')
report=[
'BUILD24I PACKAGED; production launch remains BLOCKED. No upload, launch or production review occurred.',
'The tree is byte-identical: '+tree_sha+' across '+str(len(tree))+' files. Existing packages are unchanged (work/build24i/INVARIANTS.json).',
'Kit n: '+seals['n']+'; kit q: '+seals['q']+'.',
'GO template: '+seals['n_go']+'. GO remains false in normal kits; q is byte-identical.',
'h.py pins the real host receipt and writes v.json; rv.py publishes the prepared config and sealed-tree identity in the job view, independent of GO.',
'The helper publishes e0–e5 before WAITING_REVIEW, then polls the owner-private n_r/review.json every 30 seconds for 7,200 seconds.',
'PASS plus the exact prepared identity pins a job-private snapshot and writes REVIEW_ACCEPTED; identity, verdict, mode, symlink and timeout failures write REVIEW_REFUSED before t.py.',
'TERM/USR1 reaches the waiting helper; the real batch trap waits for its exit and runs the final copier. Training-worker signal/export tests also pass.',
'The decoded h/rv/t shell segment passes delayed-review and refusal tests with both GO settings; the tests stop at t.py, with no training (REVIEW_TESTS.json).',
'The 24h before-control refuses R1_REVIEW_RECEIPT_MISSING before publication. Additional malformed receipt, ownership, directory symlink and 50-MB config-cap controls pass (SECURITY_TESTS.json).',
'Evidence uses native Rows.row and PoseMix/RowSource, checks the whole admitted store, and samples 40 sorted native IDs with seed 20261119; frame metadata is omitted.',
'The retained fixture scanned 79,971 rows in '+str(round(retained['elapsed_seconds'],2))+' s; evidence totals '+str(retained['evidence_bytes'])+' bytes. Deterministic samples and one injected answer-only row pass (EVIDENCE_TESTS.json).',
'The literal all-stream policy refuses the retained fixture: pose 16,000 and pointing 8,000 answer-only rows; VQA/routing zero (RETAINED_EVIDENCE.json). No source row was changed.',
'The source-count bound is 555,756 rows; the fixture-rate estimate is 6.1 minutes, not a measured host runtime (EVIDENCE_RUNTIME.json). Review is expected to take 15–20 minutes.',
'PREP_FIELDS.json/.md derive 33 exact allowed leaf paths from the producers. prep_diff.py rejects unexpected fields and a learning-rate mutation (PREP_FIELDS_TESTS.json).',
'The raw 24f rehearsal comparison correctly rejects four fixture-only admission/authorization leaves; a separate copy without those gates passes. The excluded rehearsal files were not written.',
'arm_go.py requires no review and stages none; its tested GO delta has three files. The independent receipt arrives at the fixed runtime path (ARM_TESTS.json; REVIEW_SCHEMA.md).',
'Decoded q/n/GO scans and kit/naming/resolver/guard/live/runtime/session/copier suites pass. Standard-library helper statement coverage is recorded without a total-coverage claim (COVERAGE.json).',
'Both hidden-path look-aheads pass the room audit and stop at the same unavailable production-store pin; h.py, review and training are not reached there (SEQUENCE.json).',
'BLOCKER: sealed production_proof.run() never calls frame_host(); h.py still requires Q_NS/p/host.json. No production host PASS was synthesized (PRODUCTION_BLOCKERS.md).',
'The config, removals, admission, opener rows, lineage, resolver identity functions and DEFERRED boundary are unchanged. Preparation receipts only synchronize the identity-excluded receipt pins.',
'UPLOADS_24I contains '+str(up['total_files'])+' files and '+str(up['total_bytes'])+' bytes, diffed after 24h; stream root work/build24i/upload. The GO delta remains unauthorized.',
'Completed generated fixtures use reversible gzip and retained shared blobs; COMPRESSED_FIXTURES.json and DEDUP_FIXTURES.json preserve their hashes and names. No deletion occurred.',
'Evidence names without a prefix are under work/build24i. DELIVERY_24I.json records the verified package hash and member count.'
]
assert len(report)<30;(L/'out/BUILD24I_REPORT.md').write_text('\n'.join(report)+'\n')
selected={}
def add(p):
 if p.is_file() and not p.is_symlink():selected[str(p.relative_to(L))]=p
for n in tree:add(L/'work/tree_r1'/n)
for k in kits.values():
 for p in k.rglob('*'):add(p)
for root in (D/'upload',D/'scanners',D/'retained_evidence',D/'evidence_a'):
 for p in root.rglob('*'):add(p)
for p in D.iterdir():
 if p.is_file() and p.suffix in ('.py','.sh','.json','.log') and p.name not in ('PACKAGE_MANIFEST.json','package.log'):add(p)
for folder in ('guard_q','guard_n'):
 for p in (D/folder).glob('*.json'):add(p)
for n in ('prep_diff.py','PREP_FIELDS.json','PREP_FIELDS.md','arm_go.py','N_PRODUCTION_CONFIG.json','N_IDENTITY.txt','REVIEW_SCHEMA.md','PRODUCTION_BLOCKERS.md','UPLOADS_24I.json','UPLOADS_24I.list','UPLOADS_24I_GO.json','BUILD24I_REPORT.md','N_CARD_KIT_ROWS.md','SESSION_NAMES_24F.json','DELIVERY_24H.json','TREE_SEAL.json','TREE_FILES.sha256'):add(L/'out'/n)
for n in ('work/build24/joblib.py','work/build21/environment21f.py'):add(L/n)
manifest={n:dict(bytes=p.stat().st_size,sha256=J.sha(p)) for n,p in sorted(selected.items())}
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
bd=J.load(L/'out/DELIVERY_24H.json')
record=dict(schema='build24i-overlay-v1',package_seal=seal,base=dict(path=bd['package'],sha256=bd['sha256']),files=manifest,tree_sha256=tree_sha,kits=seals,production_admission='BLOCKED')
J.write(D/'PACKAGE_MANIFEST.json',record);add(D/'PACKAGE_MANIFEST.json')
target=L/'out'/('tree_rebuild_b24i_'+seal[:8]+'.tar');seen={}
with target.open('xb') as f,gzip.GzipFile(filename='',fileobj=f,mode='wb',mtime=0) as z,tarfile.open(fileobj=z,mode='w|') as t:
 for n,p in sorted(selected.items()):
  raw=p.read_bytes();info=tarfile.TarInfo(n);info.mode=0o755 if p.stat().st_mode & 0o111 else 0o644
  h=hashlib.sha256(raw).hexdigest()
  if h in seen:info.type=tarfile.LNKTYPE;info.linkname=seen[h];t.addfile(info)
  else:seen[h]=n;info.size=len(raw);t.addfile(info,io.BytesIO(raw))
expected={n:J.sha(p) for n,p in selected.items()}
with tarfile.open(target) as t:assert {m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest() for m in t}==expected
J.write(L/'out/DELIVERY_24I.json',dict(status='PACKAGED_BLOCKED',package=str(target.relative_to(L)),bytes=target.stat().st_size,sha256=J.sha(target),package_seal=seal,verified_members=len(selected),base=record['base'],tree=dict(tree_sha256=tree_sha,files=len(tree)),kits=seals,GO=False,production_host_receipt=False,production_review=False,production_admission='BLOCKED',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),uploads=dict(files=up['total_files'],bytes=up['total_bytes']),checks='PASS',rehearsal='UNTOUCHED'))
print(json.dumps(J.load(L/'out/DELIVERY_24I.json'),indent=2))
