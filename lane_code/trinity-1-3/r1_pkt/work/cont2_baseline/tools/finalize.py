"""Write current evidence and its limits for the exact packet identity."""
import json,re
from rebind import ROOT,load,sha,write

def main():
    out=ROOT/'out';b=load(out/'BINDING.json');op=load(out/'OPERATOR.json');cfg=load(out/'config.json')
    if cfg.get('continuation'):
        from report_cont1 import main as report
        return report()
    log=(out/'logs/tests.log').read_text();assert log.rstrip().endswith('OK')
    count=int(re.search(r'Ran (\d+) tests',log).group(1))
    names=['FIRST_BATCH.json','DERIVATION.json','PRE_SUBMISSION.json','SWITCH_GUARDS.json','UNIT_REAL.json']
    for n in names:
        value=load(out/'proof'/n);assert value['status']=='PASS' and value['config_identity']==b['config_identity'],n
    assert load(out/'proof/PRE_SUBMISSION.json')['operator_archive_sha256']==op['sha256']
    assert sha(out/op['archive'])==op['sha256']
    audit=load(out/'proof/loader_audit.json');assert audit['requested_config_identity']==b['config_identity']
    note=f'''BUILT FOR REVIEW. Config `{b['config_identity']}`, run `{b['run_key']}`, S2={cfg['h1']['routing_pose_targets']}, S1=false, both own-sampling probabilities zero.

Archive `{op['archive']}`, SHA256 `{op['sha256']}`. The config appends one pinned 601-row REMOVE list. The sealed trainer, v7 store, division, routing selection and units remain unchanged. Room eligibility is 425 and its cell is 1.70; direction receives the two-cent refill at 31.19. `MIX.md` gives all populations and caps; `CONFIG_DIFF10.json` gives the exact config delta.

All {count} packet tests pass. `tools/run_local_checks.py` verifies deterministic packaging, two equal fixture deployment derivations, production-form evidence validation, four-rank D0 optimizer identity, the final-config CPU first batch, and all packet tests. Native unit regeneration retains 747 rows, including 683 feet. The native VQA sampler audits 1,000 steps and 128,000 draws with at most four repeats.

Full production admission is NOT certified. The unmodified VQA build cannot read a missing pinned RGB file locally. The full-store structural regression mocks only RGB-byte binding and executes the sealed scene, REMOVE, division, uniqueness and row predicates; it fails without the new list and passes with it. Pointing, pose/model metadata and complete routing sources are absent locally. `FIX10_BUILD.json` and `FIX10_PHASES.json` record the exact boundaries. First-batch pixels and auxiliary streams are fixtures. Production CPU proof, complete RGB verification, full routing regeneration and independent review remain required.

The operator must verify the archive and bundle sums, derive a fresh private kit using `d.py`, regenerate routing selection using `q.py`, provide independent review/staging/archive evidence, seal the CPU proof using `p.py`, and run the named proof script. Existing deployment checks remain in force. No production authorization or GO is supplied.
'''
    for n in ('REPORT.md','R1P_PACKET.md'):(out/n).write_text(note)
    write(out/'proof/GATES.json',dict(status='BUILT_BLOCKED',config_identity=b['config_identity'],tests=count,
        production_authorized=False,full_store_structural=load(out/'FIX10_BUILD.json'),phases=load(out/'FIX10_PHASES.json'),
        loader_audit='PASS_LOCAL_VQA_ONLY',required_families=audit['required_families'],independent_review='PENDING'))
    write(out/'REVIEW_REQUEST.json',dict(status='REVIEW_REQUIRED',config_identity=b['config_identity'],tree_sha256=b['tree_sha256'],operator_archive=op['archive'],operator_archive_sha256=op['sha256'],reviews_requested=1,
        reason='Verify the 601 exact out-of-division REMOVE keys, staging pin, 425-row room cap, exact packet switch and local RGB/stream limits.'))
    (ROOT/'STATUS.md').write_text(note.split('\n\n')[0]+' All '+str(count)+' packet tests pass. Full native admission remains blocked by missing local production inputs; read out/FIX10.md and out/FIX10_PHASES.json.\n')
    files=[p for folder in ('proof','records','units','logs') for p in (out/folder).rglob('*') if p.is_file()]
    files += [p for p in out.iterdir() if p.is_file() and p.name!='SHA256SUMS' and (p.suffix not in ('.tar',) or p.name in (op['archive'],'r1p_code.tar'))]
    (out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(out))+'\n' for p in sorted(set(files))))
    print(json.dumps(dict(status='BUILT_BLOCKED',identity=b['config_identity'],local_tests=count,archive=op['archive'])))
if __name__=='__main__':main()
