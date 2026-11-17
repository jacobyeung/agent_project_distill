"""Run the local evidence suite after rebind; never authorize production."""
import difflib,json,subprocess,sys,tempfile
from pathlib import Path
from rebind import ROOT,H,load,sha,write
from derive_deployment import derive

def run(args,log):
    with (ROOT/'out/logs'/log).open('w') as f:
        subprocess.run([sys.executable,'-B',*map(str,args)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)

def main():
    out=ROOT/'out';binding=load(out/'BINDING.json')
    # The caller must finish rebind before running this command.
    run([ROOT/'tools/make_proof.py'],'make_proof.log')
    run([ROOT/'tools/package_operator.py'],'package.log')
    archive=out/load(out/'OPERATOR.json')['archive'];expected=sha(archive)
    run([ROOT/'tools/package_operator.py'],'package_repeat.log')
    if sha(archive)!=expected:raise ValueError('Operator package is not deterministic')
    parent=Path(tempfile.mkdtemp(prefix='derive_',dir=ROOT/'work'));source=H/'build/fx'
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
    for name in ('carrier_c1_data.py','carrier_c1_run.py','type_mix.py','loader_audit.py'):
        rel='student_pilot/'+name;old=H/'build/tree'/rel
        before=old.read_text().splitlines(keepends=True) if old.exists() else []
        patch.extend(difflib.unified_diff(before,(ROOT/'work/tree'/rel).read_text().splitlines(keepends=True),fromfile='a/'+rel,tofile='b/'+rel))
    (out/'SAMPLER_REVIEW.patch').write_text(''.join(patch))
    run([ROOT/'tests/test_packet.py'],'tests.log')
    run([ROOT/'tools/finalize.py'],'finalize.log')
    print(json.dumps(dict(status='BUILT_BLOCKED',config_identity=binding['config_identity'],operator_archive_sha256=expected)))

if __name__=='__main__':main()
