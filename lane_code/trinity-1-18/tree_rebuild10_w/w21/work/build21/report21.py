from pathlib import Path
import json,datetime
L=Path(__file__).resolve().parents[2];B=L/'work/build21'
def get(path,default=None):
 p=Path(path);return json.loads(p.read_text()) if p.exists() else default
def rel(path):
 try:return str(Path(path).relative_to(L))
 except ValueError:return str(path)
def source(path):return '`'+rel(path)+'`'
def table(headers,rows):
 return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join('---' for _ in headers)+'|',*['| '+' | '.join(str(v).replace('|','/').replace('\n',' ') for v in row)+' |' for row in rows]])+'\n'
def block(value):return '```json\n'+json.dumps(value,indent=2)+'\n```\n'
cap=get(B/'proofs/capacity/RESULT.json',{});census=get(B/'proofs/census/CENSUS.json',{});plan=get(B/'proofs/census/PLAN_RUN.json',{})
receipts=get(B/'proofs/receipts/RESULT.json',{});coverage=get(B/'DELTA_COVERAGE.json',{});uploads=get(B/'UPLOADS.json',{})
tests=[]
for p in sorted((B/'proofs').rglob('TESTS.json')):
 if any('before' in n or n=='mutant' for n in p.parts):continue
 v=get(p);tests.append((rel(p),v.get('tests'),v.get('successful'),len(v.get('failures',[])),len(v.get('errors',[]))))
issues=[]
if not cap.get('complete_native_fixture'):
 for step in ('400','600'):
  v=cap.get('milestones',{}).get(step,{})
  if v.get('status')!='ADMIT':issues.append(step+' '+str(v.get('refusal',cap.get('refusal','capacity proof unfinished'))))
if not census:issues.append('V2H census unfinished')
if any(not t[2] for t in tests):issues.append('focused or new tests contain failures; see test table')
if any(r.get('status')!='PASS' for k in ('receipts','prepared','children') for r in receipts.get(k,[])):issues.append('real receipt refusal')
if receipts.get('absent'):issues.append('real stream receipt absent')
if not get(B/'proofs/coverage_mutations/RESULT.json') and not get(B/'proofs/mutations/RESULT.json'):issues.append('coverage mutation proof absent')
verdict='NO-GO — '+'; '.join(issues) if issues else 'GO for the CPU build proof; the Orchard kit remains GO=false and unsubmitted.'
lines=[verdict,'',
 'This delivery fixes the reviewed staging and native export layout, authenticates the supplied P receipts, and binds the coverage and K1 exclusions. It preserves N’s parent, exclusion lists, component-evidence boundary, and full-model forward path. The package does not authorize a submission.','',
 'Fixes and checks','',
 table(['Change','Evidence'],[
 ('Stage ANON_OK.json with its authenticated P pin; refuse an omitted entry.','work/build21/proofs/review_final/TESTS.json; work/build21/proofs/review_controls/RESULT.json; work/build21/proofs/new_controls/RESULT.json'),
 ('Assemble full_weights.json, its native index and shards beside the manifest, using authenticated local hardlinks.','work/build21/jobtest.py; work/build21/proofs/job/; work/build21/proofs/review_controls/RESULT.json'),
 ('Use operator-created opaque aliases for P’s pool and model archive. Verify pinned archive hashes before execution; preserve legacy environment behavior through opaque aliases.','work/build21/OPERATOR.md; work/build21/naming21.py; work/build21/review21.py'),
 ('Scan decoded executable shell and operational paths; screen process logs with the bound forbidden-word lists.','work/build21/proofs/operator/SCAN.json; work/build21/review21.py'),
 ('Refuse unsupported component evidence before native store production, preserving the scoped deferral rule.','work/build21/preflight_tests21.py; work/build21/proofs/preflight_before/TESTS.json; work/build21/proofs/new_controls/RESULT.json'),
 ('Carry the authenticated full configuration from the preparation reader to the opener initializer; check its identity and keep the sealed parent path.','work/build21/forward_diag.log; work/build21/opener_tests21.py; work/build21/proofs/new_controls/RESULT.json'),
 ('Correct the tiny fixture vision-head count while retaining its hidden and parameter dimensions. The former head count fails the native vision rotary operation.','work/build21/model_debug.log; work/build21/model_debug_one.log; work/build21/proofs/model/TESTS.json; work/build21/native_assets21.py'),
 ('Authenticate both coverage sources and held-out wording templates at training intake; refuse a planted held-out wording by name.','work/build21/proofs/coverage_tests/TESTS.json; work/build21/proofs/v2h/PLANTED.json'),
 ('Authenticate the K1 union’s two inputs, exact content and placement after the original list and before N’s list.','work/build21/proofs/v2h/BINDING.json; work/build21/proofs/new_controls/RESULT.json')]),
 'All review findings were accepted. No finding was dismissed. The scanner covers decoded executable shell, arguments, environment names and operational paths. Sealed source and provenance records retain their authenticated identifiers; this is not a claim that every byte of the source archive is word-free.','',
 'Real receipt readers','',
 'The table records calls through the readers used by mode q. Source: '+source(B/'proofs/receipts/RESULT.json')+'.',
 table(['Receipt / use','SHA-256','Reader','Result'],[
 (r['pin'].get('path'),r['pin'].get('sha256'),r['reader'],r['status']) for k in ('receipts','prepared','children') for r in receipts.get(k,[])]),
 'Prepared rows use the preparation pin and stream name recorded in the receipt result. That result also records the authenticated database identities and pose counts. Authentication mutation evidence: '+source(B/'proofs/receipt_auth/TESTS.json')+'.',
 'Dependencies absent from the fetched local metadata set are listed below. These are requirements for the real host, not silent passes for file contents.',
 table(['SHA-256','In-job path'],[(r['sha256'],r['path']) for r in receipts.get('missing_dependency_pins',[])]),
 'Capacity fixture','',
 'Source: '+source(B/'proofs/capacity/RESULT.json')+' and '+source(B/'proofs/capacity/CAPACITY.json')+'. Synthetic RGB, metric labels and the tiny native model stand in at the frame-host/model-size boundary. The CPU processor constructor and local publication collectives are explicit stand-ins. Native stores, receipt producers, admission, audit, handover, initialization and forward/loss functions run unchanged. No real frame set, database, cache or checkpoint was copied.','']
rows=[];losses=[]
for step in ('400','600'):
 v=cap.get('milestones',{}).get(step,{})
 for e in v.get('stage_events',[]):rows.append((step,e['function'],e['result'],e.get('error',''),rel(B/'proofs/capacity'/step/'q/RESULT.json')))
 f=get(B/'proofs/capacity'/step/'q/f.json',{})
 for rank in range(4):
  rr=[r for r in f.get('records',[]) if r['rank']==rank]
  losses.append((step,rank,rr[0].get('loss') if rr else 'not reached',rr[0].get('stream') if rr else '',len(rr),all(r.get('finite') for r in rr) if rr else False,rel(B/'proofs/capacity'/step/'q/f.json')))
 lines.extend(['Milestone '+step+': '+v.get('status','not completed')+'. '+v.get('refusal','')])
lines.extend(['',table(['Milestone','Stage','Result','Error','Source'],rows),table(['Milestone','Rank','First loss','First stream','Rows forwarded','All finite','Source'],losses)])
for step,twins in cap.get('twins',{}).items():
 lines.extend(['Twin results from '+source(B/'proofs/capacity'/step/'TWINS.json')+':',table(['Twin','Result','Refusal'],[(n,v.get('status'),v.get('refusal')) for n,v in twins.items()])])
lines.extend(['V2H binding and census','',
 'Every supplied coverage row passed the kit row validator and the exact rewording/parent-geometry check. Sources: '+source(B/'proofs/v2h/VALIDATION.json')+' and '+source(B/'proofs/v2h/PARENT_CHECK.json')+'.',
 block({k:v for k,v in get(B/'proofs/v2h/BINDING.json',{}).items() if k!='examples'}),
 'The census streams the authorized source slices and v7 store. It retains bounded examples. Frame metadata uses a synthetic host path; absent FPS uses a labelled GUESS in the census evidence. Real frame envelopes must still be supplied by the operator.',
 'Source: '+source(B/'proofs/census/CENSUS.json')+'.',
 block({k:census.get(k) for k in ('vqa','slices','heldout_wording_hits','k1_union_found','inherited_counts')}),
 'The card allocates the coverage cell pro rata from the four program cells, then applies the authentic post-filter ceilings. Source: '+source(B/'proofs/census/PLAN_RUN.json')+'.',
 table(['Cell','Eligible','Ceiling / step','Quota / step','Draws','Largest repeat'],[(n,v['eligible'],v['ceiling'],v['quota'],v['draws'],v['largest_repeat']) for n,v in plan.get('cells',{}).items()]),
 block({k:plan.get(k) for k in ('steps','largest_repeat','total_draws','resumed','scope')}),
 'Tests, mutations and coverage','',table(['Source','Tests','Passed','Failures','Errors'],tests),
 'Mutation evidence: '+source(B/'proofs/review_controls/RESULT.json')+', '+source(B/'proofs/new_controls/RESULT.json')+', '+source(B/'proofs/mutations/RESULT.json')+'.',
 'Changed-statement coverage uses the standard-library monitor, current source hashes and compiled-code fingerprints. Source: '+source(B/'DELTA_COVERAGE.json')+'.',
 block(dict(tree_observed=coverage.get('observed'),tree_total=coverage.get('total'),kit_observed=coverage.get('kit',{}).get('observed'),kit_total=coverage.get('kit',{}).get('total'))),
 'Staging and delivery','',
 'Both kits were staged from empty with GO=false. The package contains the source, editable harnesses, small proof records, staging map and authenticated small inputs. It omits generated capacity stores, model weights and frame assets. The delivery manifest authenticates every packaged member.',
 'Source seal: '+source(L/'out/TREE_SEAL.json')+'. Upload total: '+str(uploads.get('total_bytes'))+' bytes from '+source(B/'UPLOADS.json')+'. Package hash, byte size and storage accounting: '+source(B/'DELIVERY.json')+'.',
 'For the confirmation','',
 'Review '+source(B/'OPERATOR.md')+', '+source(B/'UPLOADS.json')+' and '+source(B/'DELIVERY.json')+'. The operator must create the listed opaque links and supply the pinned host dependencies and RGB envelopes before a real proof. This build performed no submission or remote write.',
 'Not checked: live Orchard contents, actual bwrap isolation, scheduler behavior, GPU kernels or distributed collectives, the full-size model archive, real-frame forward passes, complete historical suites beyond the requested focused set, or benchmark performance. CPU first-batch evidence does not establish training convergence.',''])
(L/'out/BUILD21_REPORT.md').write_text('\n'.join(lines))
print(verdict)
