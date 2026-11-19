"""Write unbound four/eight-H100 configs and a reproducible token-count estimate."""
from pathlib import Path
from rl_on_n import provenance as P
ROOT=Path(__file__).resolve().parents[1]
N=Path('/scratch/jjyeung/orch_n30/sb_f64/pkg/work/tree_r1')
P.sha(ROOT/'scripts/make_configs.py')
P.sha(ROOT/'in/b09_out/CARD_DRAFT_RL_DRYRUN.md')
P.sha(N/'student_pilot/r1_training.py');P.sha(N/'student_pilot/r1_rooms.py')
P.sha(N.parents[1]/'work/build18/inputs/config.json')
P.sha('/scratch/jjyeung/orch_n30/sb_f64/in/qwen35_9b_meta/config.json')
for world in (4,8):
    cfg=dict(schema='rl-on-n-v1',status='MISSING_PRODUCTION_BINDINGS',tree_root=str(N),world_size=world,
        start_mode='n_export',source_config=None,pool_config=None,artifact=None,pool=None,output=str(ROOT/f'out/production_{world}h100'),
        steps=200,seed=17,cpu_threads=8,prompts_per_step=8,draws_per_prompt=4,microbatch_sequences=1,
        sequences_per_rank=32//world,gradient_accumulation=32//world,
        max_sampled_tokens=1024,temperature=.7,top_p=1.,adapter_rank=16,adapter_alpha=32,
        trainable='LM MLP low-rank adapters only; base, vision, heads and towers frozen',
        reference='same immutable export with adapters disabled',learning_rate=1e-5,weight_decay=.01,clip_norm=1.,
        grpo=dict(clip_low=.2,clip_high=.2,kl_beta=.04,temperature=.7,norm='seq'),
        reward=dict(correct=1.,short=.1,route=.1,short_tokens=128,long_tokens=1024),
        grounding=dict(serving_table=None,evaluator_adapter=None),frozen_tower=dict(weights=None,config=None,dense_frames=32),
        pose_source='tower',scale_std=False,checkpoint_every=25,
        required_grounding_binding='MISSING deployed claimed-arm serving table and evaluator adapter pins; frozen G3T camera/lifting, SAM 3 plus deployed selector, fixed scale/gap math. Own heads are diagnostic only.',
        memory_plan=dict(base_bf16_gib=18e9/2**30,adapters_and_optimizer_gib=1.0,frozen_heads_and_towers_gib=14.,
                         activation_and_cache_budget_gib=24.,workspace_budget_gib=8.,assumed_h100_gib=80.,
                         measured=False,reference_extra_model_copies=0),
        notes='No launch authorization. Preserve the native source/pool configurations; bind hashes before use. One process per assigned H100; no GPU keeper or scheduler code.')
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
    average_sampled_tokens=generated,average_injected_tokens=responses,sampled_token_cap=1024,
    rollout_tokens=rollout,prefill_tokens=prefill,replay_tokens_each=replay,scenarios=scenarios,
    formula='GPUh = overhead*(rollout/decode_rate + prefill/prefill_rate + 2*replay/replay_rate + sequences*head_seconds)/3600',
    limitations='Rates and token lengths are assumptions; long visual prefixes, context-sized responses, head latency, recomputation and memory pressure can exceed the conservative case. This is not a reservation or measured speedup.'))
