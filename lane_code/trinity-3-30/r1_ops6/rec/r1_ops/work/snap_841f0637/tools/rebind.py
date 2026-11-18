"""Bind a store receipt, size selector and mix; regenerate census, identity and proof inputs."""
import argparse,copy,hashlib,io,json,os,subprocess,sys,tarfile,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
AS='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/'
H=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1')

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
def load(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).parent.mkdir(parents=True,exist_ok=True,mode=0o700);Path(p).write_text(enc(x)+'\n')
def pin(p):return dict(path=str(Path(p).resolve()),sha256=sha(p))
def diff(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):
        out=[]
        for k in sorted(set(a)|set(b)):
            if k not in a or k not in b:out.append(dict(field=path+k,before=a.get(k),after=b.get(k)))
            else:out+=diff(a[k],b[k],path+k+'.')
        return out
    return [] if a==b else [dict(field=path.rstrip('.'),before=a,after=b)]

def main():
    os.umask(0o077)
    p=argparse.ArgumentParser();p.add_argument('--receipt',type=Path,required=True);p.add_argument('--receipt-sha256',required=True)
    p.add_argument('--database',type=Path);p.add_argument('--mix',type=Path,default=ROOT/'configs/mix.json')
    p.add_argument('--unit-rows',type=Path);p.add_argument('--unit-rows-sha256');p.add_argument('--unit-cents',type=int,default=287)
    p.add_argument('--proof-partition',choices=('advanced','general'),default='advanced')
    p.add_argument('--size-selector',type=Path);p.add_argument('--room-receipt',type=Path)
    p.add_argument('--orchard-store',default='/project/community/jjyeung/okh7/s_8805de22/d.db')
    p.add_argument('--out',type=Path,default=ROOT/'out');p.add_argument('--reuse-census',action='store_true');p.add_argument('--skip-audit',action='store_true')
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True,mode=0o700)
    if sha(a.receipt)!=a.receipt_sha256:raise ValueError('Source receipt SHA differs')
    receipt=load(a.receipt);db=a.database or Path(receipt['database']['path'])
    if sha(db)!=receipt['database']['sha256']:raise ValueError('Store SHA differs')
    census=out/'ADMISSION_BY_TYPE.json'
    if a.reuse_census:
        old=load(census)
        if old.get('status')!='COMPLETE_ROW_CENSUS' or old['receipt']['sha256']!=a.receipt_sha256 or old['database']['sha256']!=sha(db):raise ValueError('Census binding differs')
    else:
        subprocess.run([sys.executable,'-B',str(ROOT/'tools/admission_census.py'),'--receipt',str(a.receipt),'--receipt-sha256',a.receipt_sha256,'--database',str(db),'--out',str(census)],check=True)
    subprocess.run([sys.executable,'-B',str(ROOT/'tools/routing_diagnosis.py'),'--out',str(out)],check=True)
    subprocess.run([sys.executable,'-B',str(ROOT/'tools/selection_check.py'),'--out',str(out/'proof/selection')],check=True)
    sys.path[:0]=[str(ROOT/'work/tree'),str(ROOT/'work/tree/generator/derivgen_v7')]
    from student_pilot import carrier_c1_run as run,source_seal,type_mix,loader_audit,s1_pool
    from student_pilot.p3_provenance import source_files,digest
    from student_pilot.checkpoint_space import plan
    # The selector fingerprints its import closure, including the sampler modules.
    # Rebind that fingerprint to the actual sealed tree without changing row predicates.
    selected=load(out/'proof/selection/r.json');selected['implementation']=s1_pool.implementation()
    write(out/'proof/selection/r.json',selected)
    evidence=load(out/'proof/selection/q.json');evidence['selection_sha256']=sha(out/'proof/selection/r.json')
    evidence['implementation_rebound']=True;write(out/'proof/selection/q.json',evidence)
    mix=load(a.mix)
    if a.size_selector:mix['size_selector']=load(a.size_selector)
    if bool(a.unit_rows)!=bool(a.unit_rows_sha256):raise ValueError('Unit rows and SHA must be supplied together')
    if a.unit_cents<1:raise ValueError('Bound units require a positive requested dose')
    unit_binding=None
    if a.unit_rows:
        from unit_binding import build
        basecfg=load(H/'build/fx/k/d12ae795.json')
        selection_path=out/'proof/selection/r.json'
        selected,unit_binding=build(a.unit_rows,a.unit_rows_sha256,load(selection_path),load(ROOT/'work/records/pool_manifest.json'),
                                  basecfg['s1_routing']['catalog'],H/'build/fx/k',out/'units')
        write(selection_path,selected)
        evidence=load(out/'proof/selection/q.json');evidence.update(selection_sha256=sha(selection_path),unit_binding=unit_binding,
            selected_rows=selected['selected_rows'],native_unit_regeneration_executed=True)
        write(out/'proof/selection/q.json',evidence)
        mix['unit_rows']=unit_binding['source']
        cells=mix['streams']['routing']['cells'];dose=min(a.unit_cents,4*unit_binding['counts']['eligible']*100//1000)
        from student_pilot.vehicle_p import ROUTING
        weights={n:cells[n]['cents'] for n in ROUTING};total=sum(weights.values());remaining=6400-dose
        shares={n:remaining*weights[n]//total for n in ROUTING}
        for n in sorted(ROUTING,key=lambda n:(-(remaining*weights[n]%total),n))[:remaining-sum(shares.values())]:shares[n]+=1
        for n in ROUTING:cells[n]['cents']=shares[n]
        cells['units']['cents']=dose
    elif mix.get('unit_rows'):
        raise ValueError('Unit binding requires --unit-rows and --unit-rows-sha256; a mix pin alone is insufficient')
    tree=ROOT/'work/tree';files=source_seal.inventory(tree)
    binding=dict(tree_sha256=digest(files),receipt_sha256=a.receipt_sha256,database_sha256=receipt['database']['sha256'],mix=mix,
                 traced_room_receipt=pin(a.room_receipt) if a.room_receipt else None,unit_binding=unit_binding)
    token=hashlib.sha256(enc(binding).encode()).hexdigest()[:8];runkey=hashlib.sha256(('run/'+token).encode()).hexdigest()[:8]
    store_base=AS+token+'/';record=out/'records';record.mkdir(exist_ok=True,mode=0o700)
    deployed=copy.deepcopy(receipt);deployed['database']['path']=store_base+'d.db'
    # Keep immutable producer receipt bytes as provenance; only deployment receipt paths change.
    producer_name='d_'+a.receipt_sha256[:16]+'.json';(record/producer_name).write_bytes(a.receipt.read_bytes())
    deployed['source']=dict(path=store_base+producer_name,sha256=a.receipt_sha256)
    write(record/'d.json',deployed)
    config=load(H/'build/fx/k/d12ae795.json');parent=copy.deepcopy(config)
    config['h1'].update(faithful_own_camera_rows=False,routing_pose_targets=False,stop_after_step=200)
    ss=load(ROOT/'work/reference/configs/d0.json')['scheduled_sampling']
    config['scheduled_sampling']=ss;config['recipe']['scheduled_sampling']=copy.deepcopy(ss)
    config['milestones']=config['recipe']['milestones']=[100,200]
    config['output']=AS+'8865619b/runs/'+runkey;config['preparation_output']=AS+'8865619b/f/'+runkey
    config['streams']['vqa']=dict(path=store_base+'d.json',sha256=sha(record/'d.json'))
    for name in ('room_size_estimation','absolute_size_room'):config['route_table'][name]='direct'
    write(record/'j.json',selected['implementation'])
    write(record/'r.json',config['route_table']);config['s1_route_policy']['table']=dict(path=store_base+'r.json',sha256=sha(record/'r.json'))
    selection=out/'proof/selection/r.json';sp=dict(path=store_base+'s.json',sha256=sha(selection))
    config['s1_routing']['selection']=sp;config['s1_routing']['catalog'][sp['sha256']]=sp['path']
    if unit_binding:
        for value in unit_binding['artifacts'].values():config['s1_routing']['catalog'][value['sha256']]=value['path']
    config['type_mix']=mix
    config['checkpoint_disk_guard']=plan(config['recipe'],config['checkpoint_disk_guard']['reserve_bytes'])
    archive=out/'r1p_code.tar'
    with tarfile.open(archive,'w') as tf:
        for name in sorted(files):
            raw=(tree/name).read_bytes();entry=tarfile.TarInfo(name);entry.size=len(raw)
            entry.mode=0o755 if os.access(tree/name,os.X_OK) else 0o644;tf.addfile(entry,io.BytesIO(raw))
    sources={str(f.relative_to(tree)):sha(f) for f in source_files([tree/'student_pilot/carrier_c1_run.py'])}
    code=source_seal.create(tree,archive,sources,sources,archive_path=AS+'8865619b/k/t_'+digest(files)[:16]+'.tar')
    write(record/'c.json',code);config['code']=dict(path=store_base+'c.json',sha256=sha(record/'c.json'))
    run.validate(config)
    identity=run.identity(config)
    # Review does not enter identity and cannot be inherited from another tree.
    review=dict(schema='r1-independent-review-required-v1',verdict='PENDING',config_sha256=identity,tree_sha256=code['tree_sha256'])
    write(record/'v.json',review);config['admission']=dict(path=store_base+'v.json',sha256=sha(record/'v.json'))
    assert run.identity(config)==identity
    write(ROOT/'configs/r1p.json',config);write(ROOT/'configs/diff_against_h1_1.json',diff(load(ROOT/'work/reference/configs/h1_1.json'),config))
    write(ROOT/'configs/diff_against_deployed.json',diff(parent,config));write(out/'config.json',config)
    binding.update(config_identity=identity,run_key=runkey,store_key=token,record_files=sorted(['c.json','d.json','j.json','r.json','v.json',producer_name]),source_receipt=pin(a.receipt),database=pin(db),
        deployment_receipt=dict(path=store_base+'d.json',sha256=sha(record/'d.json')),orchard_store=a.orchard_store,
        deployed_database=deployed['database'],code_sha256=sha(record/'c.json'),tree_sha256=code['tree_sha256'],
        code_archive_sha256=sha(archive),code_archive_name=Path(code['archive']['path']).name,selection_sha256=sp['sha256'],
        job_name='a15_cot_ap'+runkey,production_authorized=False,proof_partition=a.proof_partition,
        blockers=['production_preparation_not_run','independent_review_pending'])
    from student_pilot.vehicle_p import absent_on_p
    binding['absent_on_P']=absent_on_p(config)
    binding['units_status']='BOUND' if unit_binding else 'UNBOUND_ZERO_DOSE'
    write(out/'BINDING.json',binding)
    proof=dict(config_identity=identity,config_sha256=sha(out/'config.json'),tree_sha256=code['tree_sha256'],
        selection_sha256=sp['sha256'],disk_plan=config['checkpoint_disk_guard'],milestones=[100,200],stop_after_step=200,
        store_receipt_sha256=sha(record/'d.json'),database_sha256=receipt['database']['sha256'],run_key=runkey,
        required_checks=['disk_plan','routing_selection','empty_root','temporary_paths','runtime_binaries','private_directories','loader_audit','required_families'],
        production_preparation='NOT_RUN',production_authorized=False,absent_on_P=binding['absent_on_P'],proof_partition=a.proof_partition)
    write(out/'proof/inputs.json',proof)
    if not a.skip_audit:
        local=copy.deepcopy(config);local['type_mix']['streams'].pop('routing');local['preparation_output']=tempfile.mkdtemp(prefix='audit_',dir=ROOT/'work')
        ids=sorted(i for vals in load(ROOT/'work/admitted_indices.json').values() for i in vals)
        index_path=Path(local['preparation_output'])/'i.json';write(index_path,ids)
        prepared=dict(config_sha256=identity,streams={'vqa':dict(database=pin(db),count=len(ids),indices=pin(index_path)),
            **{s:dict(count=1,local_placeholder=True) for s in ('pose','routing','pointing')}})
        prepared=type_mix.prepare(prepared,local)
        report=loader_audit.audit(local,prepared,local_vqa_only=True)
        report['executed_config_identity']=run.identity(local)
        report['requested_config_identity']=identity
        report['limitations']=['Only vqa is present locally; pose, routing and pointing counts are placeholders excluded from this audit.',
            'RGB bytes and full production admission were not run. Production proof must audit every staged stream.']
        from student_pilot.vehicle_p import required_families
        if unit_binding:report['unit_counts']=unit_binding['counts']
        report['required_families']=required_families(config,report,local_selection=load(selection))
        report['absent_on_P']=binding['absent_on_P']
        write(out/'proof/loader_audit.json',report)
        write(out/'proof/local_prepared.json',prepared)
        write(out/'proof/local_config.json',local)
        arows=load(census);arows['vqa_by_family']=report['eligible_by_family']['vqa'];arows['post_filter_by_type']=report['eligible_by_question_type']['vqa'];arows['mix_caps']=report['tables']['vqa'];write(census,arows)
        table=['| Cell | Eligible | Proposed/step | Cap/step | Cut | Refill | Final/step |','|---|---:|---:|---:|---:|---:|---:|']
        for name,v in report['tables']['vqa'].items():table.append('| '+name+' | '+str(v['eligible'])+' | '+' | '.join(f"{v[k]/100:.2f}" for k in ('proposed_cents','cap_cents','cut_cents','refill_cents','final_cents'))+' |')
        (out/'MIX.md').write_text('Vehicle P caps each cell at four times its eligible population over 1,000 steps. Direction is 32.89 rows per step. Size and room have zero launch dose; size rows remain in the store. Recovery is absent on P and joins N. Units have zero dose until a faithful file is bound.\n\n'+'\n'.join(table)+'\n\nRouting uses the same capped allocator after native preparation. The production proof measures its final populations, caps, cuts and sampling shares.\n')
        routing_caps={}
        for name in ('recovery','units'):
            count=unit_binding['counts']['eligible'] if name=='units' and unit_binding else 0
            proposed=mix['streams']['routing']['cells'][name]['cents'];cap=4*count*100//1000
            routing_caps[name]=dict(eligible_in_bound_source=count,proposed_cents=proposed,cap_cents=cap,
                                    cut_cents=max(0,proposed-cap),production_stream_bound=bool(name=='units' and unit_binding))
        arows['routing_slice_caps']=routing_caps;arows['absent_on_P']=binding['absent_on_P'];arows['bound_units']=unit_binding;write(census,arows)
        with (out/'MIX.md').open('a') as f:
            f.write('\n| Routing cell | Requested/step | Bound unit source cap/step |\n|---|---:|---:|\n')
            for name,v in mix['streams']['routing']['cells'].items():
                cap=f"{routing_caps[name]['cap_cents']/100:.2f}" if name in routing_caps else 'Production proof'
                f.write(f"| {name} | {v['cents']/100:.2f} | {cap} |\n")
            f.write('\nPose stays at 64 rows/step and pointing at 32. Routing refills its four native cells proportionally under their caps. Bound unit counts below 100 in cm, ft or in fail the required-family gate.\n')
        traces=[]
        for stream,groups in report['traces'].items():
            for name,examples in groups.items():
                for row in examples:traces.append(dict(stream=stream,family=name,**row))
        with (out/'proof/traces.jsonl').open('w') as f:
            for row in traces:f.write(enc(row)+'\n')
    subprocess.run([sys.executable,'-B',str(ROOT/'tools/make_proof.py'),'--out',str(out)],check=True)
    subprocess.run([sys.executable,'-B',str(ROOT/'tools/package_operator.py'),'--out',str(out)],check=True)
    print(enc(dict(status='BUILT_BLOCKED',config_identity=identity,run_key=runkey,output=str(out))))
if __name__=='__main__':main()
