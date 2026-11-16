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
## In flight
- Codex Astra dispatch b05_head_build (started 12:49Z): receipts /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261116T124913Z_b05_head_build/ (transcript.log); check `grep b05 .../codex_runs/RUNNING.registry`. Writes code/owngrd/{vit,head,losses,data,train,export}.py, tests, code/HEAD_README.md, tmp_codex/BUILD_REPORT.json.
- K1 teacher pass on trinity-1-13 cards 2,3 (ORCH_CARD 1259Z), launched 13:12Z, tmux b05_teacher_0/1 under vnice; inputs /dev/shm/jjyeung/b05/{stage,lane}; outputs /dev/shm/jjyeung/b05/teacher_k1 (DONE.json per capture, PROGRESS.<i>of2.jsonl, worker_<i>.log). Poll: work/x118/poll113.sh via tssh trinity-1-13. Manifest TEACHER_K1_113.json sha 886e47a3... (frame/gate paths moved to /dev/shm). ~30 s/capture/card, ETA ~14:30Z. 1-13 /scratch is below floor: write nothing there.
- Codex dispatch b05_head_build2 (first dispatch died at launch): receipts .../codex_runs/*_b05_head_build2/.
- No governor stream, no Orchard job.
## Next
1. When the teacher pass completes (286 DONE.json): tar teacher_k1 from 1-13 over IB to 3-30 work/teacher_k1 and to 1-18; then run `python -m owngrd.labels --manifest work/manifests/TEACHER_K1.json --teacher-root .../teacher_k1 --out .../labels_k1` on 1-18, bring LABEL_SUMMARY + labels back over IB.
2. When Codex finishes: run its tests myself, inspect BUILD_REPORT, then RESULT asking ORCH for an independent refute review (eligibility + training code) before the pilot.
3. Label audit (step 2): POS yield per dataset, P7 proxy on a sample (visual check of overlays).
4. Pilot (step 3) needs ORCH_CARD + review; env allospatial_1111_v1 must be copied to the GPU node over IB (ask size first).
5. Mirror sealed code/labels to a second node.
## Defaults in force
- No GPU until ORCH_CARD. Frame count parameter 32/64 (USER ruling): K1 block has only 32 frames and 32-frame rasters; 64 needs the extension blocks. ReVSI first for reads.
Updated: 20261116T1313Z
