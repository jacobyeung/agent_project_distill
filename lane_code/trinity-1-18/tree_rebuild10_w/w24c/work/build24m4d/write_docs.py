from common import *
import ast
iv=J.load(D/"INVARIANTS.json");seals=iv["kits"];up=J.load(L/"out/UPLOADS_24M4D.json")
checks={}
for name in ("VQA_TESTS.json","ARM_TESTS.json","ARM_MISSING_DB_TEST.json","ARM_NEGATIVES.json","UPLOAD_RECONSTRUCTION.json","INVARIANTS.json","CHANGED_STATEMENT_COVERAGE.json","REVIEW_TESTS.json","KIT_TESTS.json","NAMING_TESTS.json"):
    v=J.load(D/name);assert v.get("status")=="PASS" or v.get("successful") is True
    checks[name]=dict(path=str((D/name).relative_to(L)),sha256=J.sha(D/name),status="PASS")
assert all(r["returncode"]==0 for r in J.load(D/"REGRESSIONS.json"))
for n in ("q","n","n_go","qd"):
    v=J.load(D/("SCAN_"+n+".json"));assert v["status"]=="PASS" and v["kit_seal"]==seals[n]
    checks["SCAN_"+n+".json"]=dict(path=str((D/("SCAN_"+n+".json")).relative_to(L)),sha256=J.sha(D/("SCAN_"+n+".json")),status="PASS")
for n in ("q","n"):
    for filename in ("GUARD_TESTS.json","LEGACY_GUARD_TESTS.json"):
        p=D/("guard_"+n)/filename;v=J.load(p);assert v["successful"]
        checks[str(p.relative_to(D))]=dict(path=str(p.relative_to(L)),sha256=J.sha(p),status="PASS")
J.write(D/"VALIDATION.json",dict(status="PASS",checks=checks,
    fresh_suites=["Exact production VQA replay and native room resolution across four kits","Real arming plus complete native q planner on SQLite fixture for q/n/n_go","Missing DB inventory and wrong hash/size refusals","All four decoded scans plus three armed scans","Kit, naming, four guard suites and review wait/refusal suite"],
    inherited_only=["24m4c resolver, live-export, full census and hidden-path results; their code is byte-identical"],
    fixture_boundaries=[J.load(D/"VQA_TESTS.json")["scope"],J.load(D/"ARM_TESTS.json")["scope"],"Review shell uses synthetic prepared stores/host receipt and stops at t.py boundary; guard GPU queries are stubs"],
    production_admission="NOT_RUN",orchard_access=False,tree_changed=False))
card=f"""Vehicle N uses MINIMAL on tree C {iv["tree_sha256"]} ({iv["tree_files"]} files; work/build24m4d/INVARIANTS.json).
Kit q: {seals["q"]}; kit n: {seals["n"]}.
Kit n_go: {seals["n_go"]}; kit qd: {seals["qd"]}.
GO is false except in out/kit_n_go; that template is not uploaded. Routing arming produces GO=false review copies.
UPLOADS_24M4D.json/.list contain {up["total_files"]} files and {up["total_bytes"]} bytes, diffed against 24m3: UPLOADS_24M3.json applied on top of 24m2d. The stream root is {up["stream_root"]}.
UPLOADS_24M4D_GO.json is the separate, unuploaded three-file delta for its recorded n seal. The discovery wrapper and dbb2.py already match the 24m3 base.
All non-executable kit files have mode 0644; executable modes are preserved. INVARIANTS.json records bytes, modes and retained originals.
rv.py uses the census classifier’s native stream room authority, including direction_twins Binding.room for unresolved VQA rows when enabled; without twins it uses strict Rooms. Unknown rooms still refuse.
The exact replay line resolves to scannetpp/151178afd7 and passes clean evidence; protected VQA and unresolved rows refuse in q, n, n_go and qd (VQA_TESTS.json).
The census, admission, removals and protected-room policy are unchanged. Tree C binds the pointing list d21e374f as a constant before NAMING_REMOVE; extra role lists still require an authorized tree delta.
The pinned initialization, opener rows, step-544 lineage, resolver identity checks, two NOT_PRESENT slots and seven DEFERRED slots are unchanged. The stop checkpoint order in b/pc.py is byte-identical.
Native in-job producers regenerate room, scene, pool, target and preparation receipts. live/c4.json binds census identity, store/source pins, counts and protected-key hashes; h.py and rv.py authenticate that publication.
The reviewer receives live/v.json, identity.txt, e0-e3.json stream evidence, e4-e5.json room-audit evidence, e6-e7.json protected lists and WAITING_REVIEW.json before the identity-bound review wait.
arm_routing.py takes the reviewed selection and db_bytes.json, checks the selected base’s database, and binds both staged pins. The DB is listed at Orchard u/<sha> and excluded from the upload delta; ARM_ROUTING_USAGE.md gives the exact command and outputs.
Armed q, n and n_go pass decoded scans and authenticated DB inventory checks. The actual mode-q planner returns a DB staging entry on the SQLite fixture and rejects missing staging, wrong bytes or wrong size (ARM_TESTS.json; ARM_MISSING_DB_TEST.json).
The runtime catalog eac5f9f0 remains a required authenticated input and refuses by name if unavailable. Production DB availability, preparation and admission were not exercised; VALIDATION.json states the fixture boundaries.
"""
(L/"out/N_CARD_KIT_ROWS_24M4D.md").write_text(card)
report=f"""Tree {iv["tree_sha256"]}; q {seals["q"]}; n {seals["n"]}; n_go {seals["n_go"]}; qd {seals["qd"]}.
MUST 1 passes: the exact VQA replay is clean, protected/unresolved rows refuse in all four kits, and strict lookup remains active without twins (work/build24m4d/VQA_TESTS.json).
MUST 2 passes: arm_routing.py binds the selection and DB hash/size, reseals q/n/n_go copies, rescans and checks staging closure; DB bytes stay outside the upload delta (out/ARM_ROUTING_USAGE.md).
The real mode-q planner returns the authenticated DB member on the SQLite fixture; missing inventory, wrong hash/size and invalid metadata refuse (work/build24m4d/ARM_TESTS.json; ARM_MISSING_DB_TEST.json).
All non-executable kit files are 0644; executable modes and every original byte/mode are preserved in place or attic (work/build24m4d/INVARIANTS.json).
Tree C, census semantics, admission, legality, removals, opener rows, lineage, resolver identity checks, DEFERRED boundary and b/pc.py stop order are unchanged (INVARIANTS.json).
Four decoded scans, three armed scans, kit/naming/guard checks and review-wait/refusal tests pass; changed rv.py statements are covered (work/build24m4d/VALIDATION.json).
UPLOADS_24M4D.json/.list contain {up["total_files"]} files ({up["total_bytes"]} bytes), against 24m3: UPLOADS_24M3.json applied on top of 24m2d. The GO delta is separate and not uploaded.
GO remains false except in out/kit_n_go; arming copies remain false. No upload, launch or production admission ran; remote DB/runtime catalog availability is unverified.
Fixture scope, input hashes and inherited-only checks appear in VALIDATION.json; package integrity and disk allocation appear in DELIVERY_24M4D.json.
"""
assert len(report.splitlines())<15
(L/"out/BUILD24M4D_REPORT.md").write_text(report)
print("Validation and requested documents written",flush=True)
