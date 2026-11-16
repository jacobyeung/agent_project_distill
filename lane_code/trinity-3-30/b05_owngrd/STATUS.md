# b05_owngrd STATUS (Devin lane on trinity-3-30, successor of the Claude lane; brief briefs/b05_owngrd.md -> briefs/qs/05_own_grounding_head.md)
Goal: own-encoder grounding head (branch O): teacher pass (SAM 3) -> label audit -> pilot -> full train -> K1/dev-S1 read -> attach. GPU only with ORCH_CARD; no Orchard.
## Facts
- F1 Shared Qwen ViT FROZEN in D0 (b01ce449) and A2 tree: carrier_c1.py:133-136, full_ft.DEFAULT_TRAIN vision_blocks False, merger False. Head may train on step-544 ViT taps.
- F2 Pool kit_k1a CAPTURES.json: 2,343 captures; my gate admits 1,985. K1 pilot 300; 11 in withheld_80 refused; 3 ARKit lack GT -> TEACHER_K1 manifest 286 (233 train, 53 heldout), 4,546 name prompts (gt 2832, confuser 1144, absent 570).
- F3 K1 SAM 3 pass mirror trinity-3-30:/scratch/jjyeung/n30_mirror/k1_ops3/run_tower_sam_2 (300 dirs; operand phrases only). Dir->capture map work/k1map/DIR_TO_CAPTURE.json (97c15164...).
- F4 trinity-1-18: /scratch/jjyeung/k1_frames (K1 frames), envs/sam3_capretry_native_v1 (7.4 GB), k1/m544_parts, orch_cd/{mdg_build,own_probe,dose_pool,mdg_next}.
## Done (paths under /scratch/jjyeung/orch_n30/b05_owngrd)
- work/auth/: exclusion authorities + K1 manifest copies, SHA256SUMS.
- code/owngrd/: common.py, eligibility.py (Gate), vocab.py, build_manifest.py, teacher.py (resumable SAM 3 runner), stub_tower.py, vendor/ (kit_k1a sam3_tower, sam_backend, phrase + VENDOR_SHA256SUMS). code/tools/st_extract.py. code/owngrd/labels.py (triage POS/HARDNEG/MISS/ABSENT/DISPUTED, presence only where GT and SAM 3 agree). code/tests/: 16 pass (eligibility 6, teacher 5, labels 5): `cd code && /scratch/jjyeung/envs/p1cpu/bin/python -m pytest -q tests -p no:cacheprovider --basetemp=$L/tmp_pytest`.
- teacher.py CONTRACT = design 3.1: joint floor 0.2, cap 10.
- Real SAM 3 smoke on trinity-1-18 CPU passed (2 frames x 2 names, 38 s; SAM3 upstream hardcodes cuda, so CPU smoke monkeypatches device; GPU run needs none): work/x118/smoke.py, smoke_out.json.gz. ARKit GT rasters are partial (tv raster = corner sliver inside SAM 3 mask): expect low ARKit POS yield.
- trinity-1-18 holds code+auth+TEACHER_K1 at the same paths (/scratch/jjyeung/orch_n30/b05_owngrd/{code,work/auth,work/manifests}) and work/x118/launch_teacher.sh <card> <i/n> (tmux b05_teacher_<i>o<n>, vnice, out .../teacher_k1).
- QUESTION event card_teacher_k1 asked for 1-2 cards on trinity-1-18.
- Head build brief work/codex/HEAD_BUILD_BRIEF.md (env allospatial_1111_v1: only env with torch+torchvision+scipy+transformers qwen3_5).
- work/manifests/TEACHER_K1.json sha 4d4736cf64e496a184d36d74d710e76d1673429e28790613794867ac077048a9.
- work/m544sub/sub/subset.safetensors (334 tensors visual+embed_tokens, 2.95 GB) sha 3891d92a189bd111435190b5cc477be73617c28ad8c01baf72b8feb4bfa9343f (verified on 3-30).
- work/from118/: MDG t0bundle/base, resnet18-f37072fd.pth, own_probe_delivery_r3.tar.gz, g3t_taps.py, room_gate.py.
- work/gt/: K1_GT_RASTERS_259.tar (823ca442...), K1_GT_RASTERS_GTB2_37.tar (6630711...), extracted gt/x (296 npz).
- work/frames/: 384 frames of 12 test captures (inv/frames12_caps.json).
- Head kit DONE (Codex b05_head_build2 + my presence-head fix): code/owngrd/{vit,head,losses,data,train,export}.py, code/HEAD_README.md, tmp_codex/BUILD_REPORT.json; hashes work/CODE_SHA256SUMS_20261116T1355Z.txt. Env /scratch/jjyeung/envs/allospatial_1111_v1 (6.4 GB; only env with all deps). Tests: `cd code && OMP_NUM_THREADS=16 /scratch/jjyeung/envs/allospatial_1111_v1/bin/python -m pytest -q -p no:cacheprovider --basetemp=<new dir> tests` = 34 pass 1 skip; real ViT: OWNGRD_REAL_VIT=1 ... tests/test_head_kit.py::test_real_vit_first_batch passes (tmp_codex/REAL_VIT.json).
- Real-label CPU runs: tmp_real/run1, run2 (manifest tmp_real/man4.json: 4 ARKit captures, frames in work/frames; labels work/labels_partial from 38 pulled teacher captures in work/pull/teacher_k1). Codex originals of edited files: work/codex/{head,train}.py.codex_orig.
- owngrd/audit_sample.py renders POS/MISS contact sheets + AUDIT_SAMPLE.tsv for the P7 audit (tested on stub).
- RESULT head_kit_ready_review_request (13:5xZ) asked ORCH for the refute review and a pilot card.
- K1 teacher pass DONE 14:30Z (286/286, 0 failures): 3-30 work/teacher_k1_full/teacher_k1 (120 MB); copy still in trinity-1-13:/dev/shm/jjyeung/b05 (REMOVAL_CANDIDATES.md). Cards 2,3 on 1-13 released (idle since 14:29/14:31Z).
- Labels DONE: work/labels_k1 (286 captures, LABEL_SUMMARY.json sha 80cf2afb...): POS 19,817, HARDNEG 46,795, DISPUTED 8,673, MISS rows 25,952; agreed positive frames 13,896, ABSENT 103,134.
- All 9,152 K1 frames now on 3-30: work/frames (2.4 GB).
- Mirror: trinity-1-18:/scratch/jjyeung/n30_mirror/b05_owngrd/B05_K1_TEACHER_LABELS.tar (teacher_k1_full, labels_k1, manifests, auth), 150,261,760 B, sha256 7e9b6d8e4d98056bff9718b251865f9a9e7ba9800343a966f2e46a3d6141f62c (equal on 3-30 work/).
- Audit proxy: work/audit_p7 (96 tiles, sheets 00-05, AUDIT_SAMPLE.tsv; I viewed sheets 00, 02, 05; verdict column not filled).
- Review review_owngrd DONE: GO AFTER FIXES (events/review_owngrd/REVIEW_VERDICT_OWNGRD.md, 8 fixes); ORCH ORDER 1428Z: fix all eight, reviewer tests (review_owngrd/work/code2/tests/test_review_refute.py, test_review_resume.py) are the gate, pilot cap 4 A6000-h, then pilot may take a gpu_fill2 card, no third review.
- Record: distill_design/OWN_GROUNDING_HEAD_K1_20261116.md + INDEX line (pilot bar = 0.70 x unambiguous recall@5 ceiling, fixed before the pilot).
## In flight
- Codex Astra b05_head_fixes (14:47Z): brief work/codex/FIXES_BRIEF.md; receipts /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261116T144753Z_b05_head_fixes/; delivers tmp_codex/FIXES_DONE.md, updated BUILD_REPORT.json, tmp_codex/smoke_fix. Do not edit code/ while it runs.
- No GPU job, no governor stream, no Orchard job.
## Next
1. When Codex finishes: run the full suite (allospatial env) incl. reviewer tests, check FIXES_DONE.md against each verdict item, re-run real-ViT first batch, write new CODE_SHA256SUMS.
2. Build the pilot manifest: `python -m owngrd.split_manifest --in work/manifests/TEACHER_K1.json --split train --out work/manifests/TRAIN_K1.json`; frame paths must point where the pilot runs.
3. Ask gpu_fill2/ORCH for one A6000 (QUESTION event); stage env allospatial_1111_v1 (6.4 GB) + m544sub (2.9 GB) + frames + labels + teacher + code to the card node (/dev/shm on 1-13 already holds frames; check du first, list in REMOVAL_CANDIDATES.md); run pilot `python -m owngrd.train ... --device cuda --hours 4` under vnice in tmux; poll every minute then 10 min.
4. After the pilot: stop-rule verdict RESULT; K1 held-out read plan (53 captures) vs SAM 3 + selector.
5. Extension beyond K1 (more pool captures need frames + GT rasters, builder events/gt_build2): ask ORCH after the pilot verdict.
## Defaults in force
- No GPU until ORCH_CARD. Frame count parameter 32/64 (USER ruling): K1 block has only 32 frames and 32-frame rasters. ReVSI first for reads. MISS weight 0.25.
Updated: 20261116T1453Z
