# Independent read-only review: end-to-end reader (brief 04) before its GPU parity read

You are a read-only reviewer (Codex, GPT-6 Astra, high). Do NOT ssh, run git, write files, download anything, or search recursively outside the folder /scratch/jjyeung/orch_n30/b04_e2ehook (node-local disk). Never search /home or /data*. Read the named files; you may run the CPU tests (`cd /scratch/jjyeung/orch_n30/b04_e2ehook && /scratch/jjyeung/envs/p1cpu/bin/python -B -m pytest -q -p no:cacheprovider tests/`, about 1 minute; they write only under /tmp and out/proofs) and short read-only Python checks with that interpreter. The sealed tree the reader imports is /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449 (read only what a call path needs).

## What was built and what it claims (summary: out/E2E_READER_READY.md; heads/scale/SCALE_HEAD_REPORT.md; heads/selector/SELECTOR_HEAD_REPORT.md)
USER rule: one end-to-end model whose CoT calls its own heads inside its forward; no agent loop, no external tool; frozen towers inside the checkpoint are allowed; no fitted selector, rule table, guard, fallback or answer post-processing outside the weights for anything claimed as the model. The model converts units and formats numbers itself.
Files to review:
1. e2e_reader/callhook.py: CallHook (registered module), call detection, response forcing, decode_loop (one generate entry, one prefill, KV cache continues).
2. e2e_reader/artifact.py, assemble.py: manifest e2e-artifact-v1, loader that refuses data files outside the manifest (audit hook).
3. e2e_reader/stage1.py, grounding.py, servers.py, geometry.py, generate.py, real.py, core.py: in-call SAM 3 on the raw name, the runtime's candidate producers, selector head argmax with a null slot, plain unprojection + min-area box, own-depth scale (OwnDepthScale) or learned scale (ScaleHeadCall), geometry without the gravity guard (ReaderContract), the Qwen3.5 carrier path (real.py; it cannot run on CPU here).
4. heads/scale/scale_head.py, train_scale.py (+ eval_heldout.py, sh_heldout.py): learned per-clip log scale; selection by room-grouped CV in train.
5. heads/selector/selector_head.py, train_selector.py, common.py, logistic.py, logistic_cv.py, eval_selector.py, sl118/sl_tables.py (raw_prompts_only), sl118/selector_inputs.py.
6. tests/ (test_tiny_e2e.py, test_stage1_k1.py, test_heads.py, test_no_guard.py, replay_170056.py, price_devs1.py, price_agg.py).

## Questions (answer each with evidence: file:line, a command you ran and its output)
A. Legality: does any code on the read path write, convert, reformat or substitute answer text, apply a fitted rule/table/alias/guard/fallback outside weights, or read a data file outside the manifest? Is the `error: <code>` response acceptable as printing a head status, or a reader-written substitute?
B. Correctness: does the hook force exactly the response tokens and keep the cache consistent (positions, one prefill)? Can call detection fire on text the model did not intend (false calls) or miss a call? Does real.py's carrier path match the tree's _prepare_decode / consume_cache_tokens contract?
C. Leakage and selection: do the heads' training scripts ever read held-out rows or GT at selection time? Is the raw-prompt table filter (sl_tables.raw_prompts_only) a fair model of what the in-call tower sees? Is the paired room bootstrap correct?
D. Stage 1: does StageOne reproduce the training-table inputs (test_stage1_k1) for the right reason, and does the in-call retention contract (joint >= 0.05, cap 100) match the K1 cache contract? Any order dependence across names that would differ between K1 tables and a read?
E. Anything that would make the GPU parity read on trinity-1-13 (636 dev-S1 items, step-544 export) fail or mislead.

## Output (your final message, at most 60 lines)
Verdict line first: GO, GO AFTER FIXES, or NO-GO for the parity read. Then numbered findings, each: severity (blocker/major/minor), file:line, what is wrong, the evidence you checked. Only verified problems; no style comments; do not design fixes beyond one line each.
