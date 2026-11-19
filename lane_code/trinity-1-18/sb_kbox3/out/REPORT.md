K1 box-ladder pricing is BLOCKED because the registered A0 geometry differs from R1 serving.
The convert guard refuses 12 registered training rows in two captures; the serving reader answers 11 of those rows.
The table-reference mismatch is independently explained by S4 scale plus G1 gravity. It is not an adapter feature bug.

| Geometry replay against original table | Matched / choices | Agreement | >=95% |
|---|---:|---:|---|
| GD reviewed convert | 132/149 | 88.59% | FAIL |
| Original table S4/G1 | 149/149 | 100.00% | PASS |
| R1 serving rule on cached own outputs | 137/149 | 91.95% | FAIL |

| Dataset | Captures | Choices | GD matches | Table matches |
|---|---:|---:|---:|---:|
| arkitscenes | 15 | 39 | 36 | 39 |
| scannet | 15 | 40 | 36 | 40 |
| scannetpp | 15 | 70 | 60 | 70 |

The sample was fixed before replay: the first 15 canonical-sorted eligible train captures per dataset, all registered operand names with table inputs.
Table exports match their recorded hashes for 45/45 captures; exact features and candidate sets match for 149/149 objects.
The convert and serving median scales match on all 240 available training exports. The two missing exports are explicit gravity refusals.
Requiring matching IDs and member frames gives GD 127/149 and table geometry 149/149.
On available sample exports, R1 and GD choose the same IDs and member frames on 142/142 operands.
The table producer uses S4 from SCALES_S4.json, not an own-depth scale or another convert run.
The serving reader removes an up-axis rejection that the spec’s reviewed loader retains. This changes accepted inputs and answers.
Serving-rule replay uses stored cp2 checkpoint own tensors; a fresh serving prefill was not run.

| Decision bar | Verdict |
|---|---|
| replace_box | MISSING |
| fused_path | MISSING |
| merge_safe | MISSING |
| selector_worth | MISSING |
| selector_adopt | MISSING |
| size_screen | MISSING |
| first_seen_screen | MISSING |
| tower_challenger | MISSING |

No variant is frozen. Full train pricing, selector retraining, cross-fitting, bootstrap contrasts, and held-out evaluation are MISSING.
PER_ITEM.jsonl, LADDER_TRAIN.txt, and LADDER_HELDOUT_once.txt were not produced; OUTPUT_STATUS.json records their expected paths.
DECISION.json records the blocker and every missing bar. DRYRUN.json records the expanded replay and serving checks.
No reference rebuild ran: the task requires a BLOCKER when GD differs from serving. Relabelling under GD would preserve the wrong A0 contract.

Commands and evidence:

- bash run.sh debug_geometry.py > out/box_ladder/replay_expanded.log 2>&1 — replay counts, features, geometry hashes, scales, TV membership.
- bash run.sh audit_serving_scale.py > out/box_ladder/serving_scale_audit.log 2>&1 — full training scale audit.
- bash run.sh audit_guard.py > out/box_ladder/serving_guard_audit.log 2>&1 — acceptance and answers on both refused captures.
- bash run.sh audit_sources.py > out/box_ladder/source_audit.log 2>&1 — source identity.
- bash run.sh finalize_debug.py — report, decisions, provenance, local archive, and SHA256.

The replay’s R1 reader copies and checked dependencies match R1_A4_SRC_SHA256.txt. SOURCE_AUDIT.json lists every check.
Inherited vendor/stage1.py and vendor/grounding.py differ from R1 and were not used as the replay reader; auxiliary harness files lack R1 manifest entries.
The table geometry function is AST-loaded unchanged with a capture-scoped loader binding. Refused GD exports remain refusals.
The dry run did not execute the full v2 all-arm parity suite because A0 serving equivalence failed.
Replay elapsed 229.531 seconds; peak RSS 635.320 MiB (reported by debug_geometry.py).
All executed Python jobs used p1cpu, nice 10, at most eight numerical threads, and a virtual-memory limit below 40 GB.
No GPU, network, SSH, Git, tmux, process termination, deletion, or external write ran. No held-out capture was evaluated.
The spec was copied once from its named NFS path; remaining task inputs were read from local scratch.
The requested local archive is out/sb_kbox3.tar; its checksum is out/sb_kbox3.tar.sha256. Network transfer is prohibited by the task.
No borderline revision-history prose was kept. Internal diagnostic identifiers are retained because the user explicitly requested a root-cause report.
