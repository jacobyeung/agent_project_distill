"""Record every changed fixture input field and check the prepared handoff."""
from pathlib import Path
import ast, json, sys, hashlib

L=Path(__file__).resolve().parents[2];D=L/'work/build24f';R=D/'rehearsal2';old=D/'rehearsal'
sys.path.insert(0,str(L/'work/build24'))
import joblib as J
changes=[]
def diff(before,after,field):
    if isinstance(before,dict) and isinstance(after,dict):
        for k in sorted(set(before)|set(after)):
            if k not in before or k not in after:
                changes.append(dict(field=field+'.'+k,before=before.get(k),after=after.get(k)))
            else:diff(before[k],after[k],field+'.'+k)
    elif before!=after:
        changes.append(dict(field=field,before=before,after=after))

for name in ('input.json','r.json','r2.json','n.json','v.json','prepared.json','PREPARED.json','VIEW.json'):
    diff(J.load(old/name),J.load(R/name),name)
single=J.load(R/'SINGLE_PROCESS.json');assert single['status']=='PASS'
assert single['production_meta_alias'] is False
production=J.load(R/'PRODUCTION_EVIDENCE.json')
kit=J.load(L/'out/kit_n_go/k/n.json')
assert kit['r1_training']['handover_receipt']['sha256']==production['export_receipt']['sha256']
assert kit['base_identity']==production['base_identity']
assert kit['world_size']==4 and kit['parallel']=='fsdp'
failure='RuntimeError: size mismatch, got input (1), mat (1x4), vec (248064)'
failure_count=(old/'train_fresh.log').read_text().count(failure)
assert failure_count>=4
J.write(R/'CAUSE_EVIDENCE.json',dict(
    observed_error=failure,occurrences=failure_count,source=str(old/'train_fresh.log'),
    tiny_weight_shape=[248064,4],four_rank_flat_shard_elements=248064*4//4,
    native_policy='work/tree_r1/student_pilot/full_ft.py:332-343',
    pose_touch='work/tree_r1/student_pilot/carrier_c1.py:562',
    warm_load_preserves_parameter_identity='work/tree_r1/student_pilot/carrier_c1_run.py:1052 parameter.copy_',
    torch_shared_parameter_rule='/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/distributed/fsdp/wrap.py:306-308',
    torch_excludes_managed_parameters='/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/distributed/fsdp/_init_utils.py:1153-1169',
    torch_flat_shard_views='/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/distributed/fsdp/_flat_param.py:2131-2166'))
stages=J.load(R/'STAGES.json')
assert [v['stage'] for v in stages]==['canary','rooms','v_config','fixture_gates']
assert all(v['returncode']==0 for v in stages)
assert not list(R.glob('*rank*.json'))
assert not (R/'train').exists()
assert J.load(R/'p2/q/RESULT.json')['status']=='ADMIT'
assert J.load(R/'gates.json')['status']=='PASS'
source_files=['make_rehearsal.py','make_rehearsal2.py','rehearsal_model.py','rehearsal_repro.py',
    'rehearsal_runner.py','rehearsal_boundary.py','rehearsal_cpu_python','rehearsal_gates.py',
    'rehearsal_copier.py','check_rehearsal.py','check_rehearsal_fix.py','rehearsal_authorize.py','rehearsal_handoff.py']
for name in source_files:ast.parse((D/name).read_text(),filename=name)
values=J.load(D/'FIXTURE_DIFF.json')
values['build24fr']=dict(
    scope='CPU fixture only; all native functions and production inputs unchanged',
    model_boundary='After native tied donor load; before optimizer and FSDP; original pinned base/donor files remain authenticated and unchanged',
    fields=[
        dict(field='effective_model.config.tie_word_embeddings',before=True,after=False,production=False),
        dict(field='effective_model.config.text_config.tie_word_embeddings',before=True,after=False,production=False),
        dict(field='effective_model.lm_head.weight identity/storage',before='same Parameter as input embedding',after='independent cloned Parameter, exactly equal initial values',production='independent Parameter'),
        dict(field='effective_model.full_ft_report.base_parameters',before=single['parameters_before'],after=single['parameters_after']),
        dict(field='effective_model.full_ft_report.trainable_parameters',before=992686,after=1984942),
        dict(field='effective_model.full_ft_report.group_parameters.llm',before=992686,after=1984942),
        dict(field='physical_output_root',before=str(old),after=str(R)),
        dict(field='TMPDIR and cache roots',before=str(L/'work/tmp'),after=str(R/'tmp')),
        dict(field='existing bwrap bind modes',before='read/write',after='read-only; rehearsal2 remains read/write'),
        dict(field='launcher preflight',before=None,after='four-rank CPU/gloo tied/untied reproduction'),
        dict(field='fixture host/review staging order',before='after h.py',after='before native h.py plus native entry refusal tests'),
        dict(field='h.py in-memory control.review',before=None,after=J.load(R/'handoff_boundary.json')['control_review_override']),
    ]+changes,
    retained_fields='Native recipe, admission, legality, row stores, initialization receipt and trained groups are unchanged; no training results are prepopulated.',
    production_evidence='rehearsal2/PRODUCTION_EVIDENCE.json',
    single_process_evidence='rehearsal2/SINGLE_PROCESS.json',
    external_evidence_expected=['rehearsal2/repro_tied.json','rehearsal2/repro_untied.json','rehearsal2/CHECK.json'])
J.write(D/'FIXTURE_DIFF.json',values)
J.write(R/'FIX_VALIDATION.json',dict(status='PASS',prepared_stages=stages,
    changed_input_fields=len(changes),python_syntax_files=len(source_files),
    training_executed=False,distributed_reproduction_executed=False,
    sources={name:J.sha(D/name) for name in source_files+['go_rehearsal.sh']},
    original_failure=str(old/'train_fresh.log')))
print(f'PASS: preparation stages, single-process ownership, syntax; {len(changes)} changed input fields recorded; distributed execution pending.')
