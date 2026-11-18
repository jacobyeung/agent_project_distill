"""Run local continuation checks without replacing the sealed Cprime package."""
import io,json,os,subprocess,sys,tarfile,tempfile,traceback
from pathlib import Path
from rebind import ROOT,H,load,write,sha

def main(only_derivation=False):
    out=ROOT/'out';op=load(out/'OPERATOR.json');binding=load(out/'BINDING.json');results=load(out/'LOCAL_CHECKS_CPRIME.json') if only_derivation else {}
    def check(name,fn):
        try:results[name]=dict(status='PASS',result=fn())
        except FileNotFoundError as e:results[name]=dict(status='NOT_RUN_MISSING_INPUT',cause=str(e))
        except Exception as e:results[name]=dict(status='FAIL',cause=str(e),traceback=traceback.format_exc())
        write(out/'LOCAL_CHECKS_CPRIME.json',results)
    def command(args,log):
        with (out/'logs'/log).open('w') as f:
            subprocess.run([sys.executable,'-B',*map(str,args)],check=True,stdout=f,stderr=subprocess.STDOUT,cwd=ROOT)
        return log
    def package():
        before=sha(out/op['archive']);command([ROOT/'tools/build_cprime.py'],'cprime_reseal.log')
        after=load(out/'OPERATOR.json');assert after['sha256']==before==sha(out/after['archive'])
        with tarfile.open(out/after['archive']) as tf:
            names=tf.getnames();assert 'B1R_MAPPING.json' not in names
            assert len(names)==len(set(names))
        return dict(archive=after['archive'],sha256=before,members=len(names),deterministic=True)
    if not only_derivation:check('deterministic_package',package)
    def derived():
        from derive_deployment import derive
        from cprime_recovery import recover_h1
        source=recover_h1();parent=Path(tempfile.mkdtemp(prefix='cprime_derive_',dir=ROOT/'work'))
        a=derive(source,parent/'a',out/'operator',sha(source/'SHA256SUMS.txt'),fixture=True)
        b=derive(source,parent/'b',out/'operator',sha(source/'SHA256SUMS.txt'),fixture=True)
        assert a==b
        write(out/'proof/DERIVATION.json',dict(status='PASS',two_derivations_exact=True,operator_archive_twice_exact=True,
            operator_archive_sha256=op['sha256'],manifest_sha256=a['manifest_sha256'],config_identity=a['config_identity'],
            missing_source_members=a['missing_source_members'],source_manifest_sha256=a['source_manifest_sha256'],
            fixture_paths=[str(parent/'a'),str(parent/'b')],scope='Local recovered H1 fixture'))
        return a
    check('two_derivations',derived)
    def off():
        worker=ROOT/'tests/tiny_worker.py';cfg=ROOT/'work/reference/configs/d0.json'
        tree='/scratch/jjyeung/orch_n30/tree_rebuild_w/work/base/tree_b01ce449'
        command([worker,'--tree',tree,'--config',cfg,'--out',out/'proof/off_sealed.json'],'cprime_off_sealed.log')
        command([worker,'--tree',ROOT/'work/tree','--config',cfg,'--out',out/'proof/off_candidate.json'],'cprime_off_candidate.log')
        left=load(out/'proof/off_sealed.json');right=load(out/'proof/off_candidate.json');assert left['ranks']==right['ranks']
        value=dict(status='PASS',all_four_ranks_exact=True,ranks=[{k:r[k] for k in ('rank','state_sha256','rows')} for r in left['ranks']],
            d0_config_identity=left['config_identity'],candidate_tree_sha256=binding['tree_sha256'],scope='Native tiny optimizer; synthetic inputs')
        write(out/'proof/OFF_IDENTITY.json',value);return value
    if not only_derivation:check('off_identity',off)
    if not only_derivation:check('first_batch',lambda:command([ROOT/'tests/tiny_worker.py','--tree',ROOT/'work/tree','--config',ROOT/'configs/r1p.json',
        '--audit',out/'proof/loader_audit.json','--out',out/'proof/FIRST_BATCH.json'],'cprime_first_batch.log'))
    print(json.dumps(results),flush=True)
    if any(x['status']=='FAIL' for x in results.values()):raise SystemExit(1)

if __name__=='__main__':main()
