from pathlib import Path
#!/usr/bin/env python3
"""Fill the step-600 pins, authenticate their closure, and reseal a launch kit.

Example: fill_m600.py --plan A --handover-dir POOL/h_6ed2c7aa/m600
    --listing LISTING.json --output-kit WORK/kits/n600
The listing contains objects (name, pool_path, bytes, sha256), export
(names, bytes, sha256), and model metadata (path or pool_path, bytes, sha256).
Plan B uses POOL/pb_a5416871 and exact published closure paths.
"""
from pathlib import Path
from copy import deepcopy
import argparse,json,shutil,sys
L=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(Path(__file__).resolve().parent), '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24u/work/tree_r1c']
import joblib as J
from kit import cap,reseal

def pin(p):return dict(path=str(p),sha256=J.sha(p),bytes=p.stat().st_size)

def fill(template,directory,listing,output,plan):
    template=Path(template).resolve();directory=J.exact_path(str(Path(directory).absolute()))
    listing=J.exact_path(str(Path(listing).absolute()));output=Path(output).resolve()
    if output.exists():raise ValueError('FILL_OUTPUT_EXISTS')
    J.seal(template);spec=deepcopy(J.load(template/'k/p.json'))
    if spec.get('step')!=600:raise ValueError('FILL_STEP600_TEMPLATE_REQUIRED')
    if plan not in ('A','B'):raise ValueError('FILL_PLAN_INVALID')
    relative='h_6ed2c7aa/m600' if plan=='A' else 'pb_a5416871'
    if not str(directory).endswith('/'+relative):raise ValueError('FILL_DIRECTORY_INVALID')
    hp=directory/'h.json';rp=directory/'RP.json';receipt=J.load(hp);run=J.load(rp)
    pins=J.receipt600(receipt,run)
    names=('h.json','RP.json','s.tar','DONE.json') if plan=='A' else ('h.json','RP.json','pb_report.json')
    files={name:pin(J.exact_path(str(directory/name))) for name in names}
    lv=J.load(listing);export=lv.get('export')
    if not isinstance(export,dict) or set(export)!={'names','bytes','sha256'}:raise ValueError('FILL_EXPORT_PIN_REQUIRED')
    if export['names']!=[x['name'] for x in lv['objects']]:raise ValueError('FILL_EXPORT_PARTS_DIFFER')
    if any('6ed2c7aa_m600.tar' not in name for name in export['names']):raise ValueError('FILL_EXPORT_NAME')
    spec.update(step=600,milestone=relative,p_run=run,handover=dict(plan=plan,files=files,l0=pin(listing),export=export))
    if plan=='A':values,metadata=J.small_archive(directory/'s.tar',600)
    else:values,metadata=J.local_metadata(spec,receipt,lv)
    runtime,preparation=J.identities(spec,run,pins,values,metadata)
    J.checkpoint600(receipt,run,values,metadata)
    model=J.metadata_at(values,metadata,preparation['model'])
    cfg=deepcopy(J.load(template/'k/n.json'));before=deepcopy(cfg)
    cfg['init_artifact']['artifact']=pins['artifact']
    cfg['r1_training'].update(p_run=run,handover_receipt=dict(path=str(hp),sha256=files['h.json']['sha256']),
        persisted_files={p['sha256']:p['path'] for p in pins.values()},proof_mode='train',donor_config_sha256=spec['p_runtime_identity'])
    cfg['streams']['routing']=runtime['streams']['routing'];cfg['s1_routing']=runtime['s1_routing']
    # All other settings, including VQA bindings, must remain byte-equivalent as values.
    scrub=lambda c:{k:v for k,v in c.items() if k not in ('init_artifact','r1_training','streams','s1_routing')}
    assert scrub(cfg)==scrub(before)
    allowed={'p_run','handover_receipt','persisted_files','proof_mode','donor_config_sha256'}
    assert {k:v for k,v in cfg['r1_training'].items() if k not in allowed}=={k:v for k,v in before['r1_training'].items() if k not in allowed}
    assert {k:v for k,v in cfg['streams'].items() if k!='routing'}=={k:v for k,v in before['streams'].items() if k!='routing'}
    shutil.copytree(template,output)
    cap(output,'k/p.json',spec);cap(output,'k/n.json',cfg)
    portable=J.load(output/'k/c.json')
    portable['init_artifact']['artifact']=dict(pins['artifact'],path=spec['namespace']+'/u/'+pins['artifact']['sha256'])
    portable['r1_training'].update({k:cfg['r1_training'][k] for k in allowed})
    portable['streams']['routing']=dict(cfg['streams']['routing'],path=spec['namespace']+'/u/'+cfg['streams']['routing']['sha256'])
    cap(output,'k/c.json',portable)
    request=J.load(output/'k/r.json');request.update(milestone=600,routing_base=cfg['streams']['routing']);cap(output,'k/r.json',request)
    seal=reseal(output)
    pool=directory.parents[1] if plan=='A' else directory.parent
    resolved=J.resolve(output,pool,listing,output.parent/(output.name+'_resolved.json'))
    record=dict(GO=False,kit=str(output),kit_seal=seal,tree_seal=J.load(output/'k/a.json')['source']['tree_sha256'],plan=plan,
        filled=dict(export=export,artifact=pins['artifact'],handover=files['h.json'],persisted_files=cfg['r1_training']['persisted_files'],
            checkpoint={k:v for k,v in pins.items() if k=='checkpoint' or k.startswith('checkpoint/')},
            model_manifest=preparation['model'],model_files=model['files']),
        unchanged=['tree','identity_algorithms','VQA_bindings','MINIMAL_declaration','card','removals','opener','lineage','component_boundaries'])
    base_inventory=J.load(L/'work/build24/UPLOADS_n.json')
    upload_rows=[]
    for item in base_inventory['files']:
        item=deepcopy(item)
        if item['opaque_name'].startswith('n/'):
            source=output/item['opaque_name'][2:]
            item.update(local_path=str(source),sha256=J.sha(source),bytes=source.stat().st_size)
        upload_rows.append(item)
    J.write(output.parent/(output.name+'_uploads.json'),dict(files=upload_rows,total_bytes=sum(x['bytes'] for x in upload_rows)))
    J.write(output.parent/(output.name+'_fill.json'),record)
    return record

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',choices=['A','B'],required=True)
    p.add_argument('--handover-dir',required=True);p.add_argument('--listing',required=True)
    p.add_argument('--template',default=str(L/'work/build24/kits/n'));p.add_argument('--output-kit',required=True)
    a=p.parse_args();print(json.dumps(fill(a.template,a.handover_dir,a.listing,a.output_kit,a.plan),indent=2))
