from pathlib import Path
import json,hashlib,difflib,ast
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';T=L/'work/tree_r1';O=B/'proofs/audit'
O.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[
 dict(keys=['lm_lr_scale','pose_lr_scale'],source='student_pilot/carrier_c1_run.py',lines=[2771,2772],rule='Absent equals 1.0; each scale must match.'),
 dict(keys=['steps','training_mode','recipe.warmup_ratio'],source='student_pilot/carrier_c1_sweep.py',lines=[52,82,99,106],rule='Compare effective recipe steps, warmup and group rates.'),
 dict(keys=['mdg.lr_scale','mdg.lora_lr'],source='student_pilot/carrier_c1.py',lines=[670,671,678],rule='Compare complete mdg configuration. LoRA weight decay is fixed at zero.'),
 dict(keys=['geometry_online.finetune.lr_scale','geometry_online.finetune.hold_steps','geometry_online.finetune.warmup_steps'],source='student_pilot/g3t_online.py',lines=[118,555,557],rule='Compare complete geometry_online configuration; R1 validation also refuses geometry extensions.'),
 dict(keys=['geometry_online.patch_fusion.align_steps'],source='student_pilot/carrier_c1_run.py',lines=[1569],rule='Compare complete geometry_online configuration.'),
 dict(keys=['geometry_online.gf1.stage','geometry_online.gf1.learning_rate'],source='student_pilot/gf1.py',lines=[186,195],rule='Compare complete geometry_online configuration.'),
 dict(keys=[],source='student_pilot/carrier_c1_run.py',lines=[2773],rule='AdamW uses the sealed RECIPE weight decay and default betas. No carrier config overrides either. Compare effective recipe weight decay and record fixed betas.'),
]
for row in records:
    row['source']='work/base/tree_b01ce449/'+row['source'];row['sha256']=sha(L/row['source'])
(O/'OPTIMIZER_INPUTS.json').write_text(json.dumps(dict(scope='Sealed carrier_c1_run training path and its transitive parameter-group/schedule functions; unrelated standalone trainers do not define the R1 optimizer.',records=records),indent=2))
old={name:h for h,name in (line.split('  ',1) for line in (B/'proofs/review_inputs/TREE_FILES.sha256').read_text().splitlines())}
current={str(p.relative_to(T)):sha(p) for p in T.rglob('*') if p.is_file() and not p.is_symlink() and not set(p.relative_to(T).parts)&{'.git','artifacts','__pycache__'}}
changed=[dict(file=n,build9fix_sha256=old.get(n),current_sha256=current.get(n)) for n in sorted(set(old)|set(current)) if old.get(n)!=current.get(n)]
(B/'DIFF_VS_BUILD9FIX.json').write_text(json.dumps(dict(source='work/n1fix2/proofs/review_inputs/TREE_FILES.sha256',files=changed),indent=2))
inputs=B/'inputs';list_pin=next(p for p in inputs.glob('*.json') if sha(p)=='02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411')
review=json.loads((B/'proofs/review_inputs/F6.json').read_text())
rows=list_pin.read_text().splitlines();assert len(rows)==review['kit_list_keys']==601
cfg=json.loads((inputs/'config.json').read_text());assert any(p['sha256']==sha(list_pin) for p in cfg['remove_files'])
division=Path(cfg['scene_division']['path']);assert division.is_relative_to(L) and sha(division)==cfg['scene_division']['sha256']
(O/'F6_PRESERVATION.json').write_text(json.dumps(dict(keys=len(rows),list_sha256=sha(list_pin),division_sha256=sha(division),source=str(list_pin.relative_to(L)),source_review='work/n1fix2/proofs/review_inputs/F6.json',admitted_inherited=review['vqa_with_list']['admitted'],full_census_rerun=False),indent=2))
old_mix=json.loads((L/'work/n1fix/inputs/mix.json').read_text());new_mix=json.loads((inputs/'mix.json').read_text())
def semantics(v):
    if isinstance(v,dict):return {k:semantics(x) for k,x in v.items() if k not in ('path','sha256')}
    if isinstance(v,list):return [semantics(x) for x in v]
    return v
assert semantics(old_mix)==semantics(new_mix)
(O/'MIX_PRESERVATION.json').write_text(json.dumps(dict(numeric_and_nonpin_content_identical=True,source='work/n1fix/inputs/mix.json',source_sha256=sha(L/'work/n1fix/inputs/mix.json'),current='work/n1fix2/inputs/mix.json',current_sha256=sha(inputs/'mix.json')),indent=2))
inference=json.loads((B/'inherited/proofs/audit/INFERENCE_COMPONENTS.json').read_text())
(O/'INFERENCE_COMPONENTS.json').write_text(json.dumps(inference,indent=2))
print(json.dumps(dict(changed_since_9fix=len(changed),list_keys=len(rows))))
