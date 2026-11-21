# fix3 REPORT: 174101's processor refusal, root cause and kit fix (updated 2026-11-21T10:02:24Z)
Work folder on trinity-1-18: W27 = /scratch/jjyeung/orch_n30/tree_rebuild10_w/w27fix. Packet: B/events/tree_rebuild/fix_proc/ (25 files + SHA256SUMS: diffs, old/ and new/ files, logs/, gpu_test/, scripts.tar, this report as FIX3_REPORT.md).
Design record: /data2/jjyeung/agent_project_data/distill_design/N_LAUNCH_174101_PROCESSOR_REFUSAL_20261121.md (INDEX.md line added).

## 1. VERDICT (item 1), settled 09:37Z by a CPU run on trinity-1-18: (B) family, and not in the forward
**The refusal is raised in-process, by the opener-witness step of production_proof._run, before admit and before the
forward. b/fw.py never ran in 174101, and the fresh interpreter loses nothing: (A) is false.** The reviewer's (B) names
the right cause (a folder of hash-named files) in the wrong place: the forward's own processor load uses
manifest['root'], the staged snapshot folder with real names, and resolves it identically in-process and through b/fw.py.

Evidence 1, the job's record (X/o/174101/q0.json): `steps = ['direction_twins', 'training_components']` and
`forward = 'not requested'`. _run appends 'p_opener_witness' after lines 128-134 and 's1_routing.build' after admit;
neither is present, so `opener(cfg, root/'v.json')` (line 130) raised.

Evidence 2, the code (launch_r1/p_opener_witness.py:17-26, prepared_vocabulary):
`root = pinned(dict(path=str(Path(manifest['root'])/'config.json'), sha256=files['config.json'])).parent`, then
`processor_for_receipt(dict(manifest, root=str(root)), receipt)`. pinned() relocates by sha256, and the kit maps every
model metadata file to p/q/u/<sha256> (z.py:266-274, pl.py:173 and 320-321). `.parent` is therefore the pool p/q/u.

Evidence 3, the run on the unfixed kit 06d9a1b5 (W27/t1/t1_old.out = packet logs/t1_unfixed_kit.out). Inputs: the kit's
own tree tar, the real model manifest cc724d5e, P's real config b08fe50c and preparation receipt a5bbef1b, the nine real
non-weight model files, weight shards as placeholders. bwrap gives the job's path names. CVD='', p1cpu, transformers 5.12.1.

| call | pid | folder handed to processor_for | holds | outcome |
|---|---|---|---|---|
| witness in-process (as production_proof runs it) | 1759471 (parent 1759464) | `/tmp/q_22c714e1/p/q/u` | 0/8 named, 81 entries | ValueError:Unrecognized processing class in /tmp/q_22c714e1/p/q/u. Can't instantiate a p |
| forward resolution in-process | 1759471 (parent 1759464) | `/project/community/jjyeung/c7d31ddd/runs/aws128p_20261025/models/a32330d0/snapshots/c2022362...` | 8/8 named, 13 entries | ImportError: Qwen3VLVideoProcessor requires the Torchvision library but it was not found |
| forward resolution through b/fw.py (fresh interpreter) | 1759526 (parent 1759471) | `/project/community/jjyeung/c7d31ddd/runs/aws128p_20261025/models/a32330d0/snapshots/c2022362...` | 8/8 named, 13 entries | ImportError: Qwen3VLVideoProcessor requires the Torchvision library but it was not found |
| witness through b/fw.py (control) | 1759557 (parent 1759471) | `/tmp/q_22c714e1/p/q/u` | 0/8 named, 81 entries | ValueError:Unrecognized processing class in /tmp/q_22c714e1/p/q/u. Can't instantiate a p |

Row 1 reproduces 174101's refusal text and folder exactly. Rows 2-3 resolve one right folder in both processes; the
ImportError there is the first test environment lacking torchvision (the rerun in section 3 instantiates). Row 4 shows the
child fails as the parent does, so the path scope reaches the child intact.
Model manifest (sha cc724d5e, from the milestone's small-file archive): root =
/project/community/jjyeung/c7d31ddd/runs/aws128p_20261025/models/a32330d0/snapshots/c2022362..., 13 files. The job script
stages that folder by name (tk_stage_model, q.steps "model staged: 18876304 KiB") and binds it; s1_routing.py:219
(file_pin(root/'tokenizer.json')) already passed there in 174101. N's own pose stream chain (8957d119 -> 30612832) pins
the same manifest, so N's forward uses this root.
Consequence: 173964 (no fw.py, exit 1 at the same point) most likely died of this witness step. No earlier mode-q run reached it.

## 2. FIX (kit only; tree seal unchanged; k/ unchanged)
New kit W27/n_go, seal **4e29bdfb8754e85ffbb959eab3be31b33b4f2ce7e4c126f9a11f6f1e6024c992** (was 06d9a1b5).
Tar W27/s27fix_n_go.tar, sha256 **211d2e902d49b4b7baaf1d4828e82963b99d66e4108283ed483c4b6f93a04609** (prefix n_go/, 60 entries).
Changed files (diff -rq vs W/w26fix2/n_go shows only these plus SHA256SUMS.txt and BUILD.json):
- b/pl.py d014bb296ba4f84f976f8aee7706c62768ea430b18f35bd39542b13466c4c31d (PL_PY.diff)
- b/a.py 22b57fae3aa6863a339aaf323311dc491951b898badd4613d52ba85291b92ced (A_PY.diff)
- b/mg.py (new) 986063ccb915a76ebc1dc4ec3d068005575455077129268169d3c5ae9b032b1f
- b/pf.py (new) 2f0bbefe00f76dfb2ff8a6ebfdaf2664c69ec0840f8e2c46b14da7e710c16e45
- BUILD.json 69b11a3906d41baf1e22ac2fda553a33431893401a157e47949b75f5b560c735 (payload differs only in kit_sha256); launch_r1.build.verify accepts the kit.

(a) Resolution repair, mode q only (b/pl.py). **The processor folder of the witness becomes /tmp/q_22c714e1/p/q/y.** The stage
hook creates p/q/y (mode 0700) after its copies and hard-links into it, under their manifest names, the nine non-weight
files of the model manifest (chat_template.jinja, config.json, merges.txt, model.safetensors.index.json,
preprocessor_config.json, tokenizer.json, tokenizer_config.json, video_preprocessor_config.json, vocab.json), each from
p/q/u/<sha256> and each checked against its sha256 (pl.named_folder, the pattern z.py uses for w/). The path scope the
hook enters then maps those nine hashes to p/q/y/<name>. Every other pin, the config bytes, the request and the staging
plan are unchanged (the names are added to the scope only, not to `paths`), so n.json and its identity do not move.
Mode r is untouched (`named` stays empty under regeneration).
(b) Preflight (new b/pf.py, called twice by pl.py in mode q): at the end of planning, before any long step, it copies the nine
files into p/i/y and runs the tree's own prepared_vocabulary on P's config plus the forward's processor load
(processor_for(manifest['root']), every manifest file present by name, small ones sha-checked) for P's manifest and
for the manifest N's pose stream pins; it runs again after the stage hook on the final layout. A failure refuses with
R1_PROCESSOR_FOLDER_UNUSABLE:<cause> (r0.json at plan time, q0.json at stage time). First firing: when planning ends,
a few minutes after "stage full done" (my estimate T+25 to T+30; the plan's duration was not measured), not T+60.
(c) Mask guard (new b/mg.py, used in b/a.py inside the existing admit wrapper): for the duration of admit(), while
CUDA_VISIBLE_DEVICES is empty, torch.cuda.is_available() is False, device_count() is 0 and _lazy_init() raises
"No CUDA GPUs are available", none calling the driver; the three originals are put back when admit returns, which is
where _run lifts the mask. The RLIMIT_AS restore stays.
(d) Forward dispatch: unchanged. The forward still runs through b/fw.py (bytes unchanged, ae4d7c15). Under (B) the order
asks for the repair and the guard only, and item 1 shows fw.py resolves the forward's folder as the in-process call does.
If you want the in-process forward first with fw.py as the fallback on "No CUDA GPUs are available", that is a
three-line change in a.py and a new seal; say so.

## 3. TESTS (all on trinity-1-18, CPU, CVD=''; outputs under W27/work and packet logs/)
| test | result | output |
|---|---|---|
| T1 item-1 run on the unfixed kit: witness -> p/q/u refuses with 174101's text; forward -> snapshot folder in both processes | reproduces | logs/t1_unfixed_kit.out |
| T2 (a) item-1 test on the fixed bytes (kit's pl.named_folder and pf.check on the job-layout replica, then the tree's witness and forward; p1cpu + torchvision 0.26.0+cpu) | PASS | logs/t2.out |
| T2 control: pf.check on the unfixed mapping refuses with 174101's text | PASS | logs/t2.out |
| T3 wiring: the fixed kit's real pl.plan_payload and real stage hook (z.copy_resolved_payload included) end to end on a synthetic handover with the real manifest, P config, P receipt and nine files; pf.check called by the kit at plan (p/i/y) and at stage (p/q/y); y = exactly the nine names, hard links, 0700; scope maps the nine hashes to y, other pins stay in u, export names stay in w; tree witness passes under the scope the hook leaves entered | PASS | logs/t3.out |
| T4 (b) load list resolved by the tree's own calls on the replica | see section 4 | logs/t4.out |
| T-guard: under the mask the guard gives False / 0 / "No CUDA GPUs are available" with 0 calls to the driver entry points (stubbed counters), the real import of transformers.models.qwen3_5.modeling_qwen3_5 under the guard makes 0 such calls, an unguarded is_available() under the mask reaches the entry once; originals restored after the block and after an exception; a.py's real block: admit is the wrapper, guard active inside admit, originals and RLIMIT_AS restored after | PASS | logs/t_guard.out |
| fix_spawn regression (t_fw.py T1-T4 on the new kit): forward wrapper installed, child result and f.json equal to in-process, exceptions equal (the constructor-args case differs as in FIX2) | PASS | logs/t_fw_after.log |
| seal, diff -rq, parse, modes 644, no __pycache__, tar round trip identical, build.verify | PASS | W27/work and rd/run2.out, rd/run5.out in fix3/ (scripts in scripts.tar) |

T2 rows on the fixed bytes:
| call | pid | folder handed to processor_for | holds | outcome |
|---|---|---|---|---|
| witness in-process (as production_proof runs it) | 1784858 (parent 1784851) | `/tmp/q_22c714e1/p/q/y` | 8/8 named, 9 entries | instantiates |
| forward resolution in-process | 1784858 (parent 1784851) | `/project/community/jjyeung/c7d31ddd/runs/aws128p_20261025/models/a32330d0/snapshots/c2022362...` | 8/8 named, 13 entries | instantiates |
| forward resolution through b/fw.py (fresh interpreter) | 1784971 (parent 1784858) | `/project/community/jjyeung/c7d31ddd/runs/aws128p_20261025/models/a32330d0/snapshots/c2022362...` | 8/8 named, 13 entries | instantiates |
| witness through b/fw.py (control) | 1785203 (parent 1784858) | `/tmp/q_22c714e1/p/q/y` | 8/8 named, 9 entries | instantiates |

## 4. LOAD LIST: every load of the forward after the processor, on the job's layout (item 3b)
| load | tree code | resolves to | staged by | check |
|---|---|---|---|---|
| processor (tokenizer, image and video processor, chat template) | carrier_c1_run.py:1242 processor_for(manifest['root']) | snapshot folder (manifest root, section 1) | job script tk_stage_model -> $S/c7d31ddd/$RR/models/a32330d0/snapshots/<rev>, bwrap bind to /project/community/jjyeung/c7d31ddd | T2: instantiates, both processes |
| base asset authentication, sha256 of the 13 manifest files | :807-810 | same folder | same | T2/T4: all 13 names present (4 shards are placeholders on the replica; the job hashes the real ones) |
| base config + 4 shards, from_pretrained(root) | :811 | same folder: config.json, model.safetensors.index.json, model.safetensors-0000[1-4]-of-00004.safetensors | same | names present; not loaded here |
| init artifact record 5083243c | init_from_artifact: load(pinned(spec['artifact'])) | /tmp/q_22c714e1/p/q/u/5083243c... | z.copy_resolved_payload, small files -> u/<sha> | T4: real bytes resolve; init_mirror() is None under the scope, so the C1_INIT_LOCAL mirror is not used |
| LM full-weights export: full_weights.json, model.safetensors.index.json, model-0000[1-5]-of-00005.safetensors | :965-967 and 1031-1043, pinned(artifact['full_weights']).parent | /tmp/q_22c714e1/p/q/w | z.py:503-514 links u/<sha> -> w/<name>; pl.py:171-177 maps the hashes | T4: folder = w with all 7 manifest names (index and shards placeholders); T3: the kit's real code builds w and the mapping |
| heads state e72208ac (heads.pt) | :976-977 torch.load(pinned(artifact['heads'])) | /tmp/q_22c714e1/p/q/u/e72208ac... (file opened by path) | z.copy_resolved_payload links it from the export archive; cfg persisted_files maps it | T4: path resolves (placeholder) |
| routing opener vocabulary | r2_openers.initialize -> load(pinned(cfg routing_vocabulary)) | /tmp/q_22c714e1/p/q/v.json | written in the job by the witness step | exists only after the witness passes |
| depth init record fd60ac2f | carrier_c1.py:709 | /tmp/q_22c714e1/p/q/u/fd60ac2f... | upload -> stage hook | T4: real bytes resolve |
| depth encoder copy weights 04823590 (encoder.safetensors, 1824074576 B) and depth head weights 07c2d3b0 (heads.safetensors, 924151276 B) | carrier_c1.py:714-716 load_file(pinned(pin)) | not staged pins: their literal paths /scratch/fsw/.../ap/97a6a3eb/runs/b19c1200/train/step_400/{encoder,heads}.safetensors | job script tk_stage_extra (kit staging map k/l.json "extra") joins them under $U, bwrap binds $U at that prefix; q.steps of 174101 shows both "joined" lines with these sizes | cannot be opened on 1-18; single files by path, no folder semantics |
| stream databases the config pins (pose b32359ce and 0b95850a, pointing c09bb5ca, vqa 210b2534) | Rows -> pinned(database) | /tmp/q_22c714e1/p/q/u/<sha256> | all four are staged pins in 174101's q0.json 'staged' list; the stage hook copies them | not on 1-18; files by path |
| routing stream database | Rows -> pinned(database) of the stream the job rebuilds | under /tmp/q_22c714e1/p/q (s1_routing.build output, then prepare) | written in the job | not checkable before the job |
| frames | Rows, frame roots of the request | $X/data2root and $X/u/4d66fc2a/f | job script bundles f3..f14 ("frames ... verified" in q.steps) | not on 1-18; r1_loader.production_audit reads them before the forward |
No tower, align, geometry_online, mdg or b7_inputs load exists for N: the kit config has align null and none of the other keys.

## 5. GPU TEST for Orchard (item 4). Written, smoke-tested on CPU for case logic, NOT submitted.
Files: /scratch/jjyeung/orch_n30/tree_rebuild27/work/fix3/gpu_test/r.sh (sha256 3a58a238...) and t.py (84d60c29...); copies in the
packet under gpu_test/ and on 1-18 in W27/gpu_test. Token recorded in tree_rebuild27/work/ORCHARD_LEDGER.jsonl.
Stage on Orchard: D = /project/community/jjyeung/okh7/x_22c714e1/t_e7c1a94b3d20 holding r.sh and t.py; the fixed kit unpacked at
X/s27fix/n_go (tar above). Submit:
`sbatch -p general --gres=gpu:1 --cpus-per-task=4 --mem=32G -t 00:10:00 --no-requeue --job-name=a15_cot_ape7c1a94b3d20 -o $D/s.log -e $D/s.err --wrap "bash $D/r.sh $D /project/community/jjyeung/okh7/x_22c714e1/s27fix/n_go"`
Reads: the kit folder (b/mg.py, SHA256SUMS.txt; r.txt prints both sha256), the kit environment archive
/project/community/jjyeung/cp4tk_rt/kit/venv_rwtrain_torch211_cu129.tar (8.1 GB, sha ffc81db4..., extracted with the pool's
kitx.py as the launch job does) and the fla overlay archive okh7/l_94a76bda/in/d00. Writes: $D/r.txt, $D/e.txt, $D/s.log, $D/s.err
(a few KB on /project) and /tmp/a15_e7c1a94b3d20_<job> on the node (about 12 GB, left in place: the script deletes nothing).
An optional third argument gives the python of an already extracted environment and skips the extraction.
Cases, one process each, in the kit environment with the job's flags (-B -s) and the fla overlay on PYTHONPATH:
none (cuda:0 opens) | guard_import (mask, guard, real import of the module, queries, init attempt, lift, cuda:0 opens: expect
ok) | control_import (mask, same import, lift: the order expects cuda:0 to fail; if it opens, that import is not what killed
173964) | guard_query / control_query (explicit is_available and device_count under the mask: expect ok / fail, the
known poison of test 174100) | job_order_guard / job_order_control (import first unmasked, as the job really does in
the witness step, then mask and queries). PASS = guard_import, guard_query and job_order_guard all `"ok": true` with
`"patched": true, "restored": true, "avail_under_mask": false, "count_under_mask": 0`. The module name is hex-encoded in
t.py and scrubbed from r.txt, so no model word lands on Orchard.

## 6. NOT COVERED, and what to watch
- No real forward and no real admit ran. Everything after the witness (bind_target, admit/prepare, bind_prepared, bind_handover,
  admission, production_audit, forward) is still unexercised in mode q by any job; section 4 covers the forward's file resolutions only.
- pl.plan_payload and the stage hook ran for real only on the synthetic handover of T3 (uploads list emptied, selection pin
  synthetic, no room census branch). The census branch (r2_all_stream_exclusions) does not touch the new lines.
- The replica holds placeholders for weight shards, heads and depth weights; their bytes and the 13-file sha256 pass are checked only in the job.
- CPU tests used transformers 5.12.1 with torch 2.11.0+cpu and torchvision 0.26.0+cpu; the job has the same transformers
  and torchvision versions in cu129 builds.
- The guard covers the three torch entry points only. A library that calls the driver directly (triton, a C extension)
  is not covered; the forward still runs in a fresh interpreter, which is.
- With the guard, code inside admit sees is_available() False even if the driver was queried unmasked earlier in the
  process (the witness import does that). That is the mask's intent, and it differs from an unguarded process.
- 173964's cause is inferred from the same code path, not from its own q0.json (X/o/173964 holds only j2.log and j2.err).
- One Orchard ssh call timed out at 09:45Z (banner exchange); the single retry two minutes later succeeded.
- /project/community had 11 GiB free at about 09:41Z (floor 8 GiB).
- fix3/ on trinity-3-30 holds about 45 MB of reading copies (rd/, ship*.tar, pkt/), over the 5 MB asked; listed in
  tree_rebuild27/REMOVAL_CANDIDATES.md together with the test folders on 1-18 (W27/t1, t3b, t3c, vt, ovl, ovl2). The kit tar exists only on trinity-1-18 so far: the mirror to a second node is owed by the lane.
