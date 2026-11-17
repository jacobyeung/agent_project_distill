"""Classify suite outcomes by the same test's untouched-base result."""
import hashlib
import json
import os
import re
from pathlib import Path
import sys
from collections import Counter
L=Path(__file__).resolve().parents[2]
root=L/'work/build7/proofs'
kind=os.environ.get('R2_COMPARISON_KIND','suite')
tree=json.loads((root/(kind+'_tree')/'results.json').read_text())
base=json.loads((root/(kind+'_base')/'results.json').read_text())
def canonical_test(name):
    return re.sub(r"(['\"])[^'\"]*/work/tmp/[^'\"]*\1", "'<temporary path>'",name)
prior={}
for name,error in base['failures']+base['errors']:
    prior.setdefault(canonical_test(name),[]).append(error)
build5=json.loads((L/'work/build5/proofs/suite_tree/results.json').read_text())
old_errors={}
for name,error in build5['failures']+build5['errors']:
    old_errors.setdefault(canonical_test(name),[]).append(error)
guard_proof=json.loads((L/'work/build7/LEGACY_GUARDS.json').read_text())
guards_verified=guard_proof['verified'] and all(
    hashlib.sha256((L/'work/tree_r1'/row['file']).read_bytes()).hexdigest()==row['current_sha256']
    for row in guard_proof['guards'])
def classify(error):
    if 'test_r2_build5_edges.py' in error and "'parts' not found" in error:
        return 'R2 fixture expects placeholder staging parts; unknown sources now require an explicit pinned parameter'
    if 'test_r2_build5_host_order.py' in error and "KeyError: 'file'" in error:
        return 'R2 host-order fixture omits the runtime file pin required by the new staging self-check'
    if 'test_gf1_cache.py' in error and 'bf16_tower_bf16_base_bf16_cache_pre_lm' in error:
        return 'BF16 cached/online gradient exceeds the supplied relative tolerance; enabled BF16 remains refused'
    if any(value in error for value in ('Build policy refuses os.'+'remove','Build policy refuses os.'+'rmdir','Build policy refuses shutil.'+'rmtree')):
        return 'forbidden file cleanup under the no-deletion rule'
    if any(s in error for s in ('Build policy refuses','Proof policy','child processes','socket.connect','socket.bind')):
        return 'forbidden subprocess or socket / restricted operation'
    if any(s in error for s in ('ModuleNotFoundError','ImportError','PackageNotFoundError','sentencepiece or tiktoken')):
        return 'absent dependency or external module'
    if 'File too large' in error:return 'file-size limit under the bounded harness'
    if 'Default process group has not been initialized' in error or 'DistNetworkError' in error:
        return 'distributed process-group fixture unavailable under the socket restriction'
    if "name 'tvF' is not defined" in error:return 'optional vision dependency is unavailable'
    if 'Repo id must be in the form' in error:return 'legacy pretrained fixture directory is absent'
    if 'temporary storage policy' in error:return 'test exceeds temporary storage limit under this harness'
    if any(s in error for s in ('FileNotFoundError','outside package','Build file policy','No such file','Missing or changed pinned')):
        return 'missing fixture at the legacy path or forbidden external path'
    if 'trace_program_version_missing' in error:
        return 'legacy fixture lacks required trace_program_version'
    if 'STUDENT_PILOT_ARCHIVED_RUN' in error:
        return 'missing archived-run fixture environment'
    if 'Operation not permitted' in error and ('multiprocessing' in error or 'synchronize.py' in error):
        return 'sandbox refuses the legacy multiprocessing semaphore fixture'
    if 'pil_torch_interpolation_mapping[resample]' in error:
        return 'optional vision interpolation dependency is unavailable'
    if 'Provisional artifacts require /data2 or an explicit node-local scratch root' in error:
        return 'legacy fixture lacks explicit node-local artifact admission'
    if 'Probe cache requires an owned absolute path without symlinks' in error:
        return 'legacy cache fixture fails ownership or path admission'
    if 'DDP input must stay inside the repository' in error:
        return 'legacy fixture fails input-root admission before its expected refusal'
    if 'MDG stream and configuration presence differ' in error:
        return 'legacy fixture stream/configuration mismatch precedes its intended check'
    if 'unexpected keyword argument' in error:
        return 'legacy test double lacks a keyword required by the base implementation'
    if 'Complete routing row exceeds' in error:
        return 'legacy routing fixture exceeds the native token limit'
    if 'Unsupported student architecture:' in error:
        return 'legacy memory-probe implementation does not support the fixture architecture'
    if 'test_module_is_the_shared_byte_identical_copy' in error:
        return 'legacy expected module digest differs from the untouched base'
    if 'test_provisional_lease_records_real_host_uuid_and_rechecks_both' in error:
        return 'legacy lease fixture UUID differs from the recorded probe UUID'
    if 'test_code_provenance_' in error:
        return 'legacy provenance mock differs from the result under the shared harness'
    if 'test_exhausted_resume_saves_the_same_step_under_each_attempt' in error or 'optimizer=None, disk_guard=None' in error:
        return 'legacy save/export assertion omits native disk-budget keyword arguments'
    if 'test_carrier_c1_t0.py' in error and 'unexpected pos' in error:
        return 'legacy teacher serialization write failure'
    return 'unclassified: '+error.strip().splitlines()[-1]
failed=[]
for name,error in tree['failures']+tree['errors']:
    key=canonical_test(name)
    tree_cause=classify(error)
    candidates=prior.get(key,[])
    matched=next((value for value in candidates if classify(value)==tree_cause),None)
    base_error=matched or (candidates[-1] if candidates else None)
    base_cause=classify(base_error) if base_error else None
    prior_guard=next((value for value in old_errors.get(key,[]) if
        'Legacy reader has no authenticated R2 bank adapter: ' in error
        and value.strip().splitlines()[-1]==error.strip().splitlines()[-1]),None)
    preserved_guard=bool(candidates and guards_verified and prior_guard)
    preexisting=bool(candidates and not name.startswith('tests.test_r2') and (matched or preserved_guard))
    basis='same_base_cause' if preexisting and matched else 'preserved_build5_guard' if preexisting else 'regression'
    cause='preserved Build-5 refusal of an unauthenticated legacy reader' if basis=='preserved_build5_guard' else tree_cause
    failed.append(dict(test=name,preexisting=preexisting,basis=basis,cause=cause,
                       tree_cause=tree_cause,base_cause=base_cause,tree_error=error,base_error=base_error,
                       build5_error=prior_guard if preserved_guard else None,
                       guard_source='work/build7/LEGACY_GUARDS.json' if preserved_guard else None))
record=dict(tree_source='work/build7/proofs/'+kind+'_tree/results.json',base_source='work/build7/proofs/'+kind+'_base/results.json',
    run=tree['tests'],passed=len(tree['passed']),preexisting=sum(r['preexisting'] for r in failed),
    regressions=sum(not r['preexisting'] for r in failed),skipped=len(tree['skips']),
    r2_failures=sum(r['test'].startswith('tests.test_r2') for r in failed),fatal=tree.get('fatal'),failures=failed)
record['counting_note']='Run/pass counts retain harness-scheduled test executions, including repeated test IDs; failure counts include subtests and setup/import errors, which are listed individually.'
record['comparison_rule']='Retain all failure events per test. A legacy failure must match a base cause or repeat a source-authenticated Build-5 unsupported-reader refusal while the same base test also fails. Other differing causes remain regressions.'
record['classification_bases']=dict(Counter(r['basis'] for r in failed))
record['failed_methods']=len({r['test'].split(' (',1)[0] for r in failed if r['test'].startswith('tests.')})
record['preexisting_causes']=dict(Counter(r['cause'] for r in failed if r['preexisting']))
record['shared_grammar_failures']=sum(r['test'].startswith('published_grammar_tests.') for r in failed)
(L/('work/build7/'+kind.upper()+'_COMPARISON.json')).write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='failures'}))
groups={}
for row in failed:
    if not row['preexisting']:
        key=row['tree_error'].strip().splitlines()[-1]
        groups.setdefault(key,[]).append(row['test'])
for reason,names in groups.items():print(json.dumps(dict(reason=reason,count=len(names),examples=names[:3])))
if len(sys.argv)>1:
    for row in failed:
        if sys.argv[1] in row['test']:print(row['test'],row['tree_error'][-4000:])
