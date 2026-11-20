from common import *
import io,tarfile,lzma,datetime
CAP=100_000_000
C=L.parent/"w24c/out/tree_rebuild_b24m4c_b7be125e.tar"
E=L/"out/tree_rebuild_b24m4e_737062d4.tar"
def content(path):
 with tarfile.open(path) as t:
  return {m.name:(t.extractfile(m).read(),m.mode) for m in t}
def record(raw,mode):return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),mode=format(mode,"04o"))
def growth():
 known=J.load(D/"DISK_BASELINE.json");seen=set();total=0
 for root,dirs,names in os.walk(L):
  dirs[:]=[n for n in dirs if n!=".git" and not Path(root,n).is_symlink()]
  for n in dirs+names:
   s=Path(root,n).lstat();k=f"{s.st_dev}:{s.st_ino}"
   if k not in seen:total+=max(0,s.st_blocks-known.get(k,0))*512;seen.add(k)
 return total
iv=J.load(D/"INVARIANTS.json");auth=J.load(D/"REVIEW_AUTH_TESTS.json")
for n in ("ARM_TESTS","REVIEW_AUTH_TESTS","ARM_COVERAGE","ARM_MISSING_DB_TEST","INVARIANTS","RESTORED_MEMBERS"):
 assert J.load(D/(n+".json"))["status"]=="PASS",n
base=J.load(L/"out/DELIVERY_24M4E.json")
validation=dict(status="PASS",tests={n:"work/build24m4f/"+n+".json" for n in ("ARM_TESTS","REVIEW_AUTH_TESTS","ARM_COVERAGE","ARM_MISSING_DB_TEST","INVARIANTS")},
 negative_review_and_retained_checks=len(auth["records"]),
 fixture_boundaries=["Reviewer RESULT files are explicitly synthetic test receipts, not production approvals.","Real apply(), CLI, decoded scanners and native mode-q planner run against a tiny SQLite fixture; unrelated production stores and weights use compact resolved metadata.","No production preparation, admission, training or remote database availability check ran."],
 inherited_only=["24m4e full kit/naming/resolver/guard/hidden-path suites and 24m4d VQA/census/review-wait suites: all four kit byte inventories and modes are unchanged."],
 report_style_exceptions=["Build identifiers and member comparisons remain because the requested delivery contract requires exact package provenance and changed/unchanged seals."])
J.write(D/"VALIDATION.json",validation)
lines=[
 "Tree "+iv["tree_sha256"]+"; "+"; ".join(n+" "+h for n,h in iv["kits"].items())+"; tree and all four kits unchanged; package and external arming helper changed.",
 "Arming requires both reviewed hashes and a RESULT containing both hashes and PASS; regenerated_sha256 must equal the authenticated DB metadata hash (out/arm_routing.py).",
 "Armed q/n/n_go seals and n_go k/c.json decoded-payload/file hashes print on success and enter UPLOADS_ROUTING_ARMED.json; exact command: out/ARM_ROUTING_USAGE.md.",
 "The matching fixture binds; fabricated regenerated hash, altered row count/digest, mismatched reviewed hashes and missing arguments refuse (work/build24m4f/REVIEW_AUTH_TESTS.json; ARM_TESTS.json).",
 "Real CLI output, three armed decoded scans, native mode-q planner closure and missing-DB refusal pass (work/build24m4f/ARM_COVERAGE.json; ARM_TESTS.json; ARM_MISSING_DB_TEST.json).",
 "The package retains every 24m4c member: 195 omitted members restored to package membership, including 190 restored to disk (work/build24m4f/RESTORED_MEMBERS.json; DELIVERY_24M4F.json member_diff_against_24m4c).",
 "arm_routing.py is outside every kit; tree C, rv.py, census, admission, legality, removals, pins and b/pc.py retain their bytes and modes (work/build24m4f/INVARIANTS.json).",
 "All 7179 original files retain their bytes/modes in place or attic; package member hashes and disk growth are verified in DELIVERY_24M4F.json.",
 "No UPLOADS_24M4F files are needed because no source kit changed. Arming tests use synthetic reviews; production admission, training and remote DB bytes were not checked (work/build24m4f/VALIDATION.json).",
 "GO stays false except in the unchanged out/kit_n_go template; no upload or launch ran. Build/member identifiers document the required delivery provenance."
]
assert len(lines)<12
(L/"out/BUILD24M4F_REPORT.md").write_text("\n".join(lines)+"\n")
c=content(C);e=content(E);rawfiles={**c,**e}
# Historical package members retain their archived bytes; only the requested
# helper and usage note replace current 24m4e members.
for rel in ("out/arm_routing.py","out/ARM_ROUTING_USAGE.md","out/BUILD24M4F_REPORT.md"):
 p=L/rel;rawfiles[rel]=(p.read_bytes(),p.stat().st_mode&511)
for p in D.rglob("*"):
 if p.is_file() and p.name not in ("package.log","PACKAGE_MANIFEST.json","PACKAGE_CHECK.json","STORAGE_FINAL.json"):
  rawfiles[str(p.relative_to(L))]=(p.read_bytes(),p.stat().st_mode&511)
for rel in iv["preserved_originals"].values():
 p=L/rel;rawfiles[rel]=(p.read_bytes(),p.stat().st_mode&511)
manifest={n:record(raw,mode) for n,(raw,mode) in sorted(rawfiles.items())}
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
target=L/"out"/("tree_rebuild_b24m4f_"+seal[:8]+".tar")
assert not target.exists()
final_names=set(rawfiles)|{"out/DELIVERY_24M4F.json","work/build24m4f/PACKAGE_MANIFEST.json"}
changed=[];unchanged=[]
for n,(raw,mode) in c.items():
 if rawfiles[n]==(raw,mode):unchanged.append(n)
 else:changed.append(dict(name=n,before=record(raw,mode),after=manifest[n],basis="24m4d/24m4e intentional replacement at the same path"))
assert not set(c)-final_names
assert [n for n in e if e[n]!=rawfiles[n]]==[n for n in e if n in ("out/arm_routing.py","out/ARM_ROUTING_USAGE.md")]
diff=dict(base_package=str(C),base_archive_sha256=J.sha(C),base_member_count=len(c),package_member_count=len(final_names),
 removed=[],removed_count=0,added=sorted(final_names-set(c)),added_count=len(final_names-set(c)),
 changed=changed,changed_count=len(changed),unchanged=sorted(unchanged),unchanged_count=len(unchanged),
 restored_from_24m4c=sorted(set(c)-set(e)),restored_count=len(set(c)-set(e)),
 policy="Union of 24m4c and 24m4e members; 24m4e wins shared paths, then only the requested external helper and usage change. No member removal exceptions.")
inner=dict(schema="build24m4f-delivery-v1",status="PASS",package=str(target.relative_to(L)),package_seal=seal,
 base=dict(build="24m4e",package=base["package"],sha256=J.sha(E),package_seal=base["package_seal"]),
 tree_sha256=iv["tree_sha256"],tree_files=iv["tree_files"],kits=iv["kits"],kit_changes=[],arm_routing_inside_kit=False,
 changed_current_files=["out/arm_routing.py","out/ARM_ROUTING_USAGE.md"],member_diff_against_24m4c=diff,
 review_binding=dict(required_arguments=["--reviewed-selection-sha256","--reviewed-regenerated-sha256","--review-verdict"],
  checks=["Exact selection file SHA256 equals independently reviewed selection hash","Selection regenerated_sha256 equals independently reviewed regenerated hash","RESULT text contains both full hashes and the word PASS","Regenerated hash equals the selected database hash in db_bytes.json","All existing authentication, staging, size and output checks"],
  arming_record="<output>/UPLOADS_ROUTING_ARMED.json",printed_and_recorded=["kits.q","kits.n","kits.n_go","armed_n_go_config.payload_sha256","armed_n_go_config.file_sha256"]),
 checks="PASS",validation="work/build24m4f/VALIDATION.json",fixture_boundaries=validation["fixture_boundaries"],inherited_only=validation["inherited_only"],
 original_files_verified=iv["original_files_verified"],preserved_originals=iv["preserved_originals"],no_deletions=True,
 unchanged=iv["unchanged"],GO=False,GO_template="out/kit_n_go",armed_copies_GO=False,uploaded=False,launched=False,
 production_admission="NOT_RUN",production_body_availability="NOT_VERIFIED",uploads_manifest=None,uploads_reason="No source kit changed; arm_routing.py is outside all kits",disk_cap_bytes=CAP,
 archive_compression="xz; tar auto-detects compression despite .tar suffix",
 archive_hash_record="External delivery adds archive SHA256, byte count, storage and verified member count; embedded delivery precedes archive hashing")
package_record=dict(schema="build24m4f-manifest-v1",package_seal=seal,files=manifest,seal_domain="files only; new package manifest and delivery excluded")
rawfiles["work/build24m4f/PACKAGE_MANIFEST.json"]=((json.dumps(package_record,sort_keys=True,indent=2)+"\n").encode(),0o644)
rawfiles["out/DELIVERY_24M4F.json"]=((json.dumps(inner,sort_keys=True,indent=2)+"\n").encode(),0o644)
buffer=io.BytesIO();seen={};expected={}
with lzma.LZMAFile(buffer,"wb",preset=6) as compressed,tarfile.open(fileobj=compressed,mode="w|") as tar:
 for n,(raw,mode) in sorted(rawfiles.items()):
  h=hashlib.sha256(raw).hexdigest();info=tarfile.TarInfo(n);info.mode=mode;key=(h,mode);expected[n]=dict(sha256=h,mode=mode)
  if key in seen:info.type=tarfile.LNKTYPE;info.linkname=seen[key]
  else:seen[key]=n;info.size=len(raw)
  tar.addfile(info,None if info.islnk() else io.BytesIO(raw))
packed=buffer.getvalue();before=growth();assert before+len(packed)+5_000_000<CAP,(before,len(packed))
with tarfile.open(fileobj=io.BytesIO(packed)) as tar:
 actual={m.name:dict(sha256=hashlib.sha256(tar.extractfile(m).read()).hexdigest(),mode=m.mode) for m in tar}
assert actual==expected
assert not set(c)-set(actual)
with target.open("xb") as f:f.write(packed)
J.write(D/"PACKAGE_MANIFEST.json",package_record)
storage=dict(new_allocated_bytes=growth(),conservative_upper_bound_bytes=growth()+1_000_000,cap_bytes=CAP,cap_met=True,transient_cap_met=True)
assert storage["conservative_upper_bound_bytes"]<CAP
J.write(D/"STORAGE_FINAL.json",storage)
delivery=dict(inner,sha256=hashlib.sha256(packed).hexdigest(),bytes=len(packed),verified_members=len(expected),storage=storage,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
J.write(L/"out/DELIVERY_24M4F.json",delivery)
J.write(D/"PACKAGE_CHECK.json",dict(status="PASS",members=len(expected),all_member_bytes_and_modes_verified=True,delivery_embedded=True,no_24m4c_member_removed=True,sha256=delivery["sha256"],bytes=len(packed),kit_seals=iv["kits"],unique_uncompressed_bytes=sum(len(rawfiles[n][0]) for n in seen.values())))
print(json.dumps(dict(package=delivery["package"],sha256=delivery["sha256"],bytes=len(packed),members=len(expected),restored=diff["restored_count"],changed_vs_24m4c=len(changed),storage=storage),indent=2),flush=True)
