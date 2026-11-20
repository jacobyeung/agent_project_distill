from pathlib import Path
import sys,json,re,hashlib
L=Path.cwd();D=L/"work/build24m4w"
sys.path[:0]=[str(L/"work/tree_r1c"),str(L/"out/kit_qd/b")]
import z
from launch_r1.build import verify
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest

def write(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+"\n")
planned=z.load(D/"PLANNED_SUITES.json");runs=z.load(D/"RUNS.json");assert [r["name"] for r in runs]==planned
all_runs=runs+z.load(D/"FIXED_RUNS.json")
if (D/"EXTRA_RUNS.json").exists():all_runs+=z.load(D/"EXTRA_RUNS.json")
latest={r["name"]:r for r in all_runs};assert all(v["returncode"]==0 for v in latest.values()),{n:v for n,v in latest.items() if v["returncode"]}
for v in latest.values():
 p=L/v["log"];v["sha256"]=z.sha(p);v["status"]="PASS"
 counts=re.findall(r"Ran (\d+) tests?",p.read_text());
 if counts:v["unittest_count"]=sum(map(int,counts))
failures=[dict(r,output=(L/r["log"]).read_text(),resolved_by=latest[r["name"]]["log"],classification="Test fixture setup; candidate source unchanged") for r in all_runs if r["returncode"]]
write(D/"FAILURES.json",dict(failures=failures,inspection_failures=[dict(command="locate_records.py",output="json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)",cause="k/j.json is an encoded shell capsule, not JSON",resolution="Inspected only required fixture declarations; copied exact files from the paths named by the supplied runner")],killed_processes=[],unresolved_test_failures=[]))
seals=z.load(D/"SEALS_FINAL.json");inv=inventory(L/"work/tree_r1c");tree=digest(inv);assert tree==seals["tree"]
paths=dict(q="work/build24/kits/q",n="work/build24/kits/n",n_go="out/kit_n_go",qd="out/kit_qd")
assert {n:verify(L/p) for n,p in paths.items()}==seals["kits"]
checks={}
for n in ("TREE_TESTS.json","REAL_TESTS.json","REAL_DIFFERENTIAL.json","CARD_NUMBERS.json","CARD_SAMPLE_TEST.json","MODE_B_TESTS.json","PUBLICATION_REPLAY.json","DELTA_REPLAY.json","PUBLICATION_INTEGRATION.json","BIND_TESTS.json","REAL_PATH_TESTS.json","INPUT_AUDIT.json","TREE_PATCH_CHECK.json","U_TESTS.json","RCJ_SCAN.json"):
 v=z.load(D/n);assert v["status"]=="PASS",n;checks[n]=dict(status="PASS",sha256=z.sha(D/n))
assert z.load(D/"TREE_TESTS.json")["tests"]==18
real=z.load(D/"REAL_TESTS.json");assert len(real["scope_checks"]["cases"])==3
chain=real["chain"];assert (chain["rows_checked"],chain["extent_exempted_rows"],chain["extent_still_checked_rows"],chain["refused_rows"])==(80,14,66,0)
card=z.load(D/"CARD_NUMBERS.json");assert (card["exempted_pool_rows"],card["still_checked_rows"],card["exempted_v1_rows"] ,card["distance_rows"] )==(10945,32156,3362,11663)
comparisons=0
for r in z.load(D/"REAL_PATH_TESTS.json")["records"]:
 assert len(r["access"]["compare_calls"])==40 and all(v["result"]=="PASS" for v in r["access"]["compare_calls"])
 assert r["result"]["compare_sha256"]==inv["student_pilot/s1_scene_census.py"]
 comparisons+=40
assert comparisons==80
for n in ("after.log","run.log"):assert "REAL_PATH_PASS" in (D/n).read_text()
for suffix in ("","_GO"):
 up=z.load(L/"out"/("UPLOADS_24M4W"+suffix+".json"));assert not up["over_5MB"]
 assert (L/"out"/("UPLOADS_24M4W"+suffix+".list")).read_text()=="".join(v["name"]+"\n" for v in up["files"])
 for v in up["files"]:
  p=L/v["relative_path"];assert z.sha(p)==v["sha256"] and p.stat().st_size==v["bytes"] and format(p.stat().st_mode&511,"04o")==v["mode"]
up=z.load(L/"out/UPLOADS_24M4W.json");pub=z.load(D/"PUBLICATION_REPLAY.json");assert pub["bytes"]==1317449
job=L.parent/"work/d173754";assert not job.exists(),"173754 arrived; inspect before finalizing"
validation=dict(status="QUALIFIED",checks_status="PASS",tree_sha256=tree,kits=seals["kits"],receipt_sha256=seals["receipt"],suite_groups=len(latest),runs=list(latest.values()),checks=checks,targeted_tree_tests=18,real_row_controls=3,real_chain=chain,native_census_comparisons=comparisons,native_plan_run_fixtures=2,missing_source_cases=28,census_compare_unchanged=True,mode_b_commands_identical=True,mode_b_publication_byte_identical=True,publication_bytes=pub["bytes"],publication_byte_identical_to_24m4u=True,job173754=dict(path=str(job),status="ABSENT",fail_before=None,helper_fixes=[],production_fail_before_after_demonstrated=False),ordinary_upload_files=up["total_files"],ordinary_upload_bytes=up["total_bytes"],optional_upload_files=11,patch_bytes=z.load(D/"TREE_PATCH_CHECK.json")["bytes"],full_N_database_checked=False,uploaded=False,launched=False,GO=False,report_style=dict(skill="no-archaeology",retained_comparison="User explicitly required merge provenance and fail-before evidence"))
write(D/"VALIDATION.json",validation);write(D/"FINAL_SUITE_RUNS.json",list(latest.values()))
s=seals["kits"]
report=[
 "QUALIFIED: merged candidate passes local checks; job 173754 is absent, so production helper findings and fail-before/pass-after evidence are unavailable.",
 "Base seals verified against 24m4u and 24m4v bytes; route-T apply passed without refusal. Tree "+tree+" equals 24m4v; c072905b remains pinned.",
 "Kit q "+s["q"]+"; n "+s["n"]+".",
 "Kit n_go "+s["n_go"]+"; qd "+s["qd"]+". GO=false except n_go.",
 "Merge: rcj/ch.py uses exact 24m4v chain tests, counters and card; rcj/x.py and nd.py retain exact 24m4u helper fixes. ps.py, pc.py, f.json, rcj.sh and P_SAMPLE_I.json retain identical input bytes; no manual conflict existed.",
 "Each kit regenerates k/7.json, k/c0.json, k/a.json, k/c.json, k/n.json, k/p.json, k/t_e047002134f979bd.tar, SHA256SUMS.txt and BUILD.json; MERGE.json lists every path and before/after hash.",
 str(len(latest))+" suite groups pass: kit, scan, naming, resolver, guard, arming, qd, planner, rcj and publication; 18 targeted tree tests, three real-row controls, two native plan/run fixtures and 28 missing-source refusals pass. FINAL_SUITE_RUNS.json records per-suite counts and logs.",
 "Real-row chain: 80 rows, 14 exempted, 66 still checked, zero refusals. Published N keys: 10,945 exemptible and 32,156 still checked; card: 3,362 / 11,663 = 28.8262%. Full N chain remains unmeasured.",
 "Census source bytes remain unchanged; 80 native comparisons pass. Eight launch-command comparisons and mode-b publication bytes match; authentic 173725 publication replay is byte-identical to 24m4u at 1,317,449 bytes.",
 "UPLOADS_24M4W.json/.list replay exactly against the reviewed overlay: 37 files, 10,527,368 bytes; no file exceeds 5 MB. The 11 optional GO files are separate. TREE_PATCH_24M4W.tar is 235,520 bytes: four changed tree files plus SHA256SUMS.txt.",
 "FAILURES.json preserves setup failures and passing reruns; no candidate code fix was needed. INPUT_AUDIT.json verifies inherited members and preserved originals. No upload, launch or production rerun occurred.",
 "The package manifest seals all deliverable bytes; archive verification checks every member byte, mode and link, and the package checksum is written last."
]
assert len(report)<15;(L/"out/BUILD24M4W_REPORT.md").write_text("\n".join(report)+"\n")
print(json.dumps(dict(status="PASS",qualified="job173754 absent",suite_groups=len(latest),unittest_count=sum(v.get("unittest_count",0) for v in latest.values()),tree=tree,uploads=up["total_files"]),indent=2),flush=True)
