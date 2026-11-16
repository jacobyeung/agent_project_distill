"""Refresh the current prelaunch card and append the requested design entry."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build6'
read=lambda name:json.loads((L/name).read_text())
d=read('work/build6/DELIVERY.json');kits=read('work/build6/kits/RESULTS.json')
card=['# Prelaunch card','','**NOT READY; no launch authorization.** CPU qualification and its limits are recorded in `out/BUILD6_REPORT.md`.','',
 'Build A2 to admission first. Use A0 only if A2 does not admit; neither is a control. Select one authenticated init input; `out/INIT_INPUT.json` records the supplied fallback. An unpinned init refuses. The archive layout follows the pin rather than a fixed export folder.','',
 'All fourteen evidence obligations in `out/RECORDS_TO_REGENERATE.md` remain. The selected init rebinds the lineage records; it supplies no missing admission evidence (`work/build6/EVIDENCE_DISPOSITION.md`).','',
 'Keep absolute-distance and camera programs, direct room and other types, recovery rows and unit rows. Room calls remain served. Square-foot room answers are valid direct rows, but the supplied room slice has no square-foot questions (`work/build6/proofs/rows/UNITS.json`).','',
 'The launch requires at least 90% final retention for the unit, recovery, room and distance-program families after legitimate exclusions. Unknown overlap remains a refusal, not an exclusion credit (`work/tree_r1/student_pilot/r2_admission.py`).','',
 'The merged withheld list and all sealed scene exclusions remain in every stream. The binding is `a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5` (`work/tree_r1/student_pilot/r2_dev_merged.json`). Full scene admission and frame joins require real host bytes. Packed-row parity does not qualify those joins (`work/build6/proofs/rows/PARITY.json`).','',
 'The materializer rebuilds sampling indices after frame resolution and refuses orphan facing twins. The whole-leg disk guard reserves native states, exports and retained archive copies. Dense geometry is reconstructed before subsampling (`work/tree_r1/student_pilot/r2_materialize.py`, `work/tree_r1/student_pilot/checkpoint_space.py`, `work/tree_r1/student_pilot/r2_frames.py`).','',
 'Distance and room scores require a breakdown by asked unit, with metres first. Unsupported legacy readers remain closed (`work/tree_r1/student_pilot/r2_units.py`, `work/tree_r1/student_pilot/r2_policy.py`).','',
 f"Package: `{d['path']}`. SHA256: `{d['sha256']}`. Source seal: `{d['tree_seal']}`. Source: `work/build6/DELIVERY.json`.",'',
 '| Kit | Hash | Authorization |','|---|---|---|']
for k in kits:card.append(f"| `{k['kit_path']}` | `{k['kit_sha256']}` | Closed |")
card+=['','Both kits were staged from empty and passed the scanner (`work/build6/kits/RESULTS.json`). The real runtime, selected-export bytes, frame map, bank catalog, vocabulary, full trainer-state recovery and remote persistence remain host obligations (`out/FRAME_HOST_JOB.md`). No launch is authorized.']
(L/'out/PRELAUNCH_CARD.md').write_text('\n'.join(card)+'\n')
record=L/'out/DESIGN_RECORD_tree_rebuild_20261115.md';text=record.read_text()
section='''\n## Build 6

The accepted contract integration preserves exact packet bytes where required and records every merged hunk in `out/CONTRACTS_INTEGRATION.md`. The source inventory, seal and delivery identity are in `out/TREE_FILES.sha256`, `out/TREE_SEAL.json` and `work/build6/DELIVERY.json`.

The route table retains distance and camera programs, direct room and other types, recovery and unit rows. The init is a pinned launch input. A2 receives admission priority; A0 is its fallback. Both authorizations remain closed.

The final family gate requires 90% retention after legitimate exclusions (`work/tree_r1/student_pilot/r2_admission.py`). Direct square-foot and inch answer units are accepted; room traces remain qualitative. Room calls stay served, and metric reports require asked-unit breakdowns with metres first (`work/tree_r1/tests/test_r2_build6.py`).

Suite outcomes, unchanged-pass checks, changed-statement coverage, bounded row parity, unit conversion evidence and unchecked host inputs are recorded in `out/BUILD6_REPORT.md`. All evidence obligations in `out/RECORDS_TO_REGENERATE.md` remain; the chosen init rebinds the lineage records without fabricating evidence.
'''
if '\n## Build 6\n' in text:text=text.split('\n## Build 6\n',1)[0]
record.write_text(text.rstrip()+'\n'+section)
