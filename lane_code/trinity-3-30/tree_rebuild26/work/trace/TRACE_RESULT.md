# CUDA queries under CUDA_VISIBLE_DEVICES='' on mode q's admit path (CPU trace, trinity-1-18, 2026-11-21)

Env: /scratch/jjyeung/envs/p1cpu/bin/python (Python 3.12.13; the CPU rehearsals go_rehearsal_k6.sh used it). torch 2.11.0+cpu, transformers 5.12.1; triton and fla are NOT installed.
Workspace: /scratch/jjyeung/orch_n30/tree_rebuild10_w/w26trace (tree tar t_e047002134f979bd.tar extracted to s/; scripts in src/; raw trace.json, slice.log). w26fix was only read, with python -B.
Local copies: src/cudatrace.py, src/slice.py, t1.sh/t1.out (run), t2.out/t3.out (static follow-up).

## Tracer
cudatrace.py imports torch, then wraps torch._C._cuda_getDeviceCount/_cuda_init/_cuda_getDevice/_cuda_setDevice/_cuda_getDeviceProperties and torch.cuda.{is_available, device_count, _lazy_init, init, current_device, set_device, get_device_properties/name/capability, is_bf16_supported, synchronize, mem_get_info, memory_allocated, get_rng_state(_all), _device_count_nvml/_raw_device_count_nvml/_device_count_amdsmi, is_initialized, get_arch_list, current_stream} and cudnn.{is_available, version}. A call made while the variable is '' saves its stack (format_stack, deduplicated); any other call is only counted. The triton driver wrap was skipped because triton is not installed. A 20 ms poller watches /proc/self/maps for libcuda.so/libnvidia-ml and would catch C++-side driver loads, but the +cpu build cannot load libcuda.
Run: CUDA_VISIBLE_DEVICES='' for the whole run (brief rule), nice 10, 8 threads, ulimit -v 16 GB, timeout 600. Exit 0, about 3 s.

## Stages and furthest point
A: a.py's imports (kit b/ z, pl, rb; launch_r1.build/entry; p3_provenance; r1_persisted; s1_admission; production_proof). All ok, no query.
B: _run's lazy imports before admit (r1_coverage, r1_rooms, r1_direction_twins, r1_training, p_opener_witness, r1_handover, r1_population, r1_loader, source_seal, carrier_c1_run). All ok, no query.
C: the real s1_admission.admit(..., prepare_only=True), called inside the same set-''/restore block as production_proof.py:438-447. No fixture config exists: build24k/rehearsal_k6/p and p2 have no c.json, because K6 stopped at twins before p_opener_witness. I passed a '{}' config, so admit ran its prologue (env check, RLIMIT_AS, torch import, set_num_threads/interop, imports of carrier_c1_data, carrier_c1_run, rehearsal (launch_s1.b.q0 resolves), first_batch_progress, s1_exclusions, attempt dir, load, deferred) and stopped at s1_admission.py:163 with "ValueError: Admission requires the four- or eight-rank unflagged mix...". FURTHEST REAL STAGE: admit's config validation, before prepare_phase.
D: an over-approximation: I imported every module named by a function-level import in 16 admit-path modules (98 targets: all of student_pilot's prepare/routing/handover modules, transformers, transformers.video_utils, safetensors.torch, PIL). No query.
E: a probe outside the confirmed path: I imported transformers.models.qwen3_5.modeling_qwen3_5 directly. This raised ONE query.

## Distinct stacks of CUDA queries under the empty mask
1 (stage E, count 1): torch.cuda.is_available
  transformers/models/qwen3_5/modeling_qwen3_5.py:66 `if is_causal_conv1d_available():`
  transformers/utils/import_utils.py:852 is_causal_conv1d_available -> is_torch_cuda_available()
  transformers/utils/import_utils.py:212 is_torch_cuda_available -> torch.cuda.is_available()
  (Under the empty mask, is_flash_linear_attention_available (import_utils.py:847) calls is_torch_cuda_available too, which also queries.)
None through stages A-D: the real admit prologue and every function-level import made no query.
Calls with the variable set: 0 (the brief kept it '' throughout). Final state: cuda not initialized, _cached_device_count None, libcuda not mapped.

## Lead for the GPU run (static, not exercised)
The first import of modeling_qwen3_5 in a process queries CUDA at module level. In the tree it comes from `from transformers import Qwen3_5ForConditionalGeneration` in r1_handover.donor_meta_model (r1_handover.py:193). Its only caller is r1_handover.py:301 (trainable_group_table, inside the function just before donor()). Other imports come from carrier_c1_run.load_model (:804) and carrier_c1.generate (:354). If prepare_phase's bind_target (s1_admission, inside the empty mask) reaches r1_handover.py:301, that import queries under '' unless an earlier, unmasked call already imported the module (for example _run's bind_target at production_proof.py:431). I did not trace whether bind_target reaches :301.

## Not exercised
admit's prepare_phase (mdg_parent.bind/AutoTokenizer.from_pretrained, data.build_stream, s1_routing.build, r1_routing.compose_native, bind_target, run.prepare), frame audit, any DataLoader construction, and the first-batch loader. The tree has no pin_memory use. Not exercised either: _run before admit (host checks refuse on nodename trinity*; a.py requires a /tmp root and SLURM_JOB_ID), fla/triton import-time driver calls (neither package is installed), and C++-level driver queries (CPU build).
