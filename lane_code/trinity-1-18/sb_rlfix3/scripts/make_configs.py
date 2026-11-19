"""Write unbound four/eight-H100 configs and a reproducible token-count estimate."""
import json
from pathlib import Path
from rl_on_n import provenance as P
from rl_on_n.serving import default_binding,load_binding,PINS
load_binding()
ROOT=Path(__file__).resolve().parents[1]
N=Path('/scratch/jjyeung/orch_n30/sb_f64/pkg/work/tree_r1')
P.sha(ROOT/'scripts/make_configs.py')
P.sha(ROOT/'in/b09_out/CARD_DRAFT_RL_DRYRUN.md')
P.sha(N/'student_pilot/r1_training.py');P.sha(N/'student_pilot/r1_rooms.py')
P.sha(N.parents[1]/'work/build18/inputs/config.json')
P.sha('/scratch/jjyeung/orch_n30/sb_f64/in/qwen35_9b_meta/config.json')
pin=P.load(P.checked(default_binding()['export_pin']));n_export=P.load(ROOT/'out/N_EXPORT_CHECK.json')
registry=N.parents[1]/'work/n1fix2/inputs/registry.json';init=P.load(registry)['init_m544']
d='/scratch/jjyeung/b01ec87a6f29b/d'
MISSING={
    'export_restore':dict(expected=f'{d}/e/RESTORE.json on orchard-community-4, the m200 restore A4 read; this path on trinity-1-18 holds an m544 restore',
        hash_source=f"sha256 recorded at staging; its original artifact/heads/full_weights must equal EXPORT_PIN.json {pin['artifact']['sha256']}/{pin['heads']['sha256']}/{pin['full_weights']['sha256']} and the replay receipt's export_identity"),
    'export_config':dict(expected=f"{d}/{pin['preparation']['config']['path']} (EXPORT_PIN.json preparation.config.path); absent on trinity-1-18",
        hash_source=f"{pin['preparation']['config']['sha256']} from EXPORT_PIN.json preparation.config.sha256"),
    'pool':dict(expected=str(ROOT/'out/PROMPT_POOL.json')+' with status ADMITTED, written by python -m rl_on_n.pool --config <pool_config>',
        hash_source='sha256 of that receipt after admission; the current file has status MISSING'),
    'pool_config':dict(expected=f"the qualified N training config given to rl_on_n.pool --config; init_m544 in {registry} has record {json.dumps(init['record'])} and status {init['status']}",
        hash_source='PROMPT_POOL.json source_config.sha256, which validate_pool requires to equal this file'),
    'grounding.artifact_manifest':dict(expected=str(ROOT/'out/ARTIFACT_BINDING.json')+' {root,name,sha256,code_roots} with reader/tree/heads/runner roots under in/claimed_reader; A4\'s d/binding.json binds /p and is refused',
        hash_source=f"sha256 of the binding at creation; its g3t/sam3/selector_head files must equal INPUTS.json {PINS['inputs'][1]} files.{{g3t,sam,selector}}_*"),
    'greedy_replay':dict(expected=str(ROOT/'out/GREEDY_REPLAY.json')+' (greedy_replay.py --out default)',
        hash_source='sha256 of its 26-item PASS receipt; its export_identity must equal export_restore'),
    'n_export_journal':dict(expected='an A4-reader journal of any N export training should start from; A4\'s load_native refuses N exports ('+n_export['finding']+')',
        hash_source='named by the orchestrator'),
}
for world in (4,8):
    cfg=dict(schema='rl-on-n-v2',status='MISSING_PRODUCTION_BINDINGS',tree_root=str(N),world_size=world,
        export_restore=None,export_config=None,pool_config=None,pool=None,missing_bindings=MISSING,output=str(ROOT/f'out/production_{world}h100'),
        steps=200,seed=17,cpu_threads=8,prompts_per_step=8,draws_per_prompt=4,microbatch_sequences=1,
        sequences_per_rank=32//world,gradient_accumulation=32//world,
        decode_budget=dict(thinking_tokens=2048,answer_tokens=64,max_new_tokens=16384),temperature=.7,top_p=1.,adapter_rank=16,adapter_alpha=32,
        trainable='LM MLP low-rank adapters only; base, vision, heads and towers frozen',
        reference='same immutable export with adapters disabled',learning_rate=1e-5,weight_decay=.01,clip_norm=1.,
        grpo=dict(clip_low=.2,clip_high=.2,kl_beta=.04,temperature=.7,norm='seq'),
        reward=dict(correct=1.,short=.1,route=.1,short_tokens=128,long_tokens=1024),
        grounding=dict(default_binding(),artifact_manifest=None),greedy_replay=None,
        scale_std=False,checkpoint_every=25,
        required_grounding_binding='Pinned A4 reader: G3T camera/lifting, SAM3 candidates_argmax selector, own gravity, own depth for scale. MISSING training artifact manifest and GPU greedy replay receipt.',
        memory_plan=dict(base_bf16_gib=18e9/2**30,adapters_and_optimizer_gib=1.0,frozen_heads_and_towers_gib=14.,
                         activation_and_cache_budget_gib=24.,workspace_budget_gib=8.,assumed_h100_gib=80.,
                         measured=False,reference_extra_model_copies=0),
        notes='No launch authorization. Training loads the export with A4\'s load_native and prompts with its config; bind hashes before use. One process per assigned H100; no GPU keeper or scheduler code.')
    P.write(ROOT/f'configs/h100_{world}.json',cfg)
# Same global batch for an honest 4-versus-8 comparison. Rates are assumptions, not measurements.
steps=200;seq=32;prompt=4800;generated=512;responses=128
rollout=steps*seq*generated
prefill=steps*seq*prompt
replay=steps*seq*(prompt+generated+responses)
# Native cached decode is bandwidth/latency limited; full prefix rescoring is throughput limited.
scenarios={}
for world in (4,8):
    rows=[]
    for label,decode_rate,prefill_rate,replay_rate,head_seconds in (
        ('optimistic',40.,2000.,800.,2.),('planning',25.,1200.,450.,5.),('conservative',12.,600.,200.,10.)):
        gpu_seconds=rollout/decode_rate+prefill/prefill_rate+2*replay/replay_rate+steps*seq*head_seconds
        # Two replays = frozen reference + policy/backward, with replay_rate an effective rate.
        overhead=1.15 if world==4 else 1.25
        gpu_hours=gpu_seconds/3600*overhead
        rows.append(dict(scenario=label,decode_tokens_per_gpu_second=decode_rate,prefill_tokens_per_gpu_second=prefill_rate,
            effective_replay_tokens_per_gpu_second=replay_rate,head_seconds_per_rollout=head_seconds,
            overhead=overhead,gpu_hours=gpu_hours,wall_hours=gpu_hours/world))
    scenarios[str(world)]=rows
P.write(ROOT/'out/GPU_ESTIMATE.json',dict(schema='rl-on-n-estimate-v1',method='token model, no measured H100 step time',
    steps=steps,prompts_per_step=8,draws=4,total_sequences=steps*seq,prompt_tokens=prompt,
    average_sampled_tokens=generated,average_injected_tokens=responses,thinking_token_budget=2048,answer_token_budget=64,
    rollout_tokens=rollout,prefill_tokens=prefill,replay_tokens_each=replay,scenarios=scenarios,
    formula='GPUh = overhead*(rollout/decode_rate + prefill/prefill_rate + 2*replay/replay_rate + sequences*head_seconds)/3600',
    limitations='Rates and token lengths are assumptions; long visual prefixes, context-sized responses, head latency, recomputation and memory pressure can exceed the conservative case. This is not a reservation or measured speedup.'))
