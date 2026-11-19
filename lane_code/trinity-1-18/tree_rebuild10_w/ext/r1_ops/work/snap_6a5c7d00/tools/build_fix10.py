"""Bind the division REMOVE list and capped cells without changing sealed inputs."""
import copy,hashlib,sys,tempfile
from pathlib import Path
from rebind import ROOT,AS,H,enc,load,write,sha,diff,pin
from derive_deployment import identity,validate_switches
SNAPS={'A':'8246a4dd','B':'2c67f1f2'}
def main():
    variant=sys.argv[1] if len(sys.argv)>1 else 'A'
    snapshot=Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_'+SNAPS[variant]);out=ROOT/'out'
    old=load(snapshot/'out/BINDING.json');before=load(snapshot/'out/config.json');cfg=copy.deepcopy(before)
    removal=out/'records/n.json';h=sha(removal)
    mix=copy.deepcopy(old['mix']);cells=mix['streams']['vqa']['cells'];room=425*4*100//1000
    cells['direction']['cents']+=cells['room']['cents']-room;cells['room']['cents']=room
    seed=dict(parent=old['config_identity'],remove_sha256=h,mix=mix)
    token=hashlib.sha256(enc(seed).encode()).hexdigest()[:8];runkey=hashlib.sha256(('run/'+token).encode()).hexdigest()[:8]
    assert token not in ('c5f3847d','6f8ed106','082d2d90') and token!=old['store_key']
    def relocate(v):
        if isinstance(v,dict):return {k:relocate(x) for k,x in v.items()}
        if isinstance(v,list):return [relocate(x) for x in v]
        if isinstance(v,str):return v.replace(AS+old['store_key']+'/',AS+token+'/')
        return v
    cfg=relocate(cfg);cfg['type_mix']=mix
    cfg['remove_files'].append(dict(path=AS+token+'/n.json',sha256=h))
    for k in ('output','preparation_output'):cfg[k]=cfg[k].replace(old['run_key'],runkey)
    receipt=relocate(load(snapshot/'out/records/d.json'));write(out/'records/d.json',receipt)
    cfg['streams']['vqa']['sha256']=sha(out/'records/d.json')
    validate_switches(cfg);newid=identity(cfg)
    review=load(snapshot/'out/records/v.json');review['config_sha256']=newid
    write(out/'records/v.json',review);cfg['admission']['sha256']=sha(out/'records/v.json')
    sys.path[:0]=[str(ROOT/'work/tree'),str(ROOT/'work/tree/generator/derivgen_v7')]
    from student_pilot import carrier_c1_run as trainer
    trainer.validate(cfg);assert trainer.identity(cfg)==newid
    binding=copy.deepcopy(old)
    binding.update(config_identity=newid,run_key=runkey,store_key=token,mix=mix,
        launch_switches=dict(S1=False,S2=cfg['h1']['routing_pose_targets'],max_own_probability=0),
        deployment_receipt=dict(path=AS+token+'/d.json',sha256=sha(out/'records/d.json')),
        deployed_database=receipt['database'],job_name='a15_cot_ap'+runkey,
        record_files=sorted(set(old['record_files'])|{'n.json'}),division_removal=dict(rows=601,sha256=h),
        traced_room_eligibility={**old['traced_room_eligibility'],'eligible':425})
    write(out/'BINDING.json',binding);write(out/'config.json',cfg);write(ROOT/'configs/r1p.json',cfg)
    write(out/'CONFIG_DIFF10.json',diff(before,cfg))
    write(out/'FIX10_VARIANT.json',dict(variant=variant,snapshot=str(snapshot),parent_identity=old['config_identity'],token_seed=seed))
    parent=load(H/'build/fx/k/d12ae795.json')
    for n in ('diff_against_h1_1.json','diff_against_deployed.json'):write(ROOT/'configs'/n,diff(parent,cfg))
    proof=load(snapshot/'out/proof/inputs.json');proof.update(config_identity=newid,config_sha256=sha(out/'config.json'),run_key=runkey,store_receipt_sha256=sha(out/'records/d.json'))
    write(out/'proof/inputs.json',proof)
    print(enc(dict(variant=variant,config_identity=newid,run_key=runkey,archive='p_'+token+'.tar')))
if __name__=='__main__':main()
