# Source audit

All paths below refer to the supplied build-20 source or the installed CPU environment, not an inferred production checkout.

`T = /scratch/jjyeung/orch_n30/so_step/in/tree/work/tree_r1`

`E = /scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages`

## DeltaNet dispatch in transformers 5.12

`E/transformers/models/qwen3_5/modeling_qwen3_5.py:66–76` imports causal convolution and FLA independently. `:217–219` forms an AND of four callable bindings for the warning. `:420–423` selects each actual implementation independently. The warning at `:425–430` does not route the whole layer through a single fallback.

| Available to transformers in the production process | Full-sequence training convolution | Delta rule at 5k tokens | Gated RMS normalization | Single-token cached decode |
|---|---|---|---|---|
| FLA accepted, causal-conv1d missing | `nn.Conv1d` depthwise convolution, causal slice, then separate `F.silu`, `:488–497` | FLA `chunk_gated_delta_rule`, `:422,535–547` | FLA `FusedRMSNormGated`, `:406–415` | Torch convolution-state update `:222–236`; FLA recurrent delta rule `:423,524–533` |
| FLA and causal-conv1d both missing | Same torch convolution | `torch_chunk_gated_delta_rule`, `:246–324` | `Qwen3_5RMSNormGated`, `:187–202` | Torch convolution update plus `torch_recurrent_gated_delta_rule`, `:327–368` |
| Both accepted | Fused causal convolution | FLA chunk rule | FLA gated RMSNorm | Both fused update paths |

Projection matmuls, sigmoid beta, FP32 decay/softplus, Q/K head replication and output projection remain native torch in all cases (`:460–467,512–521,553–560`). Missing causal-conv1d does **not** disable FLA's chunk rule, its recurrent rule or its norm. `use_cache=False` in the trainer (`T/student_pilot/carrier_c1.py:414`) means the 5k training sequence uses the chunk rule, not the token-by-token recurrent decode loop.

The torch chunk rule normalizes Q/K, transposes/contiguously copies Q/K/V/beta/g to FP32, pads to a multiple of 64, constructs chunk decay and triangular matrices, runs 63 triangular-update iterations, then carries state through `ceil(L/64)` chunks. At L=5000, that is 79 chunks and 56 padded tokens (`:259–320`). Its FP32 state has shape `[batch, value_heads, key_head_dim, value_head_dim]`. The norm fallback casts to FP32, computes mean square and reciprocal square root, multiplies the affine weight, computes SiLU of the gate and multiplies, then restores input dtype (`:193–202`). The recurrent fallback loops over sequence positions, but at the cached-decode callsite the sequence length is one.

Qwen3-Next has the same independent selection: `E/transformers/models/qwen3_next/modeling_qwen3_next.py:344–346,539–556,644–653,690–702`; its reference chunk implementation starts at `:373`. Qwen3.5 is the trainer's actual native class.

“Importable FLA” is weaker than “FLA selected.” `E/transformers/utils/import_utils.py:845–853` requires CUDA availability and FLA version >=0.2.2. `_is_package_available` at `:50–82` consults import metadata, falling back to the module's `__version__`; a namespace shadow or wrong overlay can fail the gate. The gate is cached. `is_torch_cuda_available` at `:208–213` calls `torch.cuda.is_available()`. A CPU-only probe will therefore show torch fallback even if Python can import an FLA package. An ABI/import error in an accepted package can raise during import rather than quietly select torch.

Run the single Python command in `kit_profile/probe.sh` inside the **same production venv, CUDA visibility and overlay** as job 171377. It prints both acceptance gates, every callable's module/name, modeling file and package specs. `launch.py` records actual layer bindings too. For the partial fallback case it must show non-null `fla.*` chunk/recurrent/norm bindings, null causal bindings and `fast_path=False`. For the full fallback case all five imported bindings are null, with actual layer methods named `torch_chunk_gated_delta_rule` and `torch_recurrent_gated_delta_rule`. The supplied overlay log and warning establish neither case alone.

### Expected cost at 5k tokens — estimates, not measurements

Use `C = 2*key_heads*key_dim + value_heads*value_dim`. The installed text-config defaults (`E/transformers/models/qwen3_5/configuration_qwen3_5.py:77–96`) are width 4096, 32 layers, 16 key heads, 32 value heads, 128-dimensional heads. These imply C=8192. They are an arithmetic example; the kit records the actual production config before using them as a model census.

* **Convolution:** with kernel width 4, 5000*C*4 = 164 million multiply-adds per layer. One BF16 `[1,C,5000]` buffer is 81.9 MB. Separate convolution/slice/SiLU adds launches and at least one extra read/write pass. Estimated unfused forward time: 0.2–3 ms/layer; estimated removable overhead relative to a fused path: 0.1–2 ms/layer. At 24 linear layers × 72 rows × roughly two forward visits, this suggests 0.35–6.9 s/step before convolution-backward differences. These are bandwidth/launch-scale estimates, not a measured causal-conv1d speedup.
* **Torch chunk delta:** 63 triangular updates plus 79 recurrent chunks create hundreds to thousands of eager operations and autograd nodes per layer. Each FP32 `[1,32,5000,128]` Q/K/V-sized buffer is 81.9 MB. A `[1,32,79,64,64]` matrix is 41.4 MB; several such intermediates coexist, plus retained backward state. Estimated reference forward: roughly 10–100 ms/layer on H100, versus an estimated 1–8 ms for the fused chunk path; shape, kernel versions and bandwidth can move these ranges substantially. Multiplying even 10 ms by 24×72×2 gives 34.6 s before backward. The high end is incompatible with a 133-s whole step if those dimensions/layer counts apply. That consistency check makes “only convolution missing” plausible, but does not prove it.
* **Gated RMSNorm:** several FP32 elementwise passes over 20.5 million elements in this example, versus fused reads/writes. Estimated 0.1–1 ms/layer additional forward cost, or 0.35–3.5 s/step over forward plus recompute, before backward differences.

All three kernel substitutions can change floating-point reduction/fusion order. They cannot promise bit-identical losses or gradients. A candidate numerical gate is `abs(loss_on-loss_off) <= 1e-4 + 1e-3*abs(loss_off)` and per-tensor gradient relative L2 error <=1e-3, with a separate max-absolute-error report and finite checks. This is a proposed BF16 gate, **not a validated tolerance** for these kernels. The delivered scheduling/cache patches instead require exact equality in CPU tests and zero loss tolerance in the GPU timing kit.

The [official Qwen3.5 documentation](https://huggingface.co/docs/transformers/model_doc/qwen3_5) describes hybrid attention and optional kernel dependencies. The installed version's individual callsites above determine the exact fallback behavior; the generic warning does not.

## Torch 2.11 behaviors used in the analysis and patches

| Behavior | Installed source | Official documentation |
|---|---|---|
| FULL_SHARD gathers before forward and backward; reduces/scatters gradients | `E/torch/distributed/fsdp/api.py:33–41` | [FSDP](https://docs.pytorch.org/docs/2.11/fsdp.html) |
| BACKWARD_PRE trades extra live parameters/gradients for overlap and changes collective issue order | `E/torch/distributed/fsdp/api.py:73–105` | [FSDP prefetch](https://docs.pytorch.org/docs/2.11/fsdp.html#torch.distributed.fsdp.BackwardPrefetch) |
| Forward prefetch follows the first iteration's order and needs a static graph; the all-gather limiter keeps two instances live | `E/torch/distributed/fsdp/fully_sharded_data_parallel.py:345–359` | [FSDP](https://docs.pytorch.org/docs/2.11/fsdp.html) |
| Gradients are converted to reduce dtype before reduce-scatter; its stream waits for compute; accumulation follows reduction | `E/torch/distributed/fsdp/_runtime_utils.py:748–778,831–886` | [MixedPrecision](https://docs.pytorch.org/docs/2.11/fsdp.html#torch.distributed.fsdp.MixedPrecision) |
| The all-gather limiter itself can wait for an event | `E/torch/distributed/fsdp/_runtime_utils.py:297–307` | [FSDP](https://docs.pytorch.org/docs/2.11/fsdp.html) |
| Non-reentrant checkpointing saves RNG by default and stops recomputation when saved tensors are restored | `E/torch/utils/checkpoint.py:349–399,441–474,493` | [Checkpointing](https://docs.pytorch.org/docs/2.11/checkpoint.html) |
| AdamW forwards foreach/fused options; eligible default CUDA Adam uses foreach, not fused | `E/torch/optim/adamw.py:21–48,154–180`; `E/torch/optim/adam.py:934–948`; eligibility in `E/torch/optim/optimizer.py:181–205` | [AdamW](https://docs.pytorch.org/docs/2.11/generated/torch.optim.AdamW.html) |
| Device synchronization waits for kernels on all streams | `E/torch/cuda/__init__.py:1152–1163` | [synchronize](https://docs.pytorch.org/docs/2.11/generated/torch.cuda.synchronize.html) |
| `.to(non_blocking=True)` attempts asynchronous transfers; pinned buffers and stream ownership need care | `E/torch/_tensor_docs.py:5241–5266,4051–4098,6501–6512` | [Tensor.to](https://docs.pytorch.org/docs/2.11/generated/torch.Tensor.to.html) |
| Allocated and reserved differ; memory queries delegate to allocator stats, with no explicit device sync in the Python path | `E/torch/cuda/memory.py:332–337,513–568` | [CUDA memory](https://docs.pytorch.org/docs/2.11/notes/cuda.html#cuda-memory-management) |
| Profiler ranges, export and key averages; CUDA event elapsed time | `E/torch/profiler/profiler.py:285–305,347–366,601`; `E/torch/cuda/streams.py:159–245` | [Profiler](https://docs.pytorch.org/docs/2.11/profiler.html) |
| SDPA implementations can differ numerically; boolean masks select allowed positions | `E/torch/nn/functional.py:5922–6162` | [SDPA](https://docs.pytorch.org/docs/2.11/generated/torch.nn.functional.scaled_dot_product_attention.html) |

Framework behavior is read from the installed 2.11 files. Stable web documentation currently redirects to a newer version, so the report links versioned 2.11 pages.

The continuation rechecked the installed dispatch and FSDP callsites. [evidence/framework_source_audit.txt](evidence/framework_source_audit.txt) retains numbered excerpts and SHA-256 hashes for ten installed files. The versioned FSDP/checkpoint pages and official Qwen3.5 page were reachable on 2026-11-19.

Detached metrics do not retain their autograd history (`E/torch/_tensor.py:806–825`), but they share storage with their inputs; this optimization assumes that the model does not mutate returned scalar storage. The installed equality documentation (`E/torch/_torch_docs.py:4066–4085`) specifies value equality rather than byte identity. The delivered joint comparator therefore checks dtype, shape and contiguous uint8 views, and its local regression rejects a signed-zero mismatch. The thread-setting documentation (`E/torch/_torch_docs.py:9815–9825`) requires setting the intra-op count before eager/autograd work. The runners set it once during process initialization; the prefetch worker does not change it. See [Tensor.detach](https://docs.pytorch.org/docs/2.11/generated/torch.Tensor.detach.html), [torch.equal](https://docs.pytorch.org/docs/2.11/generated/torch.equal.html) and [torch.set_num_threads](https://docs.pytorch.org/docs/2.11/generated/torch.set_num_threads.html).
