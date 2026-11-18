"""Run the local evidence suite after rebind; never authorize production."""
import argparse,contextlib,difflib,hashlib,json,os,re,subprocess,sys,tempfile
from pathlib import Path
from rebind import ROOT,H,load,sha,write
from derive_deployment import derive

def run(args,log):
    with (ROOT/'out/logs'/log).open('w') as f:
        subprocess.run([sys.executable,'-B',*map(str,args)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--continuation-recheck',action='store_true');parser.add_argument('--defer-heavy-test',action='store_true');parser.add_argument('--share-fixture-bytes',action='store_true')
    parser.add_argument('--finalize-only',action='store_true',help='Resume reporting from a complete passing suite and matching archive evidence')
    args=parser.parse_args()
    out=ROOT/'out';binding=load(out/'BINDING.json')
    if args.finalize_only:
        if args.continuation_recheck or args.defer_heavy_test or args.share_fixture_bytes:
            raise ValueError('Finalization cannot combine with suite selection')
        op=load(out/'OPERATOR.json');expected=sha(out/op['archive'])
        if expected!=op['sha256']:raise ValueError('Archive differs from completed checks')
        for name in ('DERIVATION','PRE_SUBMISSION'):
            record=load(out/'proof'/(name+'.json'))
            if (record['status']!='PASS' or record['config_identity']!=binding['config_identity']
                    or record['operator_archive_sha256']!=expected):
                raise ValueError('Completed checks do not cover this archive: '+name)
        log=(out/'logs/tests.log').read_text()
        if not re.search(r'Ran \d+ tests in .*\n\nOK\s*\Z',log):raise ValueError('Full passing test log required')
        if 'test_full_store_build_stream_division_with_and_without_remove' not in log:
            raise ValueError('Full-store test required')
        for source,packed in (('derive_deployment.py','d.py'),('seal_proof.py','p.py'),('r4.py','r4.py'),('continuation.py','c0.py')):
            if sha(ROOT/'tools'/source)!=sha(out/'operator'/packed):raise ValueError('Tested runtime source differs: '+source)
        run([ROOT/'tools/finalize.py'],'finalize.log')
        result=load(out/'CONT4_RESULT.json')
        print(json.dumps(dict(status=result['status'],config_identity=binding['config_identity'],
            operator_archive_sha256=expected,tests=result['tests'],finalization='PASS',
            completed_suite='out/logs/tests.log',completed_derivation='out/proof/DERIVATION.json')))
        return
    # The caller must finish rebind before running this command.
    run([ROOT/'tools/make_proof.py'],'make_proof.log')
    run([ROOT/'tools/package_operator.py'],'package.log')
    archive=out/load(out/'OPERATOR.json')['archive'];expected=sha(archive)
    run([ROOT/'tools/package_operator.py'],'package_repeat.log')
    if sha(archive)!=expected:raise ValueError('Operator package is not deterministic')
    parent=Path(tempfile.mkdtemp(prefix='derive_',dir=ROOT/'work'));source=H/'build/fx'
    # Rechecks share only immutable large fixture bytes already in this lane.
    # Every destination retains the normal SHA checks; no source kit is linked.
    from unittest.mock import patch
    cached={}
    if args.continuation_recheck or args.share_fixture_bytes:
        previous=Path(load(out/'proof/DERIVATION.json')['fixture_paths'][0])
        for f in previous.rglob('*'):
            if f.is_file() and not f.is_symlink() and f.stat().st_size>1_000_000 and f.suffix in ('.tar','.gz'):cached[sha(f)]=f
    native=Path.write_bytes
    def fixture_write(path,raw):
        donor=cached.get(hashlib.sha256(raw).hexdigest()) if len(raw)>1_000_000 else None
        if donor and not path.exists():os.link(donor,path);return len(raw)
        return native(path,raw)
    with patch.object(Path,'write_bytes',fixture_write):
        a=derive(source,parent/'a',out/'operator',sha(source/'SHA256SUMS.txt'),fixture=True)
        b=derive(source,parent/'b',out/'operator',sha(source/'SHA256SUMS.txt'),fixture=True)
    if a!=b:raise ValueError('Deployment derivations differ')
    write(out/'proof/DERIVATION.json',dict(status='PASS',two_derivations_exact=True,operator_archive_twice_exact=True,
        operator_archive_sha256=expected,scope='FIXTURE; two inherited source members absent locally',
        manifest_sha256=a['manifest_sha256'],config_identity=a['config_identity'],missing_source_members=a['missing_source_members'],
        source_manifest_sha256=a['source_manifest_sha256'],fixture_paths=[str(parent/'a'),str(parent/'b')]))
    worker=ROOT/'tests/tiny_worker.py';d0=ROOT/'work/reference/configs/d0.json'
    run([worker,'--tree','/scratch/jjyeung/orch_n30/tree_rebuild_w/work/base/tree_b01ce449','--config',d0,
         '--out',out/'proof/off_sealed.json'],'off_sealed.log')
    run([worker,'--tree',ROOT/'work/tree','--config',d0,'--out',out/'proof/off_candidate.json'],'off_candidate.log')
    left=load(out/'proof/off_sealed.json');right=load(out/'proof/off_candidate.json')
    if left['ranks']!=right['ranks']:raise ValueError('OFF identity differs')
    write(out/'proof/OFF_IDENTITY.json',dict(status='PASS',all_four_ranks_exact=True,
        ranks=[{k:r[k] for k in ('rank','state_sha256','rows')} for r in left['ranks']],d0_config_identity=left['config_identity'],
        candidate_tree_sha256=binding['tree_sha256'],scope='Native tiny-model optimizer step, identical D0 config and fixture inputs; no production RGB or D0 databases locally.'))
    run([worker,'--tree',ROOT/'work/tree','--config',ROOT/'configs/r1p.json','--audit',out/'proof/loader_audit.json',
         '--out',out/'proof/FIRST_BATCH.json'],'first_batch.log')
    patch=[]
    for name in ('carrier_c1_data.py','carrier_c1_run.py','type_mix.py','loader_audit.py','vehicle_p.py'):
        rel='student_pilot/'+name;old=H/'build/tree'/rel
        before=old.read_text().splitlines(keepends=True) if old.exists() else []
        patch.extend(difflib.unified_diff(before,(ROOT/'work/tree'/rel).read_text().splitlines(keepends=True),fromfile='a/'+rel,tofile='b/'+rel))
    (out/'SAMPLER_REVIEW.patch').write_text(''.join(patch))
    patch=[]
    for name in ('b/c.sh','b/p0.sh','b/r.sh','b/h.py','b/i.py','job.sh'):
        patch.extend(difflib.unified_diff((source/name).read_text().splitlines(keepends=True),
            (parent/'a'/name).read_text().splitlines(keepends=True),fromfile='a/'+name,tofile='b/'+name))
    for name in ('jb.sh','s.sh'):
        patch.extend(difflib.unified_diff((H/'payload'/name).read_text().splitlines(keepends=True),
            (out/'operator'/name).read_text().splitlines(keepends=True),fromfile='a/'+name,tofile='b/'+name))
    (out/'DEPLOYMENT_REVIEW.patch').write_text(''.join(patch))
    selected=['DerivationEvidence.test_production_records_ready_without_slurm_or_persistent_writes',
        'Continuation','Proof','Fix11','Fix9',
        'Fix8.test_real_packing_payload_pins_and_native_selection',
        'Mix.test_config_switches_disk_and_identity',
        'VehicleP.test_fallback_filter_and_deployed_diff_baseline'] if args.continuation_recheck else []
    if args.defer_heavy_test:
        sys.path.insert(0,str(ROOT/'tests'))
        import unittest,test_packet
        def cases(suite):
            for case in suite:
                if isinstance(case,unittest.TestSuite):yield from cases(case)
                else:yield case
        selected=['.'.join(t.id().split('.')[-2:]) for t in cases(unittest.defaultTestLoader.loadTestsFromModule(test_packet))
                  if not t.id().endswith('Fix10.test_full_store_build_stream_division_with_and_without_remove')]
    run([ROOT/'tests/test_packet.py',*selected],'tests.log')
    if args.continuation_recheck:
        statuses={}
        for name in ('cont1_full_tests.log','tests.log'):
            text=(out/'logs'/name).read_text()
            records=re.findall(r'^test_\w+ \(([^)]+)\) \.\.\. (.*?)(?=^test_\w+ \(|^={10,}|^-{10,}|\Z)',text,re.M|re.S)
            for test,body in records:
                status=body.rstrip().splitlines()[-1]
                if status not in ('ok','FAIL','ERROR'):raise ValueError('Unparsed test result: '+test)
                statuses['.'.join(test.split('.')[-2:])]=status
        if any(v!='ok' for v in statuses.values()):raise ValueError('Unresolved suite failure')
        write(out/'proof/CONT1_TEST_LEDGER.json',dict(status='PASS',unique_tests=len(statuses),tests=statuses,
            initial_full_suite='out/logs/cont1_full_tests.log',final_rechecks='out/logs/tests.log',
            reason='Retain unchanged passing tests to respect the 3 GB scratch cap; rerun changed runtime, proof, namespace, identity and failed config-diff checks.'))
    run([ROOT/'tools/finalize.py'],'finalize.log')
    status=load(out/'CONT4_RESULT.json')['status'] if binding.get('continuation') else 'BUILT_BLOCKED'
    print(json.dumps(dict(status=status,config_identity=binding['config_identity'],operator_archive_sha256=expected)))

if __name__=='__main__':main()
