# Distilling Gemini spatial evidence into tool-free OneThinker-8B and Qwen3.5-9B

**Date:** 2026-09-18  
**Decision stage:** `design`  
**Final gate:** `not_applicable` — research proposal, not an approved training recipe.  
**Execution:** `not_run`  
**Scientific status:** `untested`  
**Controlling reason:** The user defines success as better final benchmark performance. Intermediate perception prediction and vision-adapter attribution are optional analyses, not gates on collection, training, or the main result.  
**Attempt budget:** proposed minimum: one small distilled run per model and each model's untuned evaluation, with scale decided after profiling; target-format and mechanism controls are optional staged extensions. Actual: zero training, inference, or rewriting calls. No weights downloaded.

The recommended students receive video frames and a question, then generate a detailed, self-contained explanation and answer. Their explanations preserve supported observations, object relationships, measurements, calculations, and consequential corrections from the Gemini 3.1 Pro SPLIT archive. Token cross-entropy trains adapters in the vision blocks, visual mergers, and language model. The students receive no teacher measurements or queryable 3D scene at inference. The primary result is each distilled student's final benchmark gain over its own untuned checkpoint under matched conditions. Geometry reproduction is supervision and optional diagnostic evidence.

## Material Passport

- Material: experiment-design proposal based on primary model, paper, and training-code sources plus the named local training-pool manifest.
- Research question: Does distilling the archived Gemini traces improve final tool-free benchmark answering for OneThinker-8B and Qwen3.5-9B? Optional analysis asks whether better intermediate predictions or vision adaptation help explain that gain.
- Inputs: official VSI-590K training pool; archived correct Gemini traces; pinned OneThinker and Qwen3.5 checkpoint metadata.
- Evidence status: source code and metadata inspected; local training, target conversion, gradient flow, memory, and accuracy untested.
- Scope: student design only. Teacher collection, shared queues, ledgers, and raw archives remain owned by their respective lanes.

## 1. Hypothesis and mechanism

The hypothesis is that grounded intermediate targets provide more useful learning signals than answers alone. A correct answer supervises a short output; a supported explanation also supervises object identity, temporal correspondence, relative position, metric estimates, and the calculation connecting those estimates to the answer. These token losses can backpropagate through the language model and visual mergers into vision adapters. They do not directly impose a metric geometry loss or prove that a particular visual feature improved.

The student must infer these intermediate quantities from its own input. Teacher measurements belong on the assistant target side during training, never in the student prompt. Train-time teacher forcing conditions later explanation tokens on earlier target tokens; evaluation must generate the complete explanation without feeding any teacher evidence. That distinction is central to interpreting success.

### Target format: compare two renderings of the same evidence

Build a small, versioned intermediate record from each accepted archive before rendering either format. Each retained fact links privately to its source message/tool-return field and frame. The record contains observable entities, frame/time references, measurements with units and frames of reference, relations, calculation dependencies, consequential corrections, uncertainty, and the final teacher answer. It is an audit representation for conversion, not a student input or a new runtime tool.

| Format | Assistant target | What the comparison tests |
|---|---|---|
| P: explanatory prose | A coherent account of observations, temporal identity, measurements, calculations, and conclusion, followed by the answer | Whether continuous prose transfers the evidence effectively |
| S: structured evidence plus explanation | A compact plain-text evidence block with named fields, followed by a coherent explanation and answer | Whether explicit entity, time, unit, and reference-frame fields help with the same evidence |

Both formats preserve the same supported facts and final answer. Neither should become a short answer-only summary. Format S must not duplicate all evidence in its prose; otherwise its apparent benefit could come from extra repetitions. Keep the same order of evidence dependencies, numeric precision policy, and answer syntax. Use the model's existing tokenizer; no new coordinate vocabulary is necessary for this first test.

A schema-only illustration, with no solved benchmark content, is:

```text
<think>
Evidence:
entity: <stable semantic description>
observed_in: <input-frame IDs and original timestamps>
measurement: <quantity name>; value: <value>; unit: <unit>
reference: <camera/object/world convention, if known>
support: <visible cue or teacher-derived estimate, stated accurately>
uncertainty: <supported limitation, if any>
Explanation: <connected observations, relationships, calculations, and conclusion>
</think>
<answer><teacher answer></answer>
```

OneThinker uses lowercase `<think>` and `<answer>` delimiters in its published method. Preserve those delimiters for student training and parse the last complete answer block deterministically. A scorer requiring uppercase `<ANSWER>` can receive an explicitly logged adapter output; do not change archived student text or silently make an ambiguous parser accept multiple competing answers. [OneThinker paper, §3.2](https://arxiv.org/html/2512.03043v1#S3.SS2)

### What the converter retains and rejects

Retain the evidence the teacher actually used: relevant frame observations, object identities across views, spatial relations, numbers, units, calculations, ambiguity, and meaningful corrections. Preserve a correction's evidence and resulting conclusion; remove repetitive planning and tool-interface chatter. Do not turn an unsuccessful grounding call into an observation or present a rejected hypothesis as a fact. A teacher's correct final answer does not certify every intermediate claim.

Full archives stay unchanged. A target may omit latency logs, code syntax, paths, tool-call IDs, redundant returns, and unused point arrays. It must retain the substantive observations and calculation operands that make the explanation understandable. If a large array supports a necessary measurement, preserve that measurement and its verified derivation, not an invented verbal claim that it was directly visible.

Conversion must not see benchmark answers or use them to repair reasoning. Training labels may determine acceptance after the teacher finishes, under the collection contract. Baseline-correct rows remain eligible; filtering only teacher wins would change the training population and confound the mechanism. Never rerun or alter archived teacher calls merely to obtain a preferred narrative. If an existing supported trace cannot yield a faithful target, mark the conversion failure rather than filling the gap with agent-written reasoning.

### Numeric serialization and reference frames

- Use ordinary decimal numbers with explicit units and quantity names. A centroid distance, nearest-surface distance, and horizontal distance are different targets. Preserve that distinction.
- Keep source precision in the private record. Render metric estimates with a fixed, generic significant-digit policy, proposed at three significant digits, and never add precision. Preserve integers and answer precision. Compute any derived arithmetic from the same unrounded operands, and mark rendered equalities as approximate when rounding changes them.
- Use consistent units, proposed as meters for lengths, square meters for areas, seconds for time, and degrees for angles. Record and validate every conversion. Retain the original units in provenance.
- Prefer relational quantities that survive arbitrary world-coordinate choices: distances, sizes, temporal order, and explicitly defined object-relative directions. Arbitrary reconstruction axes are a poor prediction target when the student has no way to identify their orientation.
- If coordinates are needed, define a reproducible camera frame, proposed as the first supplied frame with x right, y down, z forward. Transform world points with the archived pose only after verifying the source's camera-to-world versus world-to-camera convention. Do not infer the convention from value signs. Keep camera-frame positions distinct from gravity-aligned positions.
- Define object-relative directions using the question's reference object and viewing/facing direction. Image-left, world-left, and left of an object while facing a third object are not interchangeable. Keep the archived definition; omit unsupported coordinate claims.
- Use semantic entity descriptions and stable local indices assigned by first supported appearance, never arbitrary detector IDs as facts the student must recover. Distinguish a repeated observation of one object from a new instance.
- Preserve qualitative uncertainty when the source supplies it. Do not invent confidence percentages or claim that monocular video makes every metric quantity uniquely observable.

The practical default is prose or typed relations and distances, with camera-frame coordinates only where the archive supports them. A coordinate-free target can still teach metric estimates and spatial reasoning through token cross-entropy.

## 2. Exact implementation and provenance

### Verified OneThinker training and model facts

OneThinker starts from Qwen3-VL-8B-Instruct. Its paper describes Seed1.5-VL annotations, filtered to a 340k-example SFT set, followed by EMA-GRPO on a 600k-example multitask corpus. EMA-GRPO normalizes reward advantages using task-specific moving statistics. The paper reports 32 H800 GPUs, SFT learning rate 1e-5, RL learning rate 2e-6, up to 128 video frames, and 4,096 response tokens. This establishes the published recipe; it does not establish what our distillation run requires. [OneThinker paper, §§3–4](https://arxiv.org/html/2512.03043v1)

**Training scripts are released.** The repository includes `LLaMA-Factory/local_scripts/run_onethinker_sft.sh`, its YAML, `EasyR1/local_scripts/run_onethinker_rl.sh`, EMA-GRPO configuration, and reward code. The HF checkpoint repository itself contains weights, tokenizer/processor files, and model metadata; the linked GitHub repository contains training code. Its README's 8×80 GB guidance concerns the authors' setup, not a demonstrated minimum for our adapters. [Released repository](https://github.com/tulerfeng/OneThinker/tree/4a36ad286d04382fce9816ac4429e650157a5f11)

The released SFT YAML requests full tuning with `freeze_vision_tower: true` and `freeze_multi_modal_projector: true`, one epoch, a 16,384-token cutoff, two video frames/second, and at most 128 frames. The bundled Qwen3-VL freeze registry covers `visual.patch_embed`, `visual.blocks`, and `visual.merger`; it does not include `visual.pos_embed` or `visual.deepstack_merger_list`. Therefore those flags alone do not establish that every visual parameter was frozen. The released RL configuration sets `freeze_vision_tower: false`. These are inspected code settings, not a reconstruction of the authors' actual optimizer logs. [SFT YAML](https://github.com/tulerfeng/OneThinker/blob/4a36ad286d04382fce9816ac4429e650157a5f11/LLaMA-Factory/examples/train_full/onethinker_qwen3_sft.yaml), [freeze registry](https://github.com/tulerfeng/OneThinker/blob/4a36ad286d04382fce9816ac4429e650157a5f11/LLaMA-Factory/src/llamafactory/model/model_utils/visual.py#L355), [RL configuration](https://github.com/tulerfeng/OneThinker/blob/4a36ad286d04382fce9816ac4429e650157a5f11/EasyR1/examples/config_ema_grpo_64.yaml)

Pin the proposed student to HF revision `2b7032f4179d8c032d2eac67b3692263f85be0fc`. HF metadata lists 8,767,123,696 BF16 parameters. The config specifies `Qwen3VLForConditionalGeneration`, 36 text layers at width 4,096, and 27 vision blocks at width 1,152. Its vision patch size is 16, temporal patch size 2, spatial merge size 2, and DeepStack indices are 8, 16, and 24. Use checkpoint-specific values, not library constructor defaults. [Checkpoint config](https://huggingface.co/OneThink/OneThinker-8B/blob/2b7032f4179d8c032d2eac67b3692263f85be0fc/config.json), [HF model metadata](https://huggingface.co/api/models/OneThink/OneThinker-8B)

### Proposed adapters and training objective

Freeze all base weights explicitly, then attach adapters to the following exact module families. Names are from Transformers v4.57.0 before a PEFT wrapper adds its prefix. Enumerate actual `named_modules()` and require exact matches; broad suffixes such as `proj` can accidentally include unrelated modules. [Qwen3-VL implementation](https://github.com/huggingface/transformers/blob/v4.57.0/src/transformers/models/qwen3_vl/modeling_qwen3_vl.py)

| Component | Explicit target families | Proposed rank / alpha | Calculated adapter parameters |
|---|---|---|---:|
| Language model | `model.language_model.layers.{0..35}.self_attn.{q_proj,k_proj,v_proj,o_proj}` and `.mlp.{gate_proj,up_proj,down_proj}` | 16 / 32 | 43,646,976 |
| Vision encoder | `model.visual.blocks.{0..26}.attn.{qkv,proj}` and `.mlp.{linear_fc1,linear_fc2}` | 8 / 16 | 3,849,984 |
| Visual mergers | `model.visual.merger.{linear_fc1,linear_fc2}` and `model.visual.deepstack_merger_list.{0..2}.{linear_fc1,linear_fc2}` | 8 / 16 | 573,440 |

The total is **48,070,400 adapter parameters**, calculated as rank × (input width + output width) for each targeted linear layer. Keep patch embedding, positional embedding, layer norms, token embeddings, output head, and all base linear weights frozen. Adapting all four visual mergers avoids treating Qwen3-VL as if it had only one generic projector. Full merger tuning is a separate, optional intervention and would require a fresh memory estimate.

Start with BF16 base weights, LoRA dropout 0.05, non-reentrant gradient checkpointing, and memory-efficient attention. Proposed starting learning rates are 1e-4 for text adapters and 2e-5 for vision/merger adapters, with a short warmup, cosine decay, and gradient clipping at 1. These are engineering starting points, not source-validated optima. Pin them across comparisons. Use a single seed and one pass through the initial matched subset before proposing a longer run; do not sweep on the final benchmarks.

For an example with input video/question x and supported assistant target y, optimize:

`L = -(1 / |T|) sum_{t in T} log p_theta(y_t | x, y_<t)`

Here T contains the retained explanation, answer, and termination tokens. Mask system/user text, visual placeholder tokens, padding, and non-target chat headers with `-100`. If a target span is unsupported, remove it during conversion; loss masking alone would still feed it as context to later tokens. Use the actual tokenizer/chat template to calculate boundaries and test them on a nonbenchmark fixture. Do not assume a string offset equals a token offset. Normalize by supervised tokens consistently across accumulated minibatches and distributed workers.

Before training, require a tiny forward/backward check that finds finite, nonzero adapter gradients in text, vision, the main merger, and the DeepStack mergers; require frozen weights to have no gradients. Standard LoRA initializes one factor to zero, so both factors need not receive nonzero gradients on the first backward pass. Check a nonzero gradient and weight change per adapter group across two optimizer steps, then restore the initial checkpoint before the actual experiment. These checks prove trainability, not improved perception.

### Frames and input matching

Use the same inference-available frame-selection policy for all student arms. Prefer the archived 32-frame SPLIT selection only if its selector is reproducible in the tool-free student deployment. If selecting those frames itself requires the teacher's geometry stack, use a declared video-only policy such as uniform timestamp sampling and disclose the input difference from the teacher. Feed actual timestamps and original frame indices. Disable processor resampling when supplying selected frames: `do_sample_frames=False`. The pinned processor otherwise samples by default and can assume 24 FPS when metadata is missing. Qwen3-VL constructs text timestamps from frame indices/FPS and averages timestamps within temporal patches. [Video processor](https://github.com/huggingface/transformers/blob/v4.57.0/src/transformers/models/qwen3_vl/video_processing_qwen3_vl.py), [multimodal processor](https://github.com/huggingface/transformers/blob/v4.57.0/src/transformers/models/qwen3_vl/processing_qwen3_vl.py)

Preserve aspect ratio and processor patch alignment. Begin profiling with 32 frames at approximately 384×384 pixel area, with a 16,384-token total context. At exactly 384×384, the config implies 9,216 pre-merger visual patch tokens and 2,304 language-side visual tokens, before timestamp and boundary tokens. At 448×448 these become 12,544 and 3,136. These are arithmetic examples, not a mandate to distort every frame into a square. Record actual `video_grid_thw` and token counts after preprocessing.

A teacher may inspect additional frames or crops during tools. Record whether each supervised observation has support in the student's supplied views. If the source video contains the evidence but the fixed input misses it, either apply a predeclared inference-time frame policy shared by every arm or flag that row's evidence-coverage limitation. Do not select student frames from teacher successes or answer labels while claiming a fixed tool-free input. Nonuniform selected frames need original timestamps; treating them as a new uniformly sampled video corrupts temporal targets.

Keep the full supported explanation where it fits. Measure target-length quantiles before fixing the production context. Do not silently truncate the final answer or discard long rows from only one arm. If a row exceeds the selected cap, use a shared documented overflow policy and report its count; a lossless target may require a longer context or a separately identified exclusion. A teacher's 16k/32k generation allowance does not guarantee that every full trace fits a 16k student input-plus-target window.

### Training pool, acceptance, and held-out data

The inspected pool manifest is `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/membership/v2/TRAIN50K_SCENE_REUSE_MANIFEST.json`. The answer-free input is `train50k_scene_reuse_answer_free.jsonl` in the same directory. Its official source is `nyu-visionx/VSI-590K`, revision `346fbd4e41dec974bf24894d0541a49327ee6669`; no substituted mirror is needed. [Official dataset](https://huggingface.co/datasets/nyu-visionx/VSI-590K/tree/346fbd4e41dec974bf24894d0541a49327ee6669)

The manifest selects 50,000 rows across 1,147 normalized video/scene identifiers and seven source task classes: count, absolute distance, object size, room size, appearance order, relative direction, and relative distance. The manifest reports zero normalized scene-ID overlap against the named full VSIBench, VSTIBench, and ReVSI evaluation inputs. This is a manifest-level finding, not an independent pixel-duplicate audit. Building-level overlap, renamed duplicate footage, and the base model's pretraining contamination remain unknown.

The collection objective is 20,000 correct archived perceptual traces, not an established available count or a guaranteed yield. Correctness acceptance must retain the collection contract's numeric threshold and scorer identity. A fractional numeric score should not silently become “correct.” Keep acceptance/scoring metadata separate from runtime prompts and target-conversion input.

Split the 1,147 scene groups before inspecting teacher success rates or choosing student hyperparameters. Proposed allocation: 90% train, 5% validation, 5% internal test, grouped by normalized scene and stratified by source corpus when feasible. Keep every question, crop, rerun, and paraphrase from a scene in one partition. Extend grouping to known building/session identifiers when available. The exact row counts follow from grouping and must be recorded; they are not guaranteed to equal a 90/5/5 question split.

An archive containing 20k accepted traces across all partitions yields fewer than 20k optimizer examples. If 20k *training* traces are required, the collection target must additionally cover held-out scenes. Holdout answering must include all eligible held-out questions, not only teacher-correct examples; otherwise evaluation measures performance on teacher-selected easy cases. Final benchmark inputs and answers never enter target preparation or model selection. Keep all derived data versioned beside the immutable archives, with sanitized path-only references in Git for answer-bearing artifacts.

### Primary comparison and optional analyses

The smallest useful pilot trains each student on the same detailed target, proposed as P unless the optional P/S test identifies a preferred rendering. Evaluate each against its own untuned checkpoint. Use a common subset drawn by scene before conversion, proposed at 2,000–5,000 accepted training traces as availability allows, plus the complete predeclared internal validation questions. Do not change membership per model or arm. If few accepted scenes are available, report the limitation rather than substituting a question-level split. Collection toward 20k traces can continue independently.

| Primary pair | Untuned checkpoint | Distilled checkpoint | Primary quantity |
|---|---|---|---|
| OneThinker | Pinned OneThinker-8B | Same checkpoint + vision/text/merger adapters | Final benchmark score difference |
| Qwen3.5 | Pinned Qwen3.5-9B | Same checkpoint + vision/text/merger adapters | Final benchmark score difference |

The optional OneThinker comparisons below can explain the result; they do not gate either primary pair.

| Arm | Target | Trainable components | Isolated comparison |
|---|---|---|---|
| U | No training | None | Untuned OneThinker baseline |
| P | Detailed prose evidence and answer | Text + vision + all mergers | Primary student |
| S | Typed evidence plus explanation and answer | Text + vision + all mergers | S versus P: rendering with the same evidence |
| F | Same target as P | Text + all mergers; vision blocks frozen | P versus F: contribution of vision-block adaptation |
| A | Answer only | Text + vision + all mergers | P versus A: contribution of intermediate supervision |

Stage these runs rather than committing to a full factorial matrix. If a format comparison is useful, compare P and S on OneThinker only, then use the selected target for both primary models. F and A are optional subsequent analyses. If S is chosen, both controls must use S's examples and corresponding supervision. A separate structured-only arm is optional; the present S arm deliberately keeps the user's detailed explanation. F is a text-plus-merger control, not literally LLM-only; a strict LLM-only control would additionally freeze every merger and would confound the contribution of vision blocks with merger adaptation.

Pin checkpoint, seed, examples, frame tensors, optimizer steps, effective global batch, text/merger learning rates, sequence buckets, and evaluation decoding. Freeze only vision-block adapters for F; leave merger treatment identical. Give P and S the same facts and limit their length imbalance by construction, without truncating substantive content. Report supervised tokens and actual GPU time for every arm.

Equal examples and steps do not equalize supervised-token count between answer-only and explanation training. That difference is part of the intervention. Use the same context and padded token-slot budget to control allocated compute, and disclose measured compute differences, especially for F. Do not claim that identical epochs alone produce a FLOP-matched comparison, or give answer-only extra repeated data until it reaches the prose token count. A later fixed-FLOP comparison would answer a separate efficiency question.

Use paired answer quality on all internal held-out questions for pilot selection, with per-task scores, scene-cluster bootstrap uncertainty, answer-parse failures, and output-cap failures. Evaluate every arm with the same full-generation budget and the campaign's recorded budget-extension policy. The primary success criterion is a credible positive final benchmark delta over that student's untuned checkpoint under the preregistered evaluation contract. Report effect size and uncertainty; an indistinguishable delta is inconclusive, not a success. A higher absolute score than the other student does not establish that distillation helped.

Inspect teacher-evidence agreement on held-out traces only as an optional fidelity diagnostic, not independent geometric ground truth. P beating A supports intermediate supervision; P beating F supports the contribution of vision adaptation under this setup. Neither contrast alone establishes a broad perception improvement. A dedicated held-out localization or correspondence check with independently available annotations could strengthen that analysis, but is not required to establish the main benchmark result.

Select the representation on internal validation once, then confirm on the untouched internal test. Evaluate the chosen student once on the final benchmark contract; do not use benchmark-derived constants or tune on its mistakes. Report all pilot arms to distinguish a formatting improvement from evidence transfer and vision adaptation.

### Memory and feasibility: estimates, not measurements

The checkpoint's BF16 base weights require approximately **16.33 GiB** (8,767,123,696 × 2 bytes). The proposed 48.07M adapters need approximately **0.72 GiB** for FP32 weights, FP32 gradients, and two FP32 Adam moments, before optimizer workspaces. This arithmetic excludes activations, logits, attention workspace, allocator overhead, and distributed buffers.

For microbatch one, 32 moderately sized frames, 8k–16k total tokens, memory-efficient attention, and checkpointing in both towers, **30–45 GiB per GPU is a planning estimate**, not a fit claim. Dense FP32 logits alone cost about 4.64 GiB at 8,192 tokens or 9.27 GiB at 16,384 tokens with this vocabulary, so a verified chunked/fused cross-entropy path matters. Vision adapters require backward activations even though most weights are frozen; precomputed visual features cannot replace that path.

A 49 GB device may fit the smaller setting but has little margin for the longest targets. Profile one real-shape backward step before selecting capacity. Prefer two to four campaign-authorized 49 GB GPUs with an explicitly supported sharding setup if memory requires it; ordinary DDP replicates the base weights and does not solve single-example memory pressure. Sharding, checkpointing, and loss kernels must preserve the same training objective. Four-bit base quantization is a fallback requiring a separately recorded configuration; do not mix quantization across the causal comparisons. Training time is unknown until measured steps/second and the accepted target-length distribution are available.

### Qwen3.5-9B: second student with the same targets

Pin `Qwen/Qwen3.5-9B` to revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`. The exact checkpoint uses `Qwen3_5ForConditionalGeneration`: a dense language model with 32 layers at width 4,096, comprising 24 Gated DeltaNet layers and eight full-attention layers. Every fourth layer uses full attention. The vision encoder has 27 blocks at width 1,152 and one visual merger; `deepstack_visual_indexes` is empty. The model card's family-level MoE description must not be applied to this dense 9B checkpoint. [Pinned config](https://huggingface.co/Qwen/Qwen3.5-9B/blob/c202236235762e1c871ad0ccb60c8ee5ba337b9a/config.json)

The checkpoint is post-trained from Qwen3.5-9B-Base and enables thinking by default. Its HF repository releases checkpoint/configuration assets, not an exact reproducible pretraining/post-training run. The inspected Qwen repository tree did not contain a corresponding training package. The framework authors do release an ms-swift Qwen3.5 instruction-finetuning recipe, including dense-model LoRA; its demonstrated dense example is 4B with short inputs, not a validated 9B video/vision-LoRA configuration. [Model card](https://huggingface.co/Qwen/Qwen3.5-9B), [ms-swift training documentation](https://swift.readthedocs.io/en/v4.0/BestPractices/Qwen3_5-Best-Practice.html)

Qwen3.5 cannot use OneThinker's old Transformers v4.57.0 backend merely because its saved config contains a similar version string. The inspected Transformers v5.2.0 implementation provides the following explicit adapter targets; inspect actual loaded modules before matching them. [Versioned Qwen3.5 model code](https://github.com/huggingface/transformers/blob/v5.2.0/src/transformers/models/qwen3_5/modeling_qwen3_5.py)

| Component | Explicit target families | Proposed rank / alpha | Calculated adapter parameters |
|---|---|---|---:|
| All 32 text MLPs | `model.language_model.layers.{0..31}.mlp.{gate_proj,up_proj,down_proj}` | 16 / 32 | 25,165,824 |
| Eight full-attention blocks | `model.language_model.layers.{3,7,11,15,19,23,27,31}.self_attn.{q_proj,k_proj,v_proj,o_proj}` | 16 / 32 | 3,932,160 |
| Other 24 text blocks | `model.language_model.layers.<linear_layer>.linear_attn.{in_proj_qkv,in_proj_z,in_proj_b,in_proj_a,out_proj}` | 16 / 32 | 14,180,352 |
| Vision blocks | `model.visual.blocks.{0..26}.attn.{qkv,proj}` and `.mlp.{linear_fc1,linear_fc2}` | 8 / 16 | 3,849,984 |
| One visual merger | `model.visual.merger.{linear_fc1,linear_fc2}` | 8 / 16 | 143,360 |

This proposal totals **47,271,680 adapter parameters**. A `q_proj,v_proj` allowlist alone would omit the attention paths in 24 of the 32 text layers. Full-attention `q_proj` outputs 8,192 channels because it includes a gate; account for that when checking adapter counts. The DeltaNet linear projections are ordinary `nn.Linear` modules and can receive LoRA. Keep its depthwise convolution, `A_log`, `dt_bias`, gated normalization, base weights, patch/position embeddings, and vocabulary embeddings/head frozen. No DeepStack adapters should appear in this model.

Use ordinary next-token CE; no RL, teacher-logit loss, or MTP objective is necessary. The weight index contains 15 `mtp.*` tensors, but the inspected standard conditional-generation constructor defines the main model and language head without an MTP module. Record loader missing/unexpected-key reports and account explicitly for unused MTP tensors; do not globally suppress arbitrary load mismatches. [Pinned checkpoint index](https://huggingface.co/Qwen/Qwen3.5-9B/blob/c202236235762e1c871ad0ccb60c8ee5ba337b9a/model.safetensors.index.json)

The framework recipe identifies GatedDeltaNet training constraints: the documented Transformers path does not support packing/padding-free training, and it recommends flash-linear-attention and causal-conv1d kernels. Begin with unpacked examples, microbatch one, `use_cache=False`, and tested length buckets. Do not use an inference-only kernel as evidence of backward support. The documented environment notes include video-version incompatibilities, so a developer must pin and test one coherent dependency stack rather than combine the newest versions opportunistically. [ms-swift Qwen3.5 recipe](https://swift.readthedocs.io/en/v4.0/BestPractices/Qwen3_5-Best-Practice.html)

Both checkpoints name `Qwen3VLProcessor` and `Qwen3VLVideoProcessor`, with the same 16×16 spatial patches, temporal grouping of two, spatial merge of two, and normalization values. Qwen3.5 has different vocabulary/special-token IDs and a different chat template, and its image size defaults differ. Use each model's native processor/template, then explicitly bind the same source frames, timestamps, aspect-preserving resolution budget, and realized `video_grid_thw`. Audit whether its template already inserts `<think>` so that targets do not duplicate the prefix. Match thinking mode between each model's untuned and distilled evaluations. [Qwen3.5 image processor config](https://huggingface.co/Qwen/Qwen3.5-9B/blob/c202236235762e1c871ad0ccb60c8ee5ba337b9a/preprocessor_config.json), [video processor config](https://huggingface.co/Qwen/Qwen3.5-9B/blob/c202236235762e1c871ad0ccb60c8ee5ba337b9a/video_preprocessor_config.json)

Keep accepted questions, scene partitions, semantic targets, frame evidence, example exposures, and effective update counts equal across students. Their tokenizers differ, so identical text does not guarantee equal token counts. Report each model's supervised/input token totals, realized frames/resolution, trainable parameters, and GPU time; use the same feasible context/visual-token budget and a shared overflow membership policy. Do not truncate one student's explanations to pretend exact token parity or describe this as a pure architecture ablation. The main comparison is the distillation delta within each model, followed by the absolute scores and efficiency across models.

HF metadata reports 9,653,104,368 stored parameters, mostly BF16 with 3,840 FP32 values, approximately **17.98 GiB** of stored weights including MTP extras. Proposed FP32 adapter weights/gradients/Adam moments add about **0.70 GiB**. The 248,320-token vocabulary requires about **7.58 GiB / 15.16 GiB** for dense FP32 logits at 8k / 16k tokens, respectively. These calculations expose why fewer quadratic-attention layers do not guarantee lower training memory. An initial **32–48+ GiB** per-device planning envelope at microbatch one and 32 moderate-resolution frames is an unmeasured estimate; profile the actual delta-rule backward and loss kernel before claiming a 49 GB fit. Use sharding if required. [HF metadata](https://huggingface.co/api/models/Qwen/Qwen3.5-9B)

### Bounded development handoff

For OneThinker, the released LLaMA-Factory backend provides a concrete reference. For Qwen3.5, use a tested supported backend such as the documented ms-swift Transformers path; a single newer backend for both models is reasonable if it passes both model-specific fixtures. The scripts' existence does not make their current configuration appropriate. The developer needs one shared derived-data export, explicit model-specific training configurations with a small adapter-selection extension if necessary, and a generation/evaluation wrapper. A new training framework or orchestration service is unnecessary. The assigned development lane, not this research lane, owns implementation after teacher data begins landing.

The exporter should emit a scene-grouped membership record, video/frame references with original timestamps, the question/options, one assistant target, and private source-span provenance. It should expose neither acceptance labels nor tool-return evidence in the user input. Keep the P/S records paired by immutable source ID. Use the backend's existing conversation loader only after verifying that it preserves preselected video frames and metadata; its default FPS/max-frame settings can resample the inputs. A thin collator override is warranted if this cannot be expressed in the existing loader.

The training integration should freeze the entire base before PEFT injection, enumerate the exact adapter paths above, and log the trainable parameter names/counts by component. Set merger rank explicitly, including all three DeepStack mergers. Keep base embeddings and output head frozen. The author's `freeze_*` flags and broad `lora_target` matching are not an adequate trainability specification. Different text/vision ranks and learning rates may require explicit PEFT rank patterns and optimizer parameter groups; use a uniform, disclosed rate instead if a bounded first implementation cannot support separate groups reliably. Do not claim to have implemented groups that the trainer silently ignores.

Before the pilot, require frame-ID/timestamp preservation, assistant-only label masking, complete answer retention, frozen-base checks, and the two-step adapter-gradient/update fixture described above. Save only the adapter checkpoint plus pinned base-model/processor identity, module map, and training config. Verify reload by matching deterministic generation on a nonbenchmark fixture. The inference wrapper supplies only frames/question/options and no tools, then emits the archived response and parsed answer. These are development requirements; no exporter or runner was created in this research lane.

## 3. Revisions

| revision | change | reason | outcome |
|---|---|---|---|
| v1 | Source-grounded student proposal with explicit evidence renderings, adapter families, and comparisons | Make the proposed perception-transfer claim testable | Research complete; implementation not run |

## 4. Reviewer findings

No external review of the student-design proposal or formal training gate ran. The following are author-identified design constraints, not relayed reviewer verdicts.

| id | round | reviewer | severity | category | verified status | exact safe evidence | fix / disposition |
|---|---:|---|---|---|---|---|---|
| D-1 | 0 | author inspection | Warning | engineering | verified | Released SFT YAML and Qwen3-VL freeze registry linked above | Explicit adapter allowlist and per-group gradient checks; do not copy freeze flags blindly |
| D-2 | 0 | author analysis | Warning | scientific-validity | partial | Teacher tool coordinates and student inputs may use different information/reference frames; archive-wide coverage not audited | Preserve known frame conventions; prefer invariant relations; measure evidence coverage |
| D-3 | 0 | author inspection | Warning | integrity | partial | Named local manifest reports normalized-ID exclusion only | Scene-grouped partitions; report building/visual-duplicate and pretraining-overlap uncertainty |
| D-4 | 0 | author analysis | Warning | scientific-validity | verified | Answer-only and prose targets have different supervision lengths by definition | Match examples/steps/token-slot budget and report actual token/compute totals |
| D-5 | 0 | author analysis | Warning | engineering | unknown | No backward memory profile or conversion-length census exists in this lane | Profile before selecting devices, sequence limit, or training schedule |

## 5. Final decision and controlling reason

`not_applicable`: this document recommends a bounded comparison; it does not approve a launch, register a kept fix, or claim a result. Prioritize teacher collection and the smallest untuned-versus-distilled pair for each student, using the same detailed supported targets and explicit vision/text/merger adapters. Final benchmark improvement is the primary criterion. Format comparisons, answer-only/frozen-vision controls, and intermediate prediction analyses remain optional. The scientific hypothesis remains untested.

## 6. What would change the decision

A source-faithful target sample, measured target lengths, successful gradient and memory checks, and a pinned scene split would make a training package reviewable. Final benchmark gains over each untuned checkpoint establish the requested outcome. Gains over optional A and F controls could help explain that outcome but are not prerequisites. Unsupported intermediate facts, systematic unseen-frame targets, or arbitrary coordinate targets would require conversion changes before treating a negative result as a test of faithful distillation.

## 7. Salvage and non-revival boundary

Reuse immutable teacher archives, source-linked evidence records, pinned model metadata, and the same scene partitions across target renderings. Preserve failed conversions as recorded outcomes. Do not repair teacher answers with held-out labels, edit raw traces, claim that correct answers validate explanations, or present trainability checks as perception gains. No student checkpoint or new training infrastructure was created in this lane.

## 8. Audit receipts

Only public source bytes were hashed. Hashes below identify inspected public configuration/code, not model weights or answer-bearing training artifacts.

| artifact / sanitized path | availability | hash or omission reason | role |
|---|---|---|---|
| HF `OneThink/OneThinker-8B`, revision `2b7032f4179d8c032d2eac67b3692263f85be0fc`, `config.json` | inspected | `sha256:file_bytes:cc76a13b9e08a9548e177717d4e0b929142edcaf674d26dff5b2c586a8e28a35` | Architecture |
| OneThinker Git revision `4a36ad286d04382fce9816ac4429e650157a5f11`, SFT YAML linked above | inspected | `sha256:file_bytes:9696e611f95c50ef8d3f89bf52ecd350a56e577e517b70bd0a95bceb4dd1a409` | Released recipe |
| Same Git revision, `LLaMA-Factory/src/llamafactory/model/model_utils/visual.py` | inspected | `sha256:file_bytes:31376c6f50e562d0ddd987ae5dbe9e0abd1f704e7d5e95c308e4cfd13aaf97f3` | Freeze semantics |
| Transformers v4.57.0, `src/transformers/models/qwen3_vl/modeling_qwen3_vl.py` | inspected | `sha256:file_bytes:dd63ed3b124232735b3dca1bfa28f9d6b0d3f7182afcb75dde8f3e724b2b22da` | Module names and dimensions |
| HF `Qwen/Qwen3.5-9B`, revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`, `config.json` | inspected | `sha256:file_bytes:d0883072e01861ed0b2d47be3c16c36a8e81c224c7ffaa310c6558fb3f932b05` | Second-student architecture |
| Transformers v5.2.0, `src/transformers/models/qwen3_5/modeling_qwen3_5.py` | inspected | `sha256:file_bytes:d1ae3856f53763591ec65054129af46e003a1715efcf7eef2b752a31e85526b8` | Hybrid attention and adapter targets |
| Named `TRAIN50K_SCENE_REUSE_MANIFEST.json` | metadata inspected | `hash=omitted_unsafe` | Training-pool provenance and reported exclusions |
| Derived student targets, model adapters, launch receipt | `not_created` | Not applicable | Future implementation |

## 9. Validation and canonical routing

- Subject implementation/config commits: none; no code or experiment changes.
- Validation: primary model config, repository tree, SFT/RL scripts/configs, freeze registry, Transformers model/processors, and selected local manifest fields inspected. Adapter counts and visual-token arithmetic calculated from the pinned config. No weights, inference, training, or model allocation used.
- `campaign.py doctor`: read-only orientation returned rc=1 for existing campaign cohort/coord findings; this document-only lane did not modify coordination state or infer launch permission from it.
- Coordination work ID and terminal result: not applicable to this bounded document-only dispatch; parent owns campaign status.
- `CLOSED_LOOP_LEDGER.md` / `CAMPAIGN_LEDGER.md`: not modified, per dispatch scope; no experimental verdict to nominate.
- Canonical result path: `agent/agentic_information_5.0/VSI_DISTILLATION_STUDENT_DESIGN_RESULT.md`.
- Parent lands the pathspec-limited commit. No frozen experiment files, shared queues, or teacher packages were edited.

## 10. Clean r1313 adapter: review-fix checkpoint

The repaired clean-source adapter passed its available offline tests, but it still cannot authorize real teacher conversion. The live host must supply complete source authorities and RGB/video evidence, execute the diagnostic integrations, and reconcile the shared converter interface. No real training target or benchmark result is approved by this checkpoint.

The supplied review is `agent/scratch/devin_lanes/r1313_clean_source_adapter_v2_20260918/review/independent_review_verdict.md`, with verdict `PASS_WITH_REQUIRED_FIXES`. Its five findings have the following dispositions; no new independent review was dispatched.

| Finding | Supplied severity | Disposition | Evidence and remaining gate |
|---|---|---|---|
| 1 | required | Fixed in code: copied text and recursive metadata reject label/scoring aliases with the evidence ID and character offset | `ResponseTests` covers all requested aliases, source channels, mixed separators, escaped fields, positive controls, and actual preparation refusals |
| 2 | required | Fixed in code: snapshots preserve attempt inventories and frozen historical top-up/config bytes; each selected qid records its attempt and reason | `TopupAuthorityTests` checks accepted 32k attempts, exact initial bindings, missing/invalid authority, changed inputs/configs, drift, and rejected/partial inventory; real-source admission remains pending |
| 3 | blocking | Real media not fixed; the requested `snapshot --strict` inventory is implemented | The strict CLI returns 2 and lists 35 missing media items in the lane-staged metadata fixture, including physical scene `scannetppv2__104acbf7d2` versus frame directory `scannetppv2__15b109bd584d`; this synthetic attempt supplies no real-pixel proof |
| 4 | required | Runner fixed; live integration execution remains blocked | Dependency checks replace unconditional skips and report executed/skipped test IDs; all 15 live diagnostic integrations still require their real dependencies |
| 5 | advisory | Deferred to the shared converter integration | Preserve the validated-candidate interface; reconcile the sibling redesign and regenerate snapshots, jobs, runtime pins, and review templates before production |

Implementation branch: `clean-r1313-adapter-20260918` in the lane's `work/trainer_repo`.
- `93f28ea2499bbae6d15eda74d989f79e9a4076ec` repairs Findings 1 and 2 and implements the strict inventory for Finding 3.
- `4a2d4f4f7c8620f4a1b873413a08d13ce5a0b4e1` repairs the runner for Finding 4.
- The original adapter commit `b056a2a4e8bbc8160fa709e25bb6dbe3c144e042` remains unchanged. The complete patch series begins at `0ecb5427ac2606d222d38ef1149f945644d38e37`.

Verification selected 156 test methods: 139 passed, 17 were conditionally skipped, and none failed or errored. All 123 original methods remain registered, and 33 repair methods are added. The final source-byte guard passed. The skips comprise the 15 diagnostic integrations and two real collector-copy tests; the sibling staging directory was not read under this lane's retained scope. The original media validator and all ten inherited dependency hashes remain unchanged.

Evidence root: `agent/scratch/devin_lanes/r1313_clean_source_adapter_v2_20260918/out_fixes/`. `TEST_RESULTS.json` names every skipped dependency; `tests.log` preserves all verification runs; `VERIFICATION.json` binds the actual strict CLI refusal; `strict_staged_inventory.json` contains its inventory. `SOURCE_PINS.json`, `patches/`, `PATCH_VERIFICATION.json`, and `REVIEW_PACKET.md` provide the commit/file hashes, ordered patch replay, and live-host landing checks. Unavailable parent authorities are reported explicitly rather than treated as proof that all child references have been discovered.

No SSH, paid API call, GPU run, file deletion, push, or shared diagnostic implementation change occurred. Parent integration must land this result-file update separately from the isolated adapter commits. The controlling limit remains real-source readiness: a passing offline fixture does not certify a teacher trace, real camera decoding, or a converted explanation.
