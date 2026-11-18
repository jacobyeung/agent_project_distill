"""Bind the frozen packet to S2 without rebuilding its stores or selection."""
import copy,hashlib,sys
from pathlib import Path
from rebind import ROOT,AS,H,enc,load,write,sha,diff
from derive_deployment import identity,validate_switches

SNAPSHOT=Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_2c67f1f2')
FROZEN_ID='2c67f1f25114ab1324cee10b796e86afc79d01999ad3881860ab35710e7fee5d'
FROZEN_SHA='def1e1f2b1153328b024209e69fcbb71f2dd556b7376eacb836d40bb66d9845f'

def main():
    out=ROOT/'out';old=load(SNAPSHOT/'out/BINDING.json');cfg=load(SNAPSHOT/'out/config.json')
    if identity(cfg)!=FROZEN_ID or old['config_identity']!=FROZEN_ID:raise ValueError('Frozen config differs')
    for path in (SNAPSHOT/'out/p_6f8ed106.tar',out/'p_6f8ed106.tar'):
        if sha(path)!=FROZEN_SHA:raise ValueError('Frozen archive differs')
    # Authenticate the frozen comparison before the build. No snapshot is writable input.
    frozen={str(p.relative_to(SNAPSHOT)):sha(p) for p in SNAPSHOT.rglob('*')
            if p.is_file() and '__pycache__' not in p.parts}
    write(out/'FROZEN9.local.json',dict(snapshot=str(SNAPSHOT),files=frozen,
        protected_local_archive=dict(path='out/p_6f8ed106.tar',sha256=FROZEN_SHA)))
    for name in ('config.json','BINDING.json','r1p_code.tar','proof/selection/r.json',
                 'units/u.gz','units/packed.jsonl','units/i.json','units/m.json','units/u.json'):
        if sha(out/name)!=sha(SNAPSHOT/'out'/name):raise ValueError('Working input differs: '+name)
    seed={k:old[k] for k in ('tree_sha256','receipt_sha256','database_sha256','mix','traced_room_receipt','unit_binding')}
    switches=dict(S1=False,S2=True,max_own_probability=0);seed['launch_switches']=switches
    token=hashlib.sha256(enc(seed).encode()).hexdigest()[:8]
    run=hashlib.sha256(('run/'+token).encode()).hexdigest()[:8]
    if token in ('c5f3847d','6f8ed106') or run==old['run_key']:raise ValueError('Identity collision')
    before=copy.deepcopy(cfg)
    def relocate(value):
        if isinstance(value,dict):return {k:relocate(v) for k,v in value.items()}
        if isinstance(value,list):return [relocate(v) for v in value]
        if isinstance(value,str):return value.replace(AS+old['store_key']+'/',AS+token+'/')
        return value
    cfg=relocate(cfg);cfg['h1']['routing_pose_targets']=True
    for key in ('output','preparation_output'):cfg[key]=cfg[key].replace(old['run_key'],run)
    receipt=relocate(load(SNAPSHOT/'out/records/d.json'));write(out/'records/d.json',receipt)
    cfg['streams']['vqa']['sha256']=sha(out/'records/d.json')
    validate_switches(cfg);newid=identity(cfg)
    review=load(SNAPSHOT/'out/records/v.json');review['config_sha256']=newid
    write(out/'records/v.json',review);cfg['admission']['sha256']=sha(out/'records/v.json')
    sys.path[:0]=[str(ROOT/'work/tree'),str(ROOT/'work/tree/generator/derivgen_v7')]
    from student_pilot import carrier_c1_run as trainer
    trainer.validate(cfg)
    if trainer.identity(cfg)!=newid:raise ValueError('Trainer identity differs')
    binding=copy.deepcopy(old)
    binding.update(config_identity=newid,run_key=run,store_key=token,launch_switches=switches,
        deployment_receipt=dict(path=AS+token+'/d.json',sha256=sha(out/'records/d.json')),
        deployed_database=receipt['database'],job_name='a15_cot_ap'+run)
    write(out/'BINDING.json',binding);write(out/'config.json',cfg);write(ROOT/'configs/r1p.json',cfg)
    write(out/'CONFIG_DIFF9.json',diff(before,cfg))
    parent=load(H/'build/fx/k/d12ae795.json')
    for name in ('diff_against_h1_1.json','diff_against_deployed.json'):write(ROOT/'configs'/name,diff(parent,cfg))
    proof=load(SNAPSHOT/'out/proof/inputs.json')
    proof.update(config_identity=newid,config_sha256=sha(out/'config.json'),run_key=run,
                 store_receipt_sha256=sha(out/'records/d.json'))
    write(out/'proof/inputs.json',proof)
    # S2 does not enter the sampler. Preserve its frozen row census and plan;
    # the final-config CPU first-batch test executes that same plan again.
    local=copy.deepcopy(cfg);local['type_mix']['streams'].pop('routing')
    local['preparation_output']=load(SNAPSHOT/'out/proof/local_config.json')['preparation_output']
    write(out/'proof/local_config.json',local)
    prepared=load(SNAPSHOT/'out/proof/local_prepared.json');prepared['config_sha256']=newid
    write(out/'proof/local_prepared.json',prepared)
    audit=load(SNAPSHOT/'out/proof/loader_audit.json')
    audit.update(config_identity=newid,requested_config_identity=newid,executed_config_identity=identity(local),
        inherited_sampling_evidence=dict(config_identity=FROZEN_ID,sha256=sha(SNAPSHOT/'out/proof/loader_audit.json'),
            reason='Identical stores, type mix, recipe, selections and frame pins; S2 changes only target supervision. Census not rerun.'))
    write(out/'proof/loader_audit.json',audit)
    write(out/'REBIND9.local.json',dict(argv=sys.argv,source_config=FROZEN_ID,
        source_archive_sha256=FROZEN_SHA,config_identity=newid,token_seed=seed,
        preserved=['trainer tree','code archive','unit artifacts','routing selection','source stores','frame pins','type mix']))
    print(enc(dict(config_identity=newid,run_key=run,archive='p_'+token+'.tar',config_diff=diff(before,cfg))))

if __name__=='__main__':main()
