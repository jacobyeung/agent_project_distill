"""Build the continuation from the frozen launch authority."""
import argparse,copy,hashlib,sys,tempfile
from pathlib import Path
from rebind import ROOT,H,load,sha,write,enc,diff
from continuation import PARENT,RUN,policy,identity
SNAP=Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_9dd2fbb7')

def main():
    p=argparse.ArgumentParser();p.add_argument('--cells',type=Path,default=ROOT/'configs/cont1_cells.json')
    p.add_argument('--mix',type=Path);a=p.parse_args()
    out=ROOT/'out';parent=load(SNAP/'out/config.json');old=load(SNAP/'out/BINDING.json')
    assert identity(parent)==PARENT and old['run_key']==RUN
    assert sha(SNAP/'out/p_9dd2fbb7.tar')=='9dd2fbb77503ecee875d538ebaed933cc95ff286f76e5955fc2591f63e3f0192'
    if not a.cells.exists():write(a.cells,{s:v['cells'] for s,v in parent['type_mix']['streams'].items()})
    cells=load(a.cells);assert set(cells)==set(parent['type_mix']['streams'])
    mix=load(a.mix) if a.mix else copy.deepcopy(parent['type_mix'])
    for s,v in cells.items():mix['streams'][s]['cells']=v
    seed=dict(parent=PARENT,step=200,stop=600,milestones=[400,600],mix=mix,contract=sha(ROOT/'tools/continuation.py'))
    token=hashlib.sha256(enc(seed).encode()).hexdigest()[:8];run=hashlib.sha256(('run/'+token).encode()).hexdigest()[:8]
    cfg=copy.deepcopy(parent)
    cfg['continuation']=dict(schema='c0-v1',run=RUN,config=PARENT,step=200,root='/project/community/jjyeung/okh7/r/'+RUN,
        rows='exact' if mix==parent['type_mix'] else 'rebind')
    cfg['h1']['stop_after_step']=600;cfg['recipe']['milestones']=[400,600]
    cfg['milestones']=[400,600]
    cfg['type_mix']=mix
    for k in ('output','preparation_output'):cfg[k]=cfg[k].replace(RUN,run)
    policy(cfg,parent)
    sys.path[:0]=[str(ROOT/'work/tree'),str(ROOT/'work/tree/generator/derivgen_v7')]
    from student_pilot import carrier_c1_run,source_seal
    carrier_c1_run.validate(cfg)
    assert source_seal.inventory(ROOT/'work/tree')==load(SNAP/'out/records/c.json')['files']
    assert sha(out/'r1p_code.tar')==sha(SNAP/'out/r1p_code.tar')
    for name in old['record_files']:assert sha(out/'records'/name)==sha(SNAP/'out/records'/name)
    b=copy.deepcopy(old);b.update(config_identity=identity(cfg),run_key=run,store_key=token,record_key=old['store_key'],
        mix=cfg['type_mix'],job_name='a15_cot_ap'+run,proof_partition='general',continuation=cfg['continuation'],time_limit='24:00:00')
    write(out/'config.json',cfg);write(ROOT/'configs/r1p.json',cfg);write(out/'BINDING.json',b)
    write(out/'a0.json',parent)
    write(out/'CONFIG_DIFF_CONT1.json',diff(parent,cfg))
    for n in ('diff_against_h1_1.json','diff_against_deployed.json'):
        write(ROOT/'configs'/n,diff(load(H/'build/fx/k/d12ae795.json'),cfg))
    proof=load(SNAP/'out/proof/inputs.json');proof.update(config_identity=b['config_identity'],config_sha256=sha(out/'config.json'),
        run_key=run,milestones=[400,600],stop_after_step=600,proof_partition='general')
    proof['required_checks']=sorted(set(proof['required_checks'])|{'resume_pointer'})
    write(out/'proof/inputs.json',proof)
    # Existing census and rows are unchanged; record that this is a same-input
    # reuse, then run the full native loader audit again against those inputs.
    from student_pilot import loader_audit,type_mix
    local=copy.deepcopy(cfg);local['type_mix']['streams'].pop('routing')
    local['preparation_output']=tempfile.mkdtemp(prefix='cont1_audit_',dir=ROOT/'work')
    local['continuation']=cfg['continuation']
    prepared=load(SNAP/'out/proof/local_prepared.json')
    prepared=type_mix.prepare(prepared,local)
    report=loader_audit.audit(local,prepared,local_vqa_only=True)
    prior=load(SNAP/'out/proof/loader_audit.json')
    for k in ('unit_counts','required_families','absent_on_P','limitations','executed_config_identity'):
        if k in prior:report[k]=prior[k]
    report['requested_config_identity']=b['config_identity'];report['continuation_population_source']=PARENT
    report['executed_config_identity']=identity(local)
    write(out/'proof/loader_audit.json',report)
    write(out/'proof/local_config.json',local);write(out/'proof/local_prepared.json',prepared)
    print(enc(dict(identity=b['config_identity'],run=run,token=token)))
if __name__=='__main__':main()
