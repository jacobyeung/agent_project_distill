"""Record complete fixture-field differences and validate the prepared handoff."""
from pathlib import Path
import sys,ast,json
L=Path(__file__).resolve().parents[2];D=L/'work/build24f';R=D/'rehearsal3';old=D/'rehearsal2'
sys.path.insert(0,str(L/'work/build24'));import joblib as J
changes=[]
def diff(a,b,path):
    if isinstance(a,dict) and isinstance(b,dict):
        for k in sorted(set(a)|set(b)):
            if k not in a or k not in b:
                changes.append(dict(field=path+'.'+k,before=a.get(k),after=b.get(k),
                    before_present=k in a,after_present=k in b))
            else:diff(a[k],b[k],path+'.'+k)
    elif a!=b:changes.append(dict(field=path,before=a,after=b))
gen=J.load(R/'GENERATION.json');single=J.load(R/'SINGLE_PROCESS_GROUPS.json')
assert gen['status']==single['status']=='PASS'
assert J.load(R/'PRODUCTION_GROUPS.json')['status']=='PASS'
assert J.load(R/'METADATA_PRESERVED.json')['status']=='PASS'
stages=J.load(R/'STAGES.json')
assert [x['stage'] for x in stages]==['canary','rooms','v_config','fixture_gates']
assert all(x['returncode']==0 for x in stages)
assert J.load(R/'p2/q/RESULT.json')['status']=='ADMIT'
assert not (R/'train').exists()
generated_bytes=sum(p.stat().st_size for p in R.rglob('*') if p.is_file())
assert generated_bytes<300_000_000, 'Fixture exceeds the inherited 300 MB growth bound'
oldcfg=J.load(old/'input.json');oldprep=J.load(old/'prepared.json')
oldartifact=J.load(oldcfg['init_artifact']['artifact']['path'])
oldmodel=J.load(oldprep['model']['path'])
pairs={
 'donor/config.json':Path(oldcfg['r1_training']['p_run']['config']['path']),
 'donor/preparation.json':Path(oldcfg['r1_training']['p_run']['preparation']['path']),
 'donor/binding.json':Path(oldcfg['r1_training']['p_run']['binding']['path']),
 'donor/receipt.json':Path(oldcfg['r1_training']['handover_receipt']['path']),
 'donor/export/artifact.json':Path(oldcfg['init_artifact']['artifact']['path']),
 'donor/export/full_weights/full_weights.json':Path(oldartifact['full_weights']['path']),
 'donor/export/full_weights/model.safetensors.index.json':Path(oldartifact['full_weights']['path']).parent/'model.safetensors.index.json',
 'donor/mapping.json':Path(oldcfg['r1_training']['handover_mapping']['path']),
 'model.json':Path(oldprep['model']['path']),
 'model/config.json':Path(oldmodel['root'])/'config.json',
 'model/generation_config.json':Path(oldmodel['root'])/'generation_config.json',
}
evidence={'PRODUCTION_GROUPS.json','CAUSE_GROUPS.json','DONOR_GROUPS.json','GENERATION.json',
          'SINGLE_PROCESS_GROUPS.json','FIX2_VALIDATION.json','seed.json','STAGES.json'}
files=[]
for p in sorted(R.rglob('*.json')):
    relative=str(p.relative_to(R))
    if relative in evidence or relative.startswith(('tmp/','p2/s/')) or p.name.startswith('tokenizer'):continue
    before=pairs.get(relative,old/relative)
    if not before.exists() and '/prepare_' in relative:
        prefix,tail=relative.split('/prepare_',1);suffix=tail.split('/',1)[1]
        candidates=list((old/prefix).glob('prepare_*/'+suffix))
        if len(candidates)==1:before=candidates[0]
    previous=J.load(before) if before.exists() else {}
    current=J.load(p)
    diff(previous,current,relative)
    files.append(dict(path=relative,before_path=str(before) if before.exists() else None,
        before_sha256=J.sha(before) if before.exists() else None,after_sha256=J.sha(p)))
cause=J.load(R/'CAUSE_GROUPS.json');diff(cause['source'],single['source'],'donor.trainable_group_table')
assert cause['target']==single['target']
import torch,hashlib
from safetensors.torch import load_file
torch.set_num_threads(2)
binary=[]
oldweights=J.load(oldartifact['full_weights']['path'])
oldshard=Path(oldartifact['full_weights']['path']).parent/oldweights['files'][0]['name']
newweights=J.load(R/'donor/export/full_weights/full_weights.json')
assert oldweights['training']['group_parameters']['llm']==992686
assert newweights['training']['group_parameters']['llm']==1984942
observed=(old/'train_fresh.log').read_text().count('P_EXPORT_TRAINABLE_GROUP_MISMATCH')
assert observed>=4
newshard=R/'donor/export/full_weights'/newweights['files'][0]['name']
assert J.sha(newshard)==J.sha(R/'donor/export_legacy/full_weights'/newweights['files'][0]['name'])
assert J.sha(R/'donor/export/heads.pt')==J.sha(R/'donor/export_legacy/heads.pt')
for label,before,after in [('base',Path(oldmodel['root'])/'model.safetensors',R/'model/model.safetensors'),
                          ('export',oldshard,newshard)]:
    a,b=load_file(before),load_file(after)
    for name in sorted(set(a)|set(b)):
        if name in a and name in b and torch.equal(a[name],b[name]):continue
        def description(t):
            if t is None:return None
            return dict(shape=list(t.shape),dtype=str(t.dtype),
                        sha256=hashlib.sha256(t.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest())
        entry=dict(field=label+'.tensor.'+name,before=description(a.get(name)),after=description(b.get(name)))
        changes.append(entry);binary.append(entry)
    assert set(a)<=set(b) and all(torch.equal(v,b[k]) for k,v in a.items())
    assert set(b)-set(a)=={'lm_head.weight'}
    assert torch.equal(b['lm_head.weight'],b['model.language_model.embed_tokens.weight'])
summaries=[]
for a,b in zip(cause['source']['groups'],cause['target']['groups']):
    if a!=b:
        summaries.append(dict(name=a['name'],source_tensors=a['tensors'],target_tensors=b['tensors'],
          source_parameters=a['parameters'],target_parameters=b['parameters'],
          added_members=[x for x in b['members'] if x not in a['members']]))
assert len(summaries)==1 and summaries[0]['name']=='llm'
sources=['make_rehearsal3.py','make_rehearsal3_launch.py','rehearsal_preserve_metadata.py','rehearsal_inputs3.py','check_rehearsal_production.py',
 'check_rehearsal_groups.py','check_rehearsal_fix2.py','rehearsal_model.py','rehearsal_runner.py',
 'rehearsal_boundary.py','rehearsal_copier.py','check_rehearsal.py','rehearsal_repro.py']
for name in sources:ast.parse((D/name).read_text(),filename=name)
values=J.load(D/'FIXTURE_DIFF.json')
values['build24fr2']=dict(scope='Fixture only',fields=changes,files=files,group_difference=summaries,
 binary_changes=binary,
 construction=dict(base='Untied saved tiny base; original tokenizer bytes',
 donor='Authenticated warm-loaded tiny donor; clone head before native export, recompute full_ft accounting',
 receipt='Native p_export_receipt.produce over regenerated export and model preparation',
 preparation='Synthetic c1_pose_mix settings.model points to rehearsal3/model.json before native prepare validates it',
 target='Native authenticated load from untied base/export; no post-load parameter mutation'),
 control_fields=[dict(field='physical_output_root',before=str(old),after=str(R)),
 dict(field='post_load_untie',before=True,after=False),
 dict(field='REHEARSAL_OVERRIDES.model_boundary',before='Post-load clone of authenticated tied donor',
      after=J.load(D/'REHEARSAL_OVERRIDES.json')['model_boundary']),
 dict(field='REHEARSAL_OVERRIDES.copier.target',before='rehearsal2/target',after='rehearsal3/target'),
 dict(field='native_gate',before='Unchanged',after='Unchanged; positive and negative single-process checks')],
 sources={n:J.sha(D/n) for n in sources+['go_rehearsal.sh','check_rehearsal_groups.sh','REHEARSAL_OVERRIDES.json']},
 unchanged='Native code, kits, production configuration, admission, legality, source stores and row selections',
 production='rehearsal3/PRODUCTION_GROUPS.json',single_process='rehearsal3/SINGLE_PROCESS_GROUPS.json',
 distributed_training_executed=False)
J.write(D/'FIXTURE_DIFF.json',values)
J.write(R/'FIX2_VALIDATION.json',dict(status='PASS',stages=stages,changed_fields=len(changes),
    generated_bytes=generated_bytes,
    group_difference=summaries,observed_refusal=dict(path=str(old/'train_fresh.log'),occurrences=observed),
    distributed_training_executed=False,sources=values['build24fr2']['sources']))
print(json.dumps(dict(status='PASS',changed_fields=len(changes),group_difference=summaries)))
