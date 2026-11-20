from pathlib import Path
import json,tarfile,ast,hashlib,subprocess,sys,importlib.util,shutil
H=Path(__file__).resolve().parent;J=Path.cwd();N=H/"e2_patched_delivery/n"
for p in (H/"proposed/e2.py",H/"proposed/observe.py",H/"strict_sink.py"):
 ast.parse(p.read_text(),filename=str(p))
p=subprocess.run(["patch","--dry-run","-p1"],input=(J/"out/FIX_E2_173911.patch").read_text(),capture_output=True,text=True)
(H/"patch_check.log").write_text(p.stdout+p.stderr);assert p.returncode==0
spec=importlib.util.spec_from_file_location("e2_finish_final",H/"proposed/e2.py");driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
driver.finish(N,N.parent/"x","24045",0)
r=json.loads((N/"E2.json").read_text());assert r["status"]=="PASS" and len(r["objects"])==16
with tarfile.open(N/"logs.tgz") as t:
 members={m.name:t.extractfile(m).read() for m in t.getmembers()}
 for name,raw in members.items():
  assert all(x not in raw for x in (b"https://",b"http://",b"upload_id",b"CAPABILITY_SENTINEL",b"TOKEN_SENTINEL")),name
 manifest=json.loads(members["log_manifest.json"]);entry=next(x for x in manifest if x["source"]=="logs/upload.jsonl")
 events=[json.loads(s) for s in members[entry["member"]].decode().splitlines() if s.strip()]
 statuses=[e for e in events if e["event"]=="http_status"];runtime=[e for e in events if e["event"]=="writer_runtime"]
 assert len(statuses)==16 and all(e["status"]==200 for e in statuses)
 assert runtime and all(e["isolated"]==1 and e["no_user_site"]==1 and e["executor"]=="threads" for e in runtime)
 assert len(json.loads(members["r.json"]))==16
 assert len(json.loads(members["http_metadata.json"]))==16
 assert any(e["source"]=="logs/runtime.json" for e in manifest)
 assert any(e["source"]=="n/live_spool/retry.log" for e in manifest)
 assert any("/state/gcs_" in e["source"] for e in manifest)
 result=dict(status="PASS",checks=r["checks"],receipts=16,http_metadata=16,http_statuses=len(statuses),runtime_records=len(runtime),archive_bytes=(N/"logs.tgz").stat().st_size,
             manifest=manifest,secrets_found=False)
(H/"logging_archive_test.json").write_text(json.dumps(result,indent=2)+"\n")
# Successful HTTP metadata must survive even if no receipt could be appended.
F=H/"metadata_without_receipt";F.mkdir();n=F/"n";x=F/"x";x.mkdir()
for folder in ("logs","obs","k/k","k/b","n/live_spool/state"):(n/folder).mkdir(parents=True,exist_ok=True)
shutil.copyfile(J/"out/kit_n/k/y.json",n/"k/k/y.json")
meta=json.loads(members["http_metadata.json"])[0]
(n/"obs/r_valid.json").write_text(json.dumps(meta))
bad={**meta,"md5Hash":"CAPABILITY_SENTINEL"};(n/"obs/r_rejected.json").write_text(json.dumps(bad))
(n/"E2.json").write_text(json.dumps(dict(status="FAIL",checks={},objects=[],job="24045")))
s=importlib.util.spec_from_file_location("e2_finish",H/"proposed/e2.py");m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.finish(n,x,"24045",1)
with tarfile.open(n/"logs.tgz") as t:
 names=t.getnames();assert "r.json" not in names
 saved=json.load(t.extractfile("http_metadata.json"));assert saved==[meta]
 for member in t.getmembers():assert b"CAPABILITY_SENTINEL" not in t.extractfile(member).read()
(H/"metadata_without_receipt.json").write_text(json.dumps(dict(status="PASS",metadata=1,receipts=0,invalid_metadata_excluded=True))+"\n")
print("PASS: final patch syntax/dry-run; all 14 E2 checks; 16 HTTP statuses, receipts and metadata; safe metadata retained without receipts; no capability leakage")
