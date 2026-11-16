# Student evaluation plan and DSIBench acquisition

**Date:** 2026-09-18  
**Request:** REQ-20260917-232, distillation evaluation lane  
**Decision stage:** `build_spec_ready`  
**Final gate:** `not_entered` — this document specifies the harness; it does not attest that the harness passed launch admission.  
**Execution:** DSIBench downloaded; checkpoint and code inventory completed; CPU checks passed; zero GPU runs, paid API calls, or training.  
**Scientific status:** `untested` — no student benchmark improvement has been measured.  
**Controlling reason:** Evaluate each original checkpoint as soon as its harness passes admission. Its baseline does not depend on teacher collection or adapter training.  
**Attempt budget:** Seed 17; one generation attempt per question per checkpoint per paper cell. Four checkpoints across the three primary cohorts require 32,104 generations: 4 × (500 + 450 + 7,076). This lane consumed zero inference attempts. The fixed-63 diagnostic and optional full-set extensions are separate scopes.

## Material Passport

- Origin: Academic Research Suite experiment planning, with the user's supplied experiment design and primary benchmark sources.
- Material: executable build specification, local inventory, public benchmark acquisition, and CPU validation.
- Verification: downloaded file identities, annotation census, first-frame decoding, checkpoint headers, and existing diagnostic CPU tests were checked. GPU inference and clean-training preprocessing parity remain unverified.
- Source runtime: `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/trainer_repo` (`STUDENT_REPO` below). Do not run the mirror under `agent/student_distillation/`.
- Benchmark root: `/data2/jjyeung/agent_project_data/student_eval_benchmarks_20260918` (`BENCH_ROOT`).
- Lane root: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_student_eval_scoping` (`LANE_ROOT`).
- Source design: `agent/agentic_information_5.0/VSI_DISTILLATION_STUDENT_DESIGN_RESULT.md`, student and evaluation sections only.

## 1. Hypothesis and mechanism

Vision, merger, and language LoRA adapters trained on grounded Gemini 3.1 Pro explanations may improve a student's spatial answers from RGB video alone. Test that claim through each distilled checkpoint's score minus its own pinned base score on identical questions, frames, prompts, decoding, and scoring. A higher score than the other model's base does not measure the effect of distillation.

The treatment is the clean VSI-590K adapter checkpoint. The existing benchmark-trained diagnostic adapter and the answer-only training smoke cannot support this paper claim. Require an adapter receipt that identifies its original base revision, accepted training data, scene split, and preprocessing contract. Freeze training/model-selection choices on internal validation before inspecting final benchmark scores. Report all six model-by-benchmark paired deltas, including negative deltas. A claim that both students improve on all three benchmarks requires all six deltas to be positive; point estimates from one seed do not establish statistical significance.

## 2. Exact implementation and provenance

### 2.1 DSIBench identity, sources, and acquisition

Use **DSI-Bench: A Benchmark for Dynamic Spatial Intelligence**, by Ziang Zhang, Zehan Wang, Guanghao Zhang, Weilong Dai, Yan Xia, Ziang Yan, Minjie Hong, and Zhou Zhao. The primary paper is arXiv:2510.18873, dated 2025-10-21. An OpenReview manuscript identifies an ICLR 2026 submission; acceptance was not verified because the forum/API refused access. Cite it as an arXiv preprint rather than asserting an accepted venue. [Paper](https://arxiv.org/abs/2510.18873), [ICLR submission manuscript](https://openreview.net/pdf?id=NtxX9jyVxd).

The name in the brief omits the hyphen. Search found this matching dynamic video benchmark and no second primary benchmark with the exact DSIBench name. SIBench-VSR and MMSI-Video-Bench are different benchmarks, so neither is substituted. [Project](https://dsibench.github.io/), [official repository](https://github.com/SpatialVision/dsibench), [official HF dataset](https://huggingface.co/datasets/Viglong/DSI-Bench).

The HF card and repository license declare **CC BY 4.0**. Preserve attribution and source provenance; the declaration does not establish ownership of every third-party video. [Dataset license declaration](https://huggingface.co/datasets/Viglong/DSI-Bench/blob/7e3be50cda54f98e8ce11fe89696b5b1ed246801/README.md), [repository license](https://github.com/SpatialVision/dsibench/blob/af90adcd760f2757f8b8dbd869ae9a821f725513/LICENSE).

The local census establishes 1,769 question groups over 943 referenced source clips. Each group has `std`, `reverse`, `hflip`, and `reverse_hflip` versions, for **7,076 evaluation rows**. Each CSV contains `cate`, `relative_path`, `video_type`, `question`, `options`, `GT`, and `others`; `metadata_4aug.csv` adds `aug`. Options form one semicolon-separated string with A–D labels; `GT` is one letter. Six categories cover object motion with static/moving cameras, camera motion with static/dynamic scenes, object-camera distance, and orientation. The four CSVs align by row ordinal, relative video path, and category. Never join by video path alone: several questions share a clip.

All files were downloaded without credentials to `BENCH_ROOT/dsibench/`:

| Artifact | Pinned identity or observed state |
|---|---|
| HF dataset revision | `7e3be50cda54f98e8ce11fe89696b5b1ed246801` |
| Official repository commit | `af90adcd760f2757f8b8dbd869ae9a821f725513` |
| Dataset download | 3,783 files; 2,841,744,284 bytes, approximately 2.84 GB / 2.65 GiB |
| Dataset plus five official code/license files | 3,788 files; 2,841,776,923 bytes |
| Videos physically downloaded | 3,776; 944 per variant. One unreferenced clip per variant stays outside the evaluation membership. |
| `MANIFEST.json` | Per-file URL, revision/commit, bytes, computed SHA-256, and verification status; `COMPLETE` |
| `DATASET_AUDIT.json` | Row counts, group alignment, reference coverage, and download-size recheck |
| `MEDIA_CENSUS.json` | All 3,776 headers and first RGB frames decoded on CPU; zero errors; minimum header frame count 42. This is not a full-video decode audit. |
| `OVERLAP_SCREEN.json` | Source counts and limited identifier comparison against the clean training pool |
| `REMOTE_FILES.json` | Complete, paginated upstream file inventory at the pinned revision |

The exact acquisition command is `python -B LANE_ROOT/acquire_dsibench.py`, with `LANE_ROOT` expanded to the absolute path above. It uses eight public-download threads, verifies sizes and upstream LFS SHA-256 values, preserves partial files, and writes a final manifest. Nothing remains to download. File hashes that bind question/answer files stay in the off-git manifest; their hashes are omitted from this tracked result (`hash=omitted_unsafe`).

The paper names CameraBench, Kinetics-700, SynFMC, LLaVA-178K, and online footage as sources. It uses RGB video for VLM evaluation; tools helped construct the dataset, and 3D expert systems are separate baselines. Students need no depth, poses, point clouds, motion labels, audio, or tools. The paper's 5-fps/2,048-token setting differs from this project's matched 32-frame/16,384-token protocol, so published leaderboard numbers are contextual comparisons. [Construction and evaluation protocol](https://arxiv.org/html/2510.18873v1#S3.SS2).

| Referenced source | Clips | Overlap assessment against ScanNet, ScanNet++, ARKitScenes, ADT, ProcTHOR, and S3DIS |
|---|---:|---|
| CameraBench | 119 | Different named corpus; physical-scene duplication not audited |
| Kinetics-700 (`k700`) | 145 | Different named corpus; web-video duplication remains possible |
| SynFMC | 45 | Synthetic motion corpus; no identified reuse of those six scene datasets |
| LLaVA-178K (`llava178k`) | 138 | Compilation source; original-footage provenance needs a deeper audit for a zero-overlap claim |
| Internet | 496 | Source namespace cannot prove scene disjointness |

SynFMC renders Unreal Engine scenes using HDRI backgrounds and animated assets, including PolyHaven, Objaverse, and Mixamo sources; it is not described as a re-rendering of the six VSI-590K scene corpora. Shared object assets would differ from shared evaluation scenes. [SynFMC construction](https://arxiv.org/html/2501.01425v1#S3.SS3).

The deterministic screen compared DSIBench clip stems with scene names and video stems from the 50,000-row, 1,147-scene clean training input. It found zero exact matches. The different namespaces make this weak evidence: no pixel, building, or renamed-footage audit was performed. Record **no identified source-corpus overlap; physical-scene overlap unknown**, not “contamination-free.” Base-checkpoint pretraining exposure is also unknown. Keep a training-scene audit as a publication check; it need not delay base inference.

### 2.2 Checkpoints and existing runtime

| Student | Exact pin | Local availability and readiness |
|---|---|---|
| OneThinker-8B | `OneThink/OneThinker-8B` at `2b7032f4179d8c032d2eac67b3692263f85be0fc` | Four shards, 17,534,339,512 bytes; headers match the index and file sizes. CPU processor load passed. Supplied two-step training smoke passed. Benchmark inference untested. |
| Qwen3.5-9B | `Qwen/Qwen3.5-9B` at `c202236235762e1c871ad0ccb60c8ee5ba337b9a` | Four shards, 19,306,310,880 bytes; headers match the index and file sizes. CPU processor load passed. GPU generation untested. |

Snapshot paths are `/data2/jjyeung/cache/huggingface/hub/models--OneThink--OneThinker-8B/snapshots/<OneThinker revision>` and `/data2/jjyeung/cache/huggingface/hub/models--Qwen--Qwen3.5-9B/snapshots/<Qwen revision>`. Qwen's pinned architecture is `Qwen3_5ForConditionalGeneration` with a vision encoder and dense hybrid text decoder; it is a vision-language checkpoint. Its pinned upstream repository also lacks `generation_config.json`: derive generation settings from the model config and explicitly freeze the resulting EOS/decoding settings. Do not require a nonexistent file or substitute another checkpoint. [Pinned Qwen config](https://huggingface.co/Qwen/Qwen3.5-9B/blob/c202236235762e1c871ad0ccb60c8ee5ba337b9a/config.json).

`LANE_ROOT/INVENTORY.json` records source/config hashes, shard paths/sizes, and header checks. Full weight-file SHA-256 hashing remains a launch-preparation step. The trainer repository HEAD is `0ecb5427ac2606d222d38ef1149f945644d38e37`; diagnostic modules include uncommitted work, so HEAD alone does not identify the inspected runtime. Freeze hashes of the actual implementation closure before a run.

| Existing code under `STUDENT_REPO` | Reusable behavior and limit |
|---|---|
| `student_pilot/diagnostic.py` | Original/adapter evaluation, greedy config, native EOS/cap detection, raw tokens/text, traces, adapter reload, and offline commands; fixed to OneThinker and the 63-question diagnostic |
| `student_pilot/diagnostic_data.py` | Answer-free holdout preparation, prompt encoding, scorer calls, pair comparison; imports donor/GT admission and has a correctness-dependent cap retry. Do not import that closure into paper inference. |
| `student_pilot/batches.py` | Hash-checked RGB32 loading; processor resampling disabled; original indices/FPS and grid audits; matched training prefix |
| `student_pilot/admission.py` | Video timing validation and pinned scorer loader; donor/label logic belongs outside inference |
| `student_pilot/runner.py`, `adapters.py` | OneThinker loading and LoRA support; model-specific Qwen3.5 dispatch is still needed |
| `tests/test_diagnostic.py` | Seven CPU tests passed, including training/evaluation prompt and pixel-tensor equality on the smoke fixture |
| `scripts/diagnostic_gpu_batch.sh`, `student_pilot/lease.py` | Existing launcher/admission is explicitly fixed to trinity-1-8 GPU1. Do not claim arbitrary-host support by changing an environment variable. |

The private environment uses torch 2.11.0, Transformers 5.12.1, PEFT 0.20.0, and PyAV 15.1.0. It loads both pinned configs/processors on CPU. Both return a Qwen3-VL processor; their model classes differ. No new environment or dependency installation is required by the inventory.

The existing holdout command family is `python -m student_pilot.cli diagnostic {prepare-protocol,prepare-heldout,cpu-check-heldout,evaluate,score,compare}`. `evaluate` takes `--manifest`, `--protocol`, `--output`, `--lease`, `--variant original|adapter`, and optionally `--training-run`. The fixed 63 questions span 18 heldout scenes and remain diagnostic-only. Preparing or evaluating a base must not require accepted teacher targets.

### 2.3 Primary paper cells

Every row below runs for both base and distilled variants of both models. Membership cannot vary by checkpoint, successful parsing, teacher correctness, or media availability.

| Cell/cohort | Question authority | Frames, prompt, decoding, output | Score |
|---|---|---|---|
| `vsibench_answerable500` | Exact 500 qids in `/data2/jjyeung/agent_project_data/answerable500_membership_20260824/MEMBERSHIP_ANSWERABLE_500.json`; membership SHA-256 `2de71c248b9b9817d515510b48dd4d9a5a3800583f5ea64ea2be855b16220fbf`. Questions/options and offline labels from `/data2/jjyeung/agent_project_data/answerable500_gt_canonical_20260902/answerable500_gt_canonical.json`. Join one-to-one by qid and validate dataset/scene/category. | Shared RGB32 and generation contract below; original question plus options | MCA exact match after frozen answer normalization; numerical MRA from pinned scorer; eight-task macro after collapsing direction easy/medium/hard |
| `vstibench_repr450_v2` | `/home/jjyeung/agent_project/agent/vstibench_repr_450_v2.json` and adjacent `.json.provenance`; 450 rows, nine categories, 312 dataset-qualified scenes. Preserve canonical letter/text mapping offline. | Same shared contract; original question plus options | Official five-subtask macro, plus separately labeled raw nine-category macro |
| `dsibench_all4` | Four pinned per-variant CSVs, 1,769 rows each; stable id `dsibench:<variant>:<zero-based-row>`; group id is the original row ordinal. Preserve each variant's own question/options. | Same shared contract; supplied variant video plus original question and verbatim options string | Primary: sample-wise accuracy over 7,076 rows. Required companion: group-wise accuracy over 1,769 groups, correct when at least three of four variants are correct; also six categories and each variant |

VSIBench/VSTIBench media root is `/data2/jjyeung/agent_project_data/vsibench_videos`, as documented in `agent/docs/data/TRINITY_DATA.md`. Resolve exact dataset-qualified media references and preflight every selected video; basename-only lookup can collide. DSIBench media resolve directly to `BENCH_ROOT/dsibench/videos/<variant>/<relative_path>`.

Full-set availability is distinct from permission to create a new cell. Local full VSIBench is `agent/original_vsibench_full.json`, 5,130 questions. The standing rule requires answerable-500 membership for every new VSIBench cell, so this plan does not silently authorize a new 5,130-question run. Existing verified full-set scores may lead headlines where the comparison matches; otherwise obtain a scope ruling before extending VSIBench. Local full VSTIBench is `agent/vstibench_full.json`, 6,042 questions. A full-set extension can lead its headline after its labels/provenance and run scope are fixed; the corrected 450-row provenance does not automatically authenticate the entire 6,042-row file. Neither extension blocks the three primary cohorts. Subset scores must keep their subset names.

### 2.4 Shared input and generation contract

1. **RGB only:** Decode exactly 32 original RGB frames with PyAV. For a video with N frames, select ordinal `floor(k*(N-1)/31)` for k=0..31. This matches the supplied smoke selection. Cache the selection once per video and reuse it across all four checkpoints. A final clean-training receipt must attest the same selector and image-processing policy. The smoke alone does not establish parity with future clean training.
2. **Timing:** Retain original frame ordinals, rational FPS, and actual PTS separately. Feed native processor metadata with the selected ordinals and FPS, with `do_sample_frames=False`. Qwen's processor represents time as ordinal/FPS and averages within temporal patches. Archive that effective representation and its deviation from actual PTS for variable-frame-rate clips; never call approximate timestamps exact. Do not guess 24 FPS. Reject missing timing or fewer than 32 frames at CPU preflight rather than silently duplicate or change membership. Every downloaded DSIBench video has at least 42 header frames.
3. **Pixels:** Preserve aspect ratio and use the existing processor settings verbatim: `size={"shortest_edge":32*128*128,"longest_edge":32*384*384}`. Record actual dimensions, `video_grid_thw`, visual tokens, pixel-tensor hash, and frame hashes. These are processor bounds, not an instruction to force every frame to 384×384. Within each model's base/distilled pair, require identical tensors and tokenized prompts.
4. **Prompt:** Use the current training user-message layout: video followed by text. Text is the original question, followed by a newline and original options when present. VSI/VSTI options are joined with newlines; DSI's supplied options string stays verbatim. Use the pinned native chat template with `add_generation_prompt=True`. Add no system message, teacher evidence, category hint, tools, or special benchmark instructions. Qwen3.5 uses `enable_thinking=True`; its template supplies the opening thinking delimiter. Preserve OneThinker's native template. Freeze these model-specific templates within each pair.
5. **Decoding:** Seed 17, BF16, batch size one, `model.eval()`, `torch.inference_mode()`, `do_sample=False`, one beam, one sequence, `use_cache=True`, SDPA. Temperature/top-p/top-k are disabled (`None`) for greedy generation. Pin native EOS and pad ids and serialize the complete effective generation config. Disable adapter dropout in evaluation. Keep quantization and attention implementation identical within each pair.
6. **Budget:** `max_new_tokens=16384`, inclusive of thinking and answer tokens. Reject inputs beyond 16,384 tokens during CPU preparation; the maximum total is 32,768, subject to each pinned model's context support. Stop on native EOS or the fixed cap. Preserve an answer completed before a cap, but never generate again to improve it. Missing, malformed, and exhausted outputs remain in the denominator. The user's one-attempt rule controls over the diagnostic's 16k→32k correctness-based retry and the generic dispatch ladder.
7. **Answer parsing:** Keep the native raw generation unchanged. In the final visible segment after `</think>` when present, select the last complete case-insensitive `<answer>...</answer>` block. Without a block, accept only a final nonempty line consisting of one option letter or one finite numeric value, optionally preceded by `Answer:` or `Final answer:`. Do not scan reasoning for answer-shaped tokens or use a judge. Reject incomplete tags, ambiguous payloads, nonfinite numbers, and letters outside the supplied option set. Record the parser branch, block count, selected span, and failure reason. Normalize only the extracted payload for scoring. Freeze the grammar in synthetic CPU fixtures before any paper generation.
8. **Attempts and resume:** Record a durable attempt start immediately before generation. Resume only never-started ids. Preserve attempted failures and interrupted starts; never silently issue a second model call. Distinguish complete attempts, incomplete coverage, and successful answers. Sharding partitions one immutable cohort and cannot add attempts or reset the seed contract.

### 2.5 Scoring and answer-bank protocol

Inference must receive an allowlisted, answer-free manifest. It must not import labels, `answer_mapping`, teacher admission, benchmark scorers, or correctness-dependent retry logic. Preparation and scoring run as separate CPU commands. Keep the final runtime package free of GT-bearing files; path/hash manifests for labels belong in the scoring package only.

The compatibility entrypoint `agent/evaluate_benchmark_v4.py` resolves to `agent/agentic_information_5.0/evaluate_benchmark_v4.py` and imports `agent/evaluation/scoring.py`. The CLI uses compatibility fallback behavior; the paper wrapper should instead call the shared scorer with `strict=True` on an explicitly archived scoring projection. The projection's last AI message contains `<ANSWER>{parsed_payload}</ANSWER>`. Invalid/missing answers produce a blank message. Preserve raw native text alongside the projection and label the projection as deterministic parser output, never as the model's raw response. MCA means exact letter agreement after the frozen normalization; numerical questions use the literal pinned `mean_relative_accuracy` implementation, with its 0.50–0.95 confidence-threshold grid. Do not substitute the scorer's separate 20%-error `is_correct` diagnostic for MRA.

For VSIBench, preserve per-question credits, each category mean, and the eight-task macro: average the three relative-direction category means once, then average that value with the seven remaining task means. For VSTIBench, use `evaluation/score_record_core.py`'s `vstibench-official-5subtask-v1`: average `camera_obj_rel_dist_v1/v2/v3`, average `obj_obj_relative_pos_lr/nf/ud`, and then average those two values with camera-object absolute distance, camera displacement, and camera movement direction. The raw nine-category average is supplemental. `score_index_vstibench.py` and its `_score_index_vstibench_mechanical.py` payload expose the existing record builders; `score_req102_vsti_v2_notool.py` is a usage reference, not a generic launch command.

DSIBench's authoritative implementation is the downloaded `official_repo/evaluate.py`. Import it only offline, set its metadata/output roots and model identifier, supply prediction CSVs in original row order with normalized `final_answer`, and call `sample_wise_evaluation()` and `group_wise_evaluation(n=3)`. Compare the wrapper's full-precision results against the official output in synthetic fixtures. The official script takes the first character of its prediction field, so feed only the validated letter or the invalid sentinel `E`; never pass raw reasoning there. Group scoring counts correct variants, not a vote over answer letters. [Official scoring script](https://github.com/SpatialVision/dsibench/blob/af90adcd760f2757f8b8dbd869ae9a821f725513/evaluate.py).

After drain, validate exact membership, one attempt per id, source/runtime/model hashes, generation token counts, EOS/cap status, and parser provenance. Score once offline; a deterministic score replay is allowed because it makes no new model call. Missing rows receive zero credit while coverage remains explicitly incomplete. Archive raw generations, generated token ids, parsed answers, scoring projections, per-question metrics, question membership, frame/protocol/model/scorer bindings, and completion/census receipts.

Every scored cell needs a new immutable bank at `/data2/jjyeung/agent_project_data/ANSWER_BANKS/<bank_id>/`. Register it in `REGISTRY.json` and `SHA256_MANIFEST.txt`; acquire the registry flock first, re-read both authorities inside the lock, write atomically, and assert the before/after entry-count delta. Use the campaign's existing archiver if one exposes that contract; otherwise stage the complete bank and report registration pending. Mirror the required metadata under `agent/evaluation/answer_banks/` in shards no larger than 100 KB. Registration and reviewed score-index admission remain prerequisites to a paper number. This lane does not write shared registries or nominate a score.

Report point estimates and paired deltas in percentage points with two decimal places. Retain full precision internally. Report parse failures, cap failures, media failures, and coverage next to scores; do not reduce denominators. No seed sweep, benchmark-driven prompt changes, adaptive output budgets, or checkpoint selection on these scores.

### 2.6 Memory, time, and run order

The supplied OneThinker smoke measured **19.34 GiB allocated / 20.26 GiB reserved** for two training steps on an RTX A6000. Its 355.22-second start-to-completion interval includes loading, training, checks, and adapter reload. It contains no generation throughput measurement; dividing that duration by two does not estimate inference latency.

For inference, OneThinker's BF16 weights occupy about 16.33 GiB. Its BF16 attention KV cache uses approximately 147,456 bytes/token (36 layers × 2 K/V × 8 KV heads × 128 dimensions × 2 bytes), or 4.50 GiB at 32,768 total tokens. Allow **22–30 GiB** for batch-one inference including vision/prefill workspace and allocator reserve. Qwen stores about 17.98 GiB of weights; eight full-attention layers use approximately 32,768 KV bytes/token, or 1.00 GiB at 32,768 tokens, plus recurrent state/workspaces. Allow **22–32 GiB** as an unmeasured Qwen envelope. Adapter tensors add a small amount. A single 49-GB GPU is a plausible target for either model, not a demonstrated inference fit. Keep full prefill logits disabled.

| Per-checkpoint cell | Questions | GPU envelope | Illustrative GPU-hours at 60–300 seconds/question |
|---|---:|---|---:|
| Fixed holdout, diagnostic only | 63 | OneThinker 22–30 GiB | 1.05–5.25 |
| VSIBench answerable-500 | 500 | OneThinker 22–30; Qwen 22–32 GiB | 8.33–41.67 |
| VSTIBench representative-450 | 450 | Same model-specific envelope | 7.50–37.50 |
| DSIBench all four variants | 7,076 | Same model-specific envelope | 117.93–589.67 |
| Optional VSTIBench full set | 6,042 | Same model-specific envelope | 100.70–503.50 |

These time ranges are capacity-planning scenarios, not smoke-derived measurements. A roughly 2k-token answer at 10–40 decode tokens/second plus preprocessing/prefill motivates the broad range; long generations can exceed it. At the full 16,384-token ceiling, decode alone would take 409.60–1,638.40 seconds under that assumed throughput. The GPU lane must measure prefill time, generated tokens, decode rate, and peak memory on non-paper smoke inputs, then use `T_cell = sum(T_prefill + generated_tokens/rate + I/O)` to publish a better estimate. Neither model has measured inference speed here.

Run order:

1. Devin builds the bounded harness below, runs CPU tests, and freezes answer-free memberships and the common contract. Keep base preparation independent of trace collection.
2. The GPU lane obtains current ownership/coordination admission and runs one small, non-paper generation smoke per base checkpoint. Use synthetic or training-scene questions, never a paper cohort for repeated debugging. This lane launches none.
3. Start the smallest ready base paper cell: OneThinker answerable-500. Qwen base can start independently as soon as its model-specific smoke passes. Continue both bases through VSTIBench-450 and then full DSIBench, scheduling ready cells without waiting for teacher traces.
4. After clean adapter training and provenance checks, run the same three cells for each distilled checkpoint with the already frozen inputs/config. Do not recycle the diagnostic adapter. Freeze scores from all variants and report the six paired deltas.
5. Consider full VSTIBench and any explicitly permitted full VSIBench extension without changing the primary cohorts. Each checkpoint/question remains a single attempt; reuse an existing generation only if the entire input/config identity matches.

Use self-contained launch scripts, data2 output/cache paths, current GPU ownership checks, and the campaign's coordination/vnice policy. The existing diagnostic launcher supports only trinity-1-8 GPU1. A minimal first implementation can retain that placement; additional placement support must validate a real lease and actual host/device identity. The generic API harness does not currently dispatch these local HF checkpoints, so the student runner is the appropriate generation backend. DSIBench's 7,076-row cell also needs the applicable full-cell scope/admission check before launch; this planning lane is not a GPU authorization.

## 3. Revisions

| Revision | Concrete contract | Validation |
|---|---|---|
| v1 | Three primary cohorts; four pinned checkpoint variants; RGB32; greedy 16k; one attempt; explicit offline score/answer-bank contract | Full DSIBench download and census; two local checkpoint header/processor checks; seven existing diagnostic CPU tests |

## 4. Reviewer findings and dispositions

No independent reviewer or formal gate ran. The following are author-verified inspection findings, not reviewer PASS attestations.

| ID | Severity / scope | Evidence | Disposition |
|---|---|---|---|
| E1 | Blocker / scientific validity | Diagnostic flags mark benchmark-trained data and forbid score nomination | Require clean VSI-590K adapter lineage for paper cells; base evaluations remain ready to build |
| E2 | Blocker / engineering | Fixed63 membership, OneThinker loader, and GPU1-only lease are encoded in the existing evaluator | Add isolated benchmark modules and explicit model dispatch; preserve diagnostic files |
| E3 | Blocker / scientific validity | Diagnostic retry eligibility depends on cap status and correctness | Paper runner records one attempt and never imports that retry path |
| E4 | Blocker / scoring | VSTIBench official aggregation collapses two category triples | Use the five-subtask composite and label the nine-category macro separately |
| E5 | Warning / provenance | DSIBench source corpora differ but online footage lacks physical-scene proof | Preserve source/identifier screen and qualify contamination claims |
| E6 | Blocker for distilled comparison / scientific validity | Smoke confirms one fixture's preprocessing; clean-training receipt does not yet exist | Freeze this same selector/processor in training and require its receipt before the distilled cell |
| E7 | Warning / engineering | Qwen has local weights/processors but no upstream generation-config file or measured GPU generation | Derive native config from the model config, pin it, and run a non-paper GPU smoke in the GPU lane |
| E8 | Warning / engineering | DSIBench video rates vary; native Qwen timestamps use ordinal/FPS | Preserve actual PTS and effective timestamps separately; test variable-rate inputs |
| E9 | Scope question / scientific validity | New VSIBench cells require answerable-500; full local file has 5,130 rows | Primary cell remains 500; full-set extension needs an explicit cohort ruling |

## 5. Decision, next steps, and salvage boundary

**Decision:** Ready for one Devin harness lane and independent base-checkpoint GPU admission. Acquisition is complete. The code, GPU fit, and paper score registration still require their own evidence.

The implementation contract is `LANE_ROOT/NEEDS-DEVIN_eval_harness.md`. The GPU lane can use the existing fixed63 evaluator for diagnostic work under its current ownership contract; the three paper benchmarks need the new adapters and isolated inference closure. A failure in Qwen support or one benchmark must not delay a ready OneThinker cell. A data/preprocessing defect discovered before model generation can be repaired and re-pinned without consuming a paper attempt. After generation starts, preserve all attempts and document any contract invalidation; do not silently redefine a paper cell.

Open decisions for the orchestrator are limited to full VSIBench scope, full VSTIBench provenance/admission if that extension is wanted, GPU placement and long DSIBench scheduling, and ensuring the clean trainer adopts the frozen preprocessing contract. No credentials or data-download commands remain outstanding. The stronger physical-scene overlap audit remains a publication limitation.

## 6. Validation and durable paths

- DSIBench: `BENCH_ROOT/dsibench/MANIFEST.json`, `DATASET_AUDIT.json`, `MEDIA_CENSUS.json`, `OVERLAP_SCREEN.json`, and pinned `official_repo/` sources.
- Checkpoints/runtime: `LANE_ROOT/INVENTORY.json`; header/index/size integrity checked for all eight weight shards, without a full weight SHA audit.
- CPU command run from `STUDENT_REPO`: `CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 ../venv/bin/python -B -m unittest discover -s tests -p test_diagnostic.py -v`; seven tests passed. Both processors/configs also loaded locally without model weights or CUDA allocation.
- GPU smoke source: `STUDENT_REPO/artifacts/runs/smoke1/smoke_result.json`; infrastructure evidence only.
- Git: changes remain uncommitted for path-limited landing by the owning lane, as required by dispatch. No frozen package, shared runtime, registry, or diagnostic implementation was edited. No deletions occurred.
