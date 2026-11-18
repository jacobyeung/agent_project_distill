from pathlib import Path
import hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/build10'
def read(name):return json.loads((B/name).read_text())
comparison=read('SUITE_COMPARISON.json');coverage=read('CHANGED_COVERAGE.json');delivery=read('DELIVERY.json')
eat=read('EAT1_SUMMARY.json');packet=read('proofs/packet/results.json')
assert all(read('proofs/suite_'+v+'/results.json')['complete'] for v in ('tree','base'))
assert all(v['status']=='complete' for v in read('FINAL_PROOFS.json'))
assert read('proofs/fixture_requalification/RESUME_RECEIPT.json')['status']=='PASS'
statuses=read('STEPS.json')
statuses['G8']=dict(status='BLOCKED_PTRACE',detail='All executable harness tests and the focused fixed_math contract pass. The original syscall-witness denial remains. Evidence: proofs/g8_available/RESULT.json; proofs/g8/test.log; HARNESS_COVERAGE.json.')
statuses['G1']=dict(status='PARTIAL_BLOCKED',detail='Registered readout passes available numeric parity. Point-depth helpers, public transforms and legacy branches remain; bound producer operands are missing. Evidence: EAT1_GROUP_EVIDENCE.json; proofs/parity/BYTE_PARITY.json.')
statuses['G2']=dict(status='BLOCKED_ACCEPTANCE',detail='Serving degree readout and available-input parity pass. The scanner flags the legacy branch; bound raw poses are missing. Evidence: proofs/parity_build7/RESULT.json; EAT1_GROUP_EVIDENCE.json.')
statuses['G3']=dict(status='BLOCKED_BOUND_INPUTS',detail='Artifact threshold and availability tests pass. Bound producer rotations are missing. Evidence: proofs/g3/RESULT.json; proofs/parity/NESTED_OPERANDS.json.')
statuses['FINAL']=dict(status='BLOCKED',detail='Source, kits, final archive, packet suite, frozen comparison, final readers and coverage are recorded. Admission remains false. See ../../out/BUILD10_REPORT.md and FINAL_PASS.json.')
(B/'STEPS.json').write_text(json.dumps(statuses,indent=2)+'\n')
(B/'STATUS.md').write_text('# Build 10 status\n\nGO=false. Source: STEPS.json.\n\n'+''.join(f'- {k}: {v["status"]}. {v["detail"]}\n' for k,v in statuses.items()))
files=['DELIVERY.json','KIT_RESULT.json','PATCH.json','FINAL_BINDING_AUDIT.json','PIN_AUDIT.json','SUITE_COMPARISON.json',
 'CHANGED_COVERAGE.json','HARNESS_COVERAGE.json','INCREMENTAL_COVERAGE.json','EAT1_SUMMARY.json','EAT1_GROUP_EVIDENCE.json',
 'proofs/package/ARCHIVE.json','proofs/packet/results.json','proofs/fixture_requalification/RESUME_RECEIPT.json',
 'proofs/parity/BYTE_PARITY.json','proofs/parity/NESTED_OPERANDS.json','proofs/parity_build7/RESULT.json','proofs/parity_tree/RESULT.json',
 'proofs/forward/RESULT.json','B04_SOURCE_AUDIT.json','B04_VALIDATOR_PIN.json','SOURCE_PRESERVATION.json','SUPPLIED_HASHES.json',
 'HARNESS_BASELINE.json','FINAL_PROOFS.json','STORAGE.json','proofs/audit/INFERENCE_COMPONENTS.json','proofs/audit/B04_COMPONENTS.json']
result=dict(status='BLOCKED',GO=False,source_seal=delivery['tree_seal'],archive_sha256=delivery['sha256'],
 packet=dict(run=len(packet),passed=sum(r['outcome']=='passed' for r in packet.values())),
 frozen_suite={k:comparison[k] for k in ('run','passed','preexisting','regressions','r2_failures','skipped')},
 coverage_classes=coverage['classes'],eat1={n:dict(overall=eat[n]['overall'],claim_grade=eat[n]['claim_grade']) for n in ('gf1','c8r','b04')},
 blockers=['BOUND_NUMERIC_INPUTS_MISSING','READOUT_MIGRATION_INCOMPLETE','B04_SEALED_VALIDATE_MISMATCH',
 'STATUS_OWNER_MISSING','STRACE_WITNESS_UNAVAILABLE','NATIVE_READER_EAT1_FAILURES','CARRIED_LAUNCH_AND_FULL_STORE_BLOCKERS'],
 evidence={name:hashlib.sha256((B/name).read_bytes()).hexdigest() for name in files})
if coverage['classes'].get('CPU-reachable unresolved'):result['blockers'].append('CPU_COVERAGE_GAPS')
(B/'FINAL_PASS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='evidence'},indent=2))
