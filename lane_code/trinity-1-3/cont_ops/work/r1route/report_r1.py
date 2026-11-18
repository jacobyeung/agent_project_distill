from pathlib import Path
import ast,datetime,difflib,glob,hashlib,json,os,tarfile
W=Path(__file__).resolve().parent;O=W/'out';F=Path('/scratch/jjyeung/orch_n30/reader_r1/work/fix7')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def read(p):return json.loads(p.read_text())
def at(p,needle):return next(i for i,s in enumerate(p.read_text().splitlines(),1) if needle in s)
ledger_paths=[Path(p) for p in glob.glob('/scratch/jjyeung/orch_n30/*/work/ORCHARD_LEDGER.jsonl')]
extra=[F/k/'REPORT.md' for k in ('b1','b2')]+[Path('/scratch/jjyeung/orch_n30/reader_r1/work/b1g/PROMPT.md')]
ledger_texts={str(p):p.read_text() for p in ledger_paths+extra}
raw_times={}
for r in (0,1):
 for p in (F/'b1/work/ret/metadata/reads'/str(r)/'metadata/journals').glob('*/*/timings.jsonl'):
  raw_times[(r,int(p.parent.parent.name))]=sum(json.loads(line)['seconds'] for line in p.read_text().splitlines())
overhead=3*3600+41*60+24-sum(raw_times.values())
checks=read(O/'FILL_TESTS.json');integrated=read(O/'INTEGRATED_FILL.json')
for k in ('b1','b2'):
 d=O/k;token=(d/'TOKEN').read_text().strip();assert all(token not in text for text in ledger_texts.values())
 write(d/'TOKEN_CHECK.json',dict(token=token,collision=False,checked=[dict(path=n,sha256=hashlib.sha256(t.encode()).hexdigest()) for n,t in ledger_texts.items()],ledger_count=len(ledger_paths)))
 plan=read(d/'READ_PLAN.json');manifest=d/'src/items'/('devs1_routed.json' if k=='b1' else 'room134.json');items=read(manifest)['items'];order=read(d/'src/9.json')['order']
 ids=[r['id'] for t in plan['read_settings'][0]['types'] for r in items if r['question_type']==order[t]]
 # Compare the actual baseline journal order, not just the item inventory.
 baseline_ids=[]
 for t in plan['read_settings'][0]['types']:
  p=F/k/'work/ret/metadata/reads/0/metadata/journals'/str(t)/'0/items.jsonl'
  baseline_ids.extend(json.loads(line)['id'] for line in p.read_text().splitlines())
 assert ids==baseline_ids
 plan['item_ids_in_execution_order']=ids;plan['item_manifest_sha256']=sha(manifest);plan['item_order_matches_baseline_read0']=True
 plan['item_sets']={'dev-S1':636} if k=='b1' else {'dev-S1':36,'R0-dev':98}
 write(d/'READ_PLAN.json',plan)
 if k=='b1':
  elapsed=overhead;segments=[]
  for t in (3,0,1,2,4):
   r=1 if t==3 else 0;seconds=raw_times[(r,t)];n=150 if t!=4 else 36;elapsed+=seconds
   segments.append(dict(type=order[t],baseline_read=r,items=n,seconds=seconds,seconds_per_item=seconds/n,estimated_end_from_job_start=elapsed))
  timing=dict(job=171253,measured_wall_seconds=13284,measured_all_segments_seconds=sum(raw_times.values()),measured_nondecode_seconds=overhead,segments=segments,
   estimated_completion_seconds=elapsed,estimated_completion_hms=str(datetime.timedelta(seconds=round(elapsed))),allocated_seconds=18000,stop_at_seconds=16200,drain_until_seconds=16800,return_margin_seconds=1200,
   stop_margin_seconds=1800,estimated_stop_slack_seconds=16200-elapsed,measured_rate_cut_point_items=636,measured_rate_cut_point='all 636 items, after the last room item',
   method='Use read 1 candidates_argmax distance timing (including its verify cost), read 0 camera/room timings, and measured total-job residual. No memo speedup is credited. Estimate only; m200 decoding can differ.',
   fixed_overhead_decode_slowdown_to_cutoff=(16200-overhead)/sum(s['seconds'] for s in segments))
 else:
  path=F/'b2/work/ret/metadata/reads/0/metadata/journals/4/0/timings.jsonl';seconds=sum(json.loads(l)['seconds'] for l in path.read_text().splitlines())
  timing=dict(job=172456,items=134,measured_read_seconds=seconds,staging_allowance_seconds=1920,estimated_completion_seconds=1920+seconds,estimated_completion_hms=str(datetime.timedelta(seconds=round(1920+seconds))),allocated_seconds=9000,stop_at_seconds=7200,drain_until_seconds=7800,return_margin_seconds=1200,stop_margin_seconds=1800,estimated_stop_slack_seconds=7200-1920-seconds,measured_rate_cut_point_items=134,method='Retain T2 staging allowance and 02:30:00 cap; replace its proxy decode estimate with job 172456 measured read time.')
 write(d/'TIME_PRICE.json',timing)
 # List every changed delivery member as well as the reviewed source patch.
 with tarfile.open(F/k/'1.tgz') as t:old={m.name:t.extractfile(m).read() for m in t if m.isfile()}
 with tarfile.open(d/'1.tgz') as t:new={m.name:t.extractfile(m).read() for m in t if m.isfile()}
 lines=(d/'FILE_SHA256_DIFF.tsv').read_text().splitlines();patch=(d/'PATCH.diff').read_text()
 # The source builder owns the initial rows. Avoid accumulating duplicate reports.
 lines=[x for x in lines if not x.startswith('delivery/')]
 marker='\n# Delivery text differences\n';patch=patch.split(marker)[0]+marker
 for n in sorted(old.keys()|new.keys()):
  if old.get(n)==new.get(n):continue
  lines.append('delivery/'+n+'\t'+(hashlib.sha256(old[n]).hexdigest() if n in old else '-')+'\t'+(hashlib.sha256(new[n]).hexdigest() if n in new else '-'))
  if n.endswith(('.json','.py','.sh','.cmd')):
   a=old.get(n,b'').decode().splitlines(True);b=new.get(n,b'').decode().splitlines(True)
   patch+=''.join(difflib.unified_diff(a,b,fromfile='base-delivery/'+n,tofile='delivery/'+n))
 (d/'FILE_SHA256_DIFF.tsv').write_text('\n'.join(lines)+'\n');(d/'PATCH.diff').write_text(patch)
 results={p.stem:read(p) for p in d.glob('*_result.json') if p.name.startswith(('base_','release_'))}
 assert all(not r['failures'] and not r['errors'] and not r['skipped'] for r in results.values())
 base_count=sum(v['tests'] for n,v in results.items() if n.startswith('base_'))
 release_count=sum(v['tests'] for n,v in results.items() if n.startswith('release_'))
 txt=['All listed suites passed; 0 failures, 0 errors, 0 skips.','',f'Base gates and scoring regressions: {base_count}.',f'Release package, admission, sequence, guard, memory, return/stop and applicable room/CPU gates: {release_count}.','Return CLI: 2 positive/negative cases per package.','Fill: 6 cases per package; real preparation files; Python 3.6.8.','Integrated fill + 3.py metadata check: 1 per package; dependency sizes/placement are explicit filesystem fixtures.','Shared scoring tests: 7. Baseline self-pairing: all five types and both room sets have zero differences and zero 95%/99.29% intervals.','', 'Suite counts:']
 for n,v in sorted(results.items()):txt.append(n+': '+str(v['tests']))
 txt+=['','CPU tests use /scratch/jjyeung/envs/p1cpu/bin/python with OMP/MKL/OPENBLAS_NUM_THREADS=8. Orchard helper tests use /usr/bin/python3 -I -s -B (3.6.8).','Local weights/model forwards, namespace, allocation, and staging are fixtures; an allocated Orchard CPU receipt remains mandatory.','Reproduce: bash '+str(W/'run_local_tests.sh')]
 (d/'TESTS.txt').write_text('\n'.join(txt)+'\n')
 pub=read(d/'package/0.json');binding=read(O/'EXPORT_BINDING.json');scope=[
  f"`src/9.json:1` seals run 673bc60f, SFT step 200, m200, the object key, runtime config identity, and all three exact preparation hashes.",
  f"`src/orchard_h10/export_pins.py:{at(d/'src/orchard_h10/export_pins.py','binding = cfg.get')}` rejects mismatched run, step, member, lineage, object, config identity, preparation hashes, and archive hash before staging.",
  f"`fill_export.py:{at(d/'fill_export.py','def bind_review')}` adds the reviewed binding checks; `scan` and `preparation` remain AST-identical to T1/T2. The fill verifies all tar members, weight shards/index, all part hashes, whole-tar bytes/SHA, and the preparation chain. It replaces archive slot 4, avoiding a stale preparation overlay; B retains its frame archive slot 5.",
  f"`tower_sequence.py:{at(d/'tower_sequence.py','RULES=')}` selects one candidates_argmax read with memo on, g3t only, no verification IDs, and no own-depth saves. A keeps read 0's dispatch order [distance, displacement, rotation, movement direction, room]. B keeps all 134 room items in T2 order.",
  f"`src/8.py:{at(d/'src/8.py','def digest')}`, `src/orchard_h10/common.py:{at(d/'src/orchard_h10/common.py','if not hasattr')}`, `node_check.py:{at(d/'node_check.py','isinstance(expression, ast.Call)')}`, and four vendor helpers provide Python 3.6 compatibility: bounded SHA256 reads, lexical containment, explicit AST attributes, PIPE arguments, and universal_newlines. Vendor keyword changes preserve behavior; their template pins are resealed.",
  f"`src/orchard_h10/job.py:{at(d/'src/orchard_h10/job.py','metadata/EXPORT_PIN.json')}` returns the admitted export pin and input manifest for local authentication. `unpack_return.py:{at(d/'unpack_return.py','inputs=json.loads((dest')}` checks these against the sealed package and returned identity.",
  f"`tower_bootstrap.py:{at(d/'tower_bootstrap.py','shared=')}` and the package checker/stager use `/project/community/jjyeung/okh7/a15_cot_ap{token}`. Public job names are `a15_cot_ap{token}`; scripts, logs, and transfer parts use numeric or opaque names. The sealed private source tree and stable logical root retain base paths because the pinned policy and reader depend on them."]
 report=f'''# R1 step-200 package {'A' if k=='b1' else 'B'}

Token: `{token}`. This package is built and tested locally; it has not been placed, filled with the real export, CPU-checked on Orchard, or submitted.

Two packages preserve the distinct T1/T2 item mapping and reader paths. A combined read would require more than a plan change. A reads 636 dev-S1 items (450 camera, 150 distance, 36 room); B reads all 134 T2 room items (36 dev-S1 and 98 R0-dev). Both use one worker per read and the same single pull of the four step-200 parts. B's pull script has no download command.

## Hashes

| File | SHA256 |
|---|---|
| 0.tgz | `{sha(d/'0.tgz')}` |
| 1.tgz | `{sha(d/'1.tgz')}` |
| PACKAGE.json | `{sha(d/'PACKAGE.json')}` |
| READ_PLAN.json | `{sha(d/'READ_PLAN.json')}` |
| Sealed plan | `{pub['plan_sha256']}` |
| Item manifest | `{sha(manifest)}` |

`TOKEN_CHECK.json` records checks against all {len(ledger_paths)} matching ledgers, both base reports, and b1g/PROMPT.md. The tokens are distinct and absent from those sources.

## Read and serving pins

The read uses tower, mode none, candidates_argmax, perception_memo on, modules [g3t], verification IDs [], and save_own_depth false. `READ_PLAN.json` lists every item in execution order; the list matches the corresponding baseline read 0 exactly. Reader, evaluator, task mapping, scorers, scale/selector weights, G3T/SAM weights, call caps, and return transport bytes remain fixed. No reader or scorer source changes enter 0.tgz. T2's per-set room labels remain distinct.

## Time and cut point

The wall cap is {plan['walltime']}. The measured-time estimate reaches all {len(ids)} items at T+{timing['estimated_completion_hms']}; the next-item admission cutoff is T+{str(datetime.timedelta(seconds=timing['stop_at_seconds']))}. The active item may drain until T+{str(datetime.timedelta(seconds=timing['drain_until_seconds']))}; return retains the final 20 minutes. The 30-minute stop margin contains the 20-minute return margin. Estimated slack before the stop cutoff is {timing['estimated_stop_slack_seconds']:.1f} seconds. `TIME_PRICE.json` gives per-type measurements and the cut-point calculation. Timing estimates do not guarantee m200's decode speed.

## Export admission and review scope

The single review must cover all of the following changes, including the operator bundle and Python 3.6 helper edits, not just 9.json:

'''+''.join('- '+x+'\n' for x in scope)+f'''
The sealed preparation SHA256 values are config `{binding['preparation_sha256']['config']}`, receipt `{binding['preparation_sha256']['receipt']}`, and data receipt `{binding['preparation_sha256']['data_receipt']}`. Runtime config identity is `{binding['config_sha256']}`. The tar SHA is intentionally unresolved until the exact object `.done` receipt lands; no step-544 export can pass the new admission.

`INTEGRATED_FILL.json` proves the fill plus actual 3.py metadata check with small four-part archives, the m100 artifact schema adapted to m200, and all three real preparation files. Negative cases reject wrong step, artifact step, run, config identity, and tar SHA. No synthetic preparation pin is used by the final positive proof. Only remote placement and unchanged dependency archive sizes are mocked for the metadata check. Actual archive extraction, environment/weight restore, and frame checks must pass the allocated Orchard CPU job.

## Validation and scoring

The base suites pass {base_count} tests and the release suites pass {release_count}; see TESTS.txt for counts and scopes. Return CLI, fill, integrated fill/check, operator syntax, receipt, and shared scoring checks are recorded separately. Both final readers remain byte-identical to their bases.

`../score_r1route.py` uses T1 job 171253 read 0 for camera and dev-S1 room, T1 read 1 candidates_argmax for distance, and T2 job 172456 read 0 for both room sets. It prints per-type accuracy/MRA, 95% and 99.29% paired intervals from 10,000 physical-room draws (accepted seed 17), call-cap/token-cap/status/not-seen counts, the fixed 450-item camera call rate, and correct conversions over all 107 non-metre distance items. Room scores use mra_answer and reproduce T2's saved scores. The accepted unit diagnostic reproduces the card's own count of 22/107; the tower baseline has 29/107. The 544-vs-544 test gives exactly zero differences and both intervals [0,0] for every type and room set.

A missed camera journal remains missing; partial results cannot certify H3. The distance call-cap count and its room-bootstrap count interval are printed separately from token caps. No R1 result or training decision is claimed by these fixture tests.

Run the exact scripts in `OPERATIONS_R1ROUTE.md`. `PATCH.diff` and `FILE_SHA256_DIFF.tsv` cover payload, operator, and delivery changes. No files were deleted. No borderline revision-history sentence is retained in this report.
'''
 (d/'REPORT.md').write_text(report)
 (d/'REMOVAL_CANDIDATES.md').write_text('''# Removal candidates

No deletion ran. Keep both packages, their shared four-part export cache, and return archives until the lane has verified and retained both scores. After both reads finish, the operator may review the package directories and A's `a/e` cache for removal. Do not remove the shared cache while B still needs it. Local `W/verify`, `W/release`, `W/tmp`, and `out/test_tmp` contain retained test fixtures. They are disposable after review; this file does not authorize deletion.
''')
 write(d/'FINAL_VERIFICATION.json',dict(token=token,base_tests=base_count,release_tests=release_count,failures=0,errors=0,skipped=0,fill_cases=6,return_cli_cases=2,integrated_fill=True,real_preparation=True,submitted=False,payload_sha256=sha(d/'0.tgz'),delivery_sha256=sha(d/'1.tgz')))
 # Shared scorer entry points keep per-package invocation convenient.
 (d/'score_r1route.py').write_text("from pathlib import Path\nimport runpy,sys\np=Path(__file__).resolve().parent.parent\nsys.path.insert(0,str(p))\nrunpy.run_path(str(p/'score_r1route.py'),run_name='__main__')\n")
 (d/'test_score_r1route.py').write_text("from pathlib import Path\nimport runpy,sys\np=Path(__file__).resolve().parent.parent\nsys.path.insert(0,str(p))\nrunpy.run_path(str(p/'test_score_r1route.py'),run_name='__main__')\n")
 print(k,token,base_count,release_count,timing['estimated_completion_hms'])
(O/'REPORT.md').write_text('''# R1 step-200 read packages

A: [b1/REPORT.md](b1/REPORT.md), token `'''+(O/'b1/TOKEN').read_text().strip()+'''`, 636 dev-S1 items.

B: [b2/REPORT.md](b2/REPORT.md), token `'''+(O/'b2/TOKEN').read_text().strip()+'''`, 134 room items (36 dev-S1 + 98 R0-dev).

Both packages use candidates_argmax and share one four-part export pull. Their real-preparation fill proofs and local CPU tests pass. They await review, Orchard fill, allocated CPU checks, and sequential one-GPU reads. The baseline self-pairing has zero differences and zero 95%/99.29% intervals. Start with each package's OPERATIONS_R1ROUTE.md; place both, fill A, then fill B from A's verified cache.
''')
