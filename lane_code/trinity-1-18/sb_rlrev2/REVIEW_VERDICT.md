# sb_rlfix re-review verdict: GO AFTER FIXES (finding 4 still blocks; 3 new minor findings)

Ten of my 12 findings are closed and reproduce on the fixed code; finding 12 is partly open and finding 4 is open. The kit still rolls out through N's `carrier_c1_decode.generate`. The deployed claimed arm uses a different reader, whose scale, lifting, grounding, budget and call caps all differ. Launch also still waits on N's MISSING pool, `init_m544` evidence and export pins. Evidence is in `runs/v2/` (scripts, outputs, `CLAIMED_ARM_BINDING.md`) and in `runs/kit/`, an extract of `sb_rlfix.tar` (sha256 `feb43f05…` checks) that matches the workspace byte for byte.

## My 12 findings
1. CLOSED. `native_kwargs` drops `trace_program_version`, and all 12 native calls bind (`v2/signatures.out`).
2. CLOSED. Correctness is `score_item`'s score: 0/74 mismatches in my `v2/parity.out` and 0/110 in the kit's test (`kit/out/PARITY.json`).
3. CLOSED. A fake early `</think>` now scores 1.0 against 1.1 for the honest trace (`v2/double_think.out`).
4. OPEN, blocker; see the next section.
5. CLOSED for refusals, gradient all-reduce, 25-step checkpoints and refusal logs (`train.py:150-198`). I correct one point from my first review: the deployed arm does not allow 200 calls. It stops distance at the 6th call and room at the 2nd (`parity_adapter.py:11,28-33`), so `max_calls=200` (`rollout.py:32`) is wrong.
6. CLOSED. Wrong answers earn 0 auxiliary reward, and both call sites pass `scale_std=False` (`v2/gaming.out`).
7. CLOSED. A spurious `<pose>` call now gets route 0 (`v2/gaming.out`).
8. CLOSED. The production `RoomGate` admits none of the excluded lists (53 / 100 / 274 / 372 / 720 / 2,084 / 2,424), admits all 233 controls with 0 physical overlaps, and the tests now use it (`v2/gate_check.out`).
9. CLOSED. `pool.clean_row` is now an allow-list; edit E below adds a prompt-equality check.
10. CLOSED. The CPU proof reruns PASS bit-identically (gradient L1 4186.33, update L1 1.966, ratio error 0.0228; 114 s, 14.63 GiB), and 34/34 tests pass (`kit/out/`).
11. CLOSED as supplied but not run: `dry_run.py` times 2 steps of 32 sequences on 1 GPU and refuses until bindings exist.
12. PARTLY OPEN. The old claims are fixed, but `README.md:17` now states as fact that the default arm is "frozen G3T for camera and lifting, SAM 3 with the deployed selector, fixed math for scale and gap", and `REPORT.md:10` says own heads are diagnostic only. Finding 4 shows that lifting, scale and selector all differ, and that the claimed arm reads two own heads.

## Finding 4: is "claimed-arm serving table MISSING" honest?
It is honest about the inputs supplied, and production refuses (`serving.py:14-18`). It is wrong that the table does not exist: it sits on this node, and the fix lane searched only N's tree. Worse, the kit demands `validate_claimed_arm` and `build_backend` (`serving.py:24-28`), which the deployed reader does not define (the only `build_backend` is N's MDG builder in `s1_grounding.py`), so no real file could ever bind. The claimed arm is the `tower` arm of out3 read A4 (`h1eval/h10/launch.py:276` calls `b/e2e_reader/parity.py:make_real`). Its root on this node is `/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/`; `cont_ops16/work/c15/r1route/out3` is absent here. Bind these files (full hashes in `v2/CLAIMED_ARM_BINDING.md`):
- Settings table: `A4/ret/metadata/reads/0/metadata/0.json` (`2c3cc6b4…`), with arm=own_depth, stage1_select_rule=candidates_argmax, sam3, selector_head and the G3T memo, plus the arm descriptor at `A4/tower_sequence.py:9-12` (`97c8e6df…`).
- Reader: `A4/package/0.tgz` (`4498fca7…`), containing `h1eval/h10/parity_adapter.py`, `b/e2e_reader/{parity,real,stage1,servers,geometry,callhook,grounding}.py` and `b/work/c8r/.../native/out2/reader_policy.py`. Do not bind `/scratch/jjyeung/b01ec87a6f29b/p`: 6 of its 8 reader files differ from A4.

The kit's path diverges from this reader in five ways. The claimed arm also reads two own heads, gravity (`real.py:64-67`) and depth for scale (`stage1.py:41-60`), so "own heads are diagnostic only" must exclude them.
- Scale: N gates own depth to 0.1–10 m (`tower_scale_rule.py:12`), while the deployed `median_ratio` accepts any positive depth (`stage1.py:70`).
- Lifting: N's tower path replaces pose only (`tower_read.py:323`) and answers `depth_at` from the own depth head (`carrier_c1_decode.py:203-210`). The deployed reader reads G3T depth (`geometry.py:111-113`).
- Grounding: the deployed reader uses a learned selector head with `candidates_argmax` and K1 retention (joint ≥ 0.05, at most 30 per frame; `stage1.py:117-160`). The kit checks only `mask_source=='svp_sam3'` (`serving.py:36`), which N's `ofs` backend also passes (`ground_profiles.py:31`).
- Budget: the deployed reader forces `</think>` after 2,048 thinking tokens and then allows 64 answer tokens (`reader_policy.py:7-10`). The kit emits EOS after 1,024 tokens (`choice.py:97-99`), which scores 0 where deployment would answer.
- Call caps: the limits from finding 5 apply. A 7-call distance trace scores 1.2 in the kit (`v2/new_probes.out`), but deployment stops it with no answer.

## Exact edits
A. Decode rollouts through `real.generate_real` with the kit's adapter-installed model, the capped hook, and `real_perception(stage1_select_rule='candidates_argmax', perception_memo='on', perception_memo_modules=['g3t'], sam3_tower=Sam3Tower(settings['sam3']), selector_head=...)`, built as in `parity.py:210-235`. Pass `logits_processor` as a sampler applied after `ThinkingBudget(DECODE_BUDGET)`, and give budget-forced ids kind 'b'. Then remove `pose_source`, `tower_state`, `attach_tower` and `prepare_tower` from `train.py` and `rollout.py`, and replace the interface in `serving.py` with pins of the files above.
B. Adopt the deployed caps (distance 6, room 2) and the deployed budget, or record an orchestrator ruling that RL trains under a different budget than the one it is scored with.
C. Before training, replay greedily on GPU with A4's m200 export (`A4/ret/metadata/EXPORT_PIN.json`). The replay must reproduce A4's journal tokens for 4 items per type.
D. Minor (new): a far numeric answer (7 against 12.19, MRA 0.2) still earns the full 0.2 auxiliary reward (`v2/new_probes.out`). Fix: add `short*=c; route*=c` after `reward.py:77`.
E. Minor (new): at pool build, assert that `prompt_batch(clean_row(row))` gives the same ids as the raw row, as N's `assert_prompt_equal` does. `carrier_c1_data.py:167,365` branch on `pose_sample` and `pointing`, which the allow-list drops.
F. Minor (new): no test executes `train.run`'s step loop. Add one CPU step with a stub model and one refusing rank.

## Tests (34)
The tests exercise real code for the reward, the production room gate, REMOVE lists, the allow-list, masks, KL, clipping and checkpoints. Parity is near-tautological: `score` passes the same dict to `score_item`, so the test checks only the field mapping. Serving, refusals and collectives are tested only through mocks, and no test touches the deployed reader.
