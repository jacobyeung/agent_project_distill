# NO-GO

The nested-frame design works on CPU fixtures, but this kit does not establish a safe training or reading launch.
Paths below are relative to `sb_f64/out/kit` unless stated otherwise. Review evidence is in this directory.

1. **BLOCKER — store conversion changes admission.** `scripts/nest_store.py:apply` catches missing-frame errors, omits those rows, and renumbers survivors. The independent missing-pins case drops all four source rows. Keeping them in a report denominator does not preserve the training population.
   `frame_input.nest_row` also sorts anchors: an adversarial reversal of the synthetic fixture changes anchor 1 from native frame 367 to 0 while retaining its pose record. This demonstrates a missing precondition, not a known reversed row in the absent population.
   Fix: preflight every source row; refuse publication when any pin or frame is MISSING; preserve source indices, targets, row count, and anchor order. Require increasing source anchors or an explicitly reviewed order-preserving implementation. Any intentional deferral needs a separately reviewed population and sampler.

2. **BLOCKER — token audit can falsely authorize launch.** `scripts/token_audit.py:summarize` reports `launch_ready=true` for an empty shard, a single pose row, and duplicated partial shards.
   Fix: bind config, preparation, sampler, stores, horizon, and shard identities by SHA256; require complete, unique coverage of the expected planned rows and every required field before returning readiness. Reject missing, duplicate, mixed-run, or incomplete shards.

3. **BLOCKER — planned first batches are MISSING.** `configs/r1_config_f64.json` lacks `r2_sampling`; its preparation is MISSING at `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/f/469ddece/receipt.json`. Code, admission, and depth-init pins are also MISSING; exact paths appear in `resume_review.json:missing_inputs`.
   Submitted full-depth evidence covers synthetic pose batches on ranks 0–3 and other streams only on rank 0; it uses substitute sampling and omits extent/membership/init bindings. The headline claim of full forwards for every rank of every stream overstates those files.
   Independent full-depth CPU check: all four synthetic ranks passed with finite losses, 9,127 tokens each and peak RSS 23.89 GiB (`forward_review.json`). Synthetic evidence cannot satisfy the planned-run gate. Bind genuine inputs, reseal the changed tree, then pass each rank's actual first batch through the complete CPU forward before any GPU use.

4. **BLOCKER — memory and step time remain estimates.** Meta construction confirms the real Qwen3.5 base: 9,409,813,744 parameters, 32 language layers and 27 vision blocks. Full forwards use random initialization; `mem_n32_8.json` and `mem_f64_8.json` use only eight language layers.
   Their batch size is one, and non-reentrant language checkpointing matches N, but gradients are BF16; they omit FP32 masters, FSDP, Adam states/updates, and the full accumulation cycle. The planned run uses four ranks, global batch 288, and 72 microsteps per rank.
   Eight-layer pose RSS increments are 10.601 versus 14.613 GiB; these are CPU allocator measurements, not GPU training peaks. The kit's 43.57-GiB static budget is analytic, and its head trainable count is inferred from rounded gradient bytes rather than counted exactly.
   Fixture lengths are 9,127–10,215 tokens, not a real-row maximum. The hard-coded GPU line gives 69.49–72.43 GiB there and 89.09 GiB at the 16,384-token ceiling. Its cited H100 calibration logs are absent from this kit.
   Thus 48-GB cards are unsupported for the current non-offloaded training configuration; 80-GB cards are plausible for short rows but unproven for the population. GPU reading/generation memory is unmeasured. The 1.91× FLOP estimate and 263/627-second step estimates are conditional; the independently recomputed CPU-forward ratio is 2.30×.

5. **minor — the export-layout helper checks less than documented.** `read/f64_read.py:training_layout` accepts a missing artifact `frame_input` when the config supplies it. The full reader separately authenticates the config hash, so this helper-level counterexample alone does not establish an end-to-end binding bypass.
   Require explicit matching declarations and validate the spec, or document the authenticated-config fallback; add absent/null/mismatch tests. Reading remains blocked by MISSING filled frame pins: `READ_CONFIG_F64.json:settings_add.student_manifest` is a placeholder.

6. **minor — anchor preservation is supported.** `PATCH_LINES.md` lists every removed/added line in both patches; `resume_review.json` retains their exact text. The sealed baseline matches archive SHA256 `caa09d0c6aa79f55ee7ddf0dbe4580145a1e483a164226678539f554e8af6a36`.
   The nine changed tree files contain no scoring or room-rule edits. Frame-spec gates, pointing provenance, anchor-only depth/markers, and pixel-default normalization have documented reasons; the 12 layout tests pass. Markers remain `Frame 1..32` on the original anchors for the tested increasing-anchor inputs; finding 1 limits the general claim.
   Clarify installation as `src/b/f64_read.py` for the patch's absolute imports, or use relative imports when installing inside `e2e_reader`; the current “install_beside” wording is ambiguous.

7. **minor — the baseline error is pre-existing, not proved harmless.** Both independent suites run 109 tests with zero assertion failures and the same one error: MISSING `/scratch/jjyeung/orch_cd/derivgen/review_pool/POOL.jsonl`.
   The unexecuted test checks trace-revision rerendering of `<closest>`; its code is unchanged. Supply the authentic pool and rerun that test before claiming a completely passing baseline. Do not fabricate a replacement pool.

8. **BLOCKER — evidence required to change the decision.** Correct the store and audit gates, resolve the export-check contract, bind the real preparation, sampler, and reader manifest, and pass actual all-rank CPU first batches and the complete token audit.
   Only then use a four-rank 80-GB GPU pilot with the intended kernels, FSDP, FP32 masters, checkpointing, and initialized Adam state. Measure allocated/reserved peaks through optimizer updates, longest planned rows, and steady full mixed steps. CPU offload needs separate measurement; world eight changes N's fixed recipe and row plan.
   No GPU is needed to fix the code or supply the missing CPU evidence. This review used no GPU, network, Git, or writes to the builder's workspace.

Commands and provenance: run from `/scratch/jjyeung/orch_n30/sb_f64rev`.

- `python review_static.py` produced the sealed-tree comparison; `bash run_cpu.sh regression_check.py baseline` and `bash run_cpu.sh regression_check.py patched` produced the two regression counts.
- `bash run_cpu.sh behavior_check.py` produced layout tests, architecture counts, and store/export counterexamples; `bash run_cpu.sh resume_audit.py` revalidated saved hashes, enumerated patch lines, reproduced audit counterexamples, and recomputed token/memory/time figures from submitted evidence.
- `bash run_cpu.sh forward_check.py` produces the independent CPU-forward records. Review JSON files record input SHA256 values; the builder's evidence JSON files do not bind their generating inputs.
- `bash run_cpu.sh anchor_order_check.py` produced the explicitly adversarial anchor-order counterexample; it does not represent a real planned training row.
