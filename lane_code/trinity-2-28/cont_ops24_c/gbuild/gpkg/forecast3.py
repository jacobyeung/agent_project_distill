"""Reproducible workload counts and explicitly unmeasured planning estimates."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def forecast():
    refs=json.loads((ROOT/'kit2/kit/rerun2/items544.json').read_text())['items']
    repeated=[r for r in refs if r['calls']][:10]
    counts=dict(items=150,primary_items=sum(r['mapping']['dense_count']==64 for r in refs),repeats=len(repeated),prefills=160)
    def calls(r):return sum(c['served'] and c['call'].startswith('<ground ') for c in r['calls'])
    counts['baseline_text_forwards']=sum(32*calls(r) for r in refs)
    counts['dense_main_text_forwards']=sum(r['mapping']['dense_count']*calls(r) for r in refs)
    counts['dense_repeat_text_forwards']=sum(r['mapping']['dense_count']*calls(r) for r in repeated)
    counts['sam_image_encodings']=sum(r['mapping']['dense_count'] for r in refs+repeated if calls(r))
    counts['sam_grounding_forwards']=counts['dense_main_text_forwards']+counts['dense_repeat_text_forwards']
    caps={r['capture']:r['mapping']['dense_count'] for r in refs if calls(r)}
    seen=set();fresh=[]
    # First 30 verify IDs match the unchanged dispatcher. A verify hit recomputes.
    for i,r in enumerate(refs):
        if not calls(r):continue
        if r['capture'] not in seen or i<30:fresh.append(r)
        seen.add(r['capture'])
    fresh+=repeated
    counts['g3t_fresh_with_working_memo']=len(fresh)
    counts['g3t_fresh_if_memo_disabled']=sum(bool(calls(r)) for r in refs+repeated)
    counts['extra_head_frame_pairs_with_working_memo']=sum(32 for r in fresh if r['mapping']['dense_count']==64)
    counts['extra_head_frame_pairs_memo_disabled']=sum(32 for r in refs+repeated if calls(r) and r['mapping']['dense_count']==64)
    exposure=sum(r['mapping']['dense_count'] for r in refs+repeated)/(150*32)
    # The 77-minute observation includes answer decode. Scaling all of it by
    # frame exposure is an envelope, not an identified per-component model.
    baseline_scaled=77*exposure
    rates=dict(prefill_seconds=[6,18],sam_image_seconds=[.05,.15],sam_text_seconds=[.08,.25],
               g3t_original_forward_seconds=[4,12],extra_depth_and_point_frame_seconds=[.02,.10],
               cpu_lift_link_observer_minutes=[20,60],initial_model_load_minutes=[5,15])
    times=[]
    for i in (0,1):
        seconds=counts['prefills']*rates['prefill_seconds'][i]
        seconds+=counts['sam_image_encodings']*rates['sam_image_seconds'][i]
        seconds+=counts['sam_grounding_forwards']*rates['sam_text_seconds'][i]
        seconds+=counts['g3t_fresh_with_working_memo']*rates['g3t_original_forward_seconds'][i]
        seconds+=counts['extra_head_frame_pairs_with_working_memo']*rates['extra_depth_and_point_frame_seconds'][i]
        times.append(seconds/60+rates['cpu_lift_link_observer_minutes'][i]+rates['initial_model_load_minutes'][i])
    tokens=(518//14)**2+5
    retained=4*64*tokens*2048*2
    naive_attention=16*(64*tokens)**2*2
    # Dominant dense linear weights: QKV/projection + two MLP matrices.
    g3t_major=(48*12*1024**2 + 24*12*1024**2 + 8*12*2048**2)*4
    sam_vit=32*(4+2*4.625)*1024**2*4
    memory=dict(units='GiB unless bytes stated',g3t_tokens_per_frame=tokens,
                g3t_four_retained_layers_bytes=retained,g3t_four_retained_layers_GiB=retained/2**30,
                g3t_major_fp32_weights_GiB=g3t_major/2**30,
                g3t_all_weights_planning_GiB=[5.2,6.5],sam_vit_fp32_weights_GiB=sam_vit/2**30,
                sam_all_weights_planning_GiB=[2,4],vlm_9B_bf16_base_weights_GiB=9e9*2/2**30,
                vlm_and_auxiliary_weights_planning_GiB=[18,24],
                prefill_KV_heads_and_private_encoder_workspace_GiB=[6,18],
                g3t_or_sam_peak_workspace_GiB=[4,12],allocator_headroom_GiB=[4,8],
                total_planning_GiB=[39.2,72.5],
                naive_global_attention_single_matrix_GiB=naive_attention/2**30,
                sam_features_on_host=True,sam_images_per_GPU_forward=1,depth_point_frames_per_head_forward=8,
                sam_host_features_conservative_fp32_four_level_GiB=64*2*256*sum(s*s for s in (288,144,72,36))*4/2**30,
                dense_incremental_sampled_grids_bytes_per_capture=64*51*51*5*4,
                expected_to_fit_80GB_H100=True,measured=False,
                qualification='requires fused/memory-efficient attention and unchanged bf16 prefill; 72.5 GiB leaves little margin on a nominal 80 GB device; first actual dense item must confirm')
    return dict(basis='code counts plus unmeasured rates, one H100 including CPU waits',counts=counts,
                baseline_full_read_GPU_minutes=77,frame_exposure_multiplier=exposure,
                baseline_scaled_GPU_minutes=baseline_scaled,
                baseline_scaled_plus_extra_heads_GPU_minutes=[baseline_scaled+counts['extra_head_frame_pairs_with_working_memo']*r/60 for r in rates['extra_depth_and_point_frame_seconds']],
                component_rates=rates,component_GPU_minutes_range=times,
                planning_GPU_minutes=round((sum(times)/2+baseline_scaled)/2),
                allocated_GPU_minutes_max=300,worker_deadline_minutes_from_start=215,staging_reduces_worker_budget=True,
                first_item_files=['metadata/8_64.json','metadata/8_32.json'],
                first_item_model='Estimate each population separately: 104*t64_warm + 46*t32_warm + 10*t_repeat_fresh + initial load. Cold first-item seconds are conservative until memo hits and verification costs are measured. Remaining forecast should use per-item metadata/5.json.',
                capture_cap_bytes=1900000000,mean_compressed_bytes_per_160_records=1900000000/160,
                memory=memory)


if __name__=='__main__':
    value=forecast();(ROOT/'out3/FORECAST.json').write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(value,indent=2))
