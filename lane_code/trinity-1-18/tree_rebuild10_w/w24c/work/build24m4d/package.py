from common import *
import io,tarfile,lzma,datetime

def growth():
    known=J.load(D/"DISK_BASELINE.json");seen=set();total=0
    for root,dirs,files in os.walk(L):
        dirs[:]=[n for n in dirs if not Path(root,n).is_symlink()]
        for name in dirs+files:
            st=Path(root,name).lstat();key=str(st.st_dev)+":"+str(st.st_ino)
            if key not in seen:total+=max(0,st.st_blocks-known.get(key,0))*512;seen.add(key)
    return total
iv=J.load(D/"INVARIANTS.json");validation=J.load(D/"VALIDATION.json");assert validation["status"]=="PASS"
base=J.load(L/"out/DELIVERY_24M4C.json");assert J.sha(L/base["package"])==base["sha256"]
# Verify the base delivery files against its own manifest, resolving changed kits
# to the retained originals. The external delivery contains final archive facts.
base_manifest=J.load(L/"work/build24m4c/PACKAGE_MANIFEST.json")["files"]
verified=0
for rel,entry in base_manifest.items():
    p=L/rel
    if rel in iv["preserved_originals"]:p=L/iv["preserved_originals"][rel]
    assert p.is_file() and J.sha(p)==entry["sha256"] and p.stat().st_mode&511==int(entry["mode"],8),(rel,str(p))
    verified+=1
J.write(D/"BASE_PRESERVATION.json",dict(status="PASS",base_package_sha256=base["sha256"],manifest_files_verified=verified,all_superseded_kit_bytes_and_modes_retained=True))
selected={}
def add(p):
    p=Path(p)
    if p.is_file() and not p.is_symlink():selected[str(p.relative_to(L))]=p
for root in (T,D,*(kit(n) for n in ("q","n","n_go","qd"))):
    for p in root.rglob("*"):
        if root==D and ("tmp" in p.relative_to(D).parts or p.name in ("PACKAGE_MANIFEST.json","PACKAGE_CHECK.json","STORAGE_FINAL.json","package.log")):continue
        if root==D and p.relative_to(D).parts[0] in ("vqa","vqa_verified","vqa_coverage","vqa_final","arming"):continue
        if root==D and p.name in ("vqa_tests.log","vqa_verified.log","vqa_coverage.log","vqa_final.log","arm_tests.log","arm_missing_test.log","scans.log","finalize.log"):continue
        add(p)
for rel in ("UPLOADS_24M4D.json","UPLOADS_24M4D.list","UPLOADS_24M4D_GO.json","N_CARD_KIT_ROWS_24M4D.md","BUILD24M4D_REPORT.md","ARM_ROUTING_USAGE.md","arm_routing.py","DELIVERY_24M4C.json","BUILD24M4C_REPORT.md","UPLOADS_24M3.json","TREE_SEAL.json","TREE_FILES.sha256","jd.sh","dbb2.py","bind_protected.py"):
    add(L/"out"/rel)
for rel in ("work/build24m3/BASELINE.json","work/build24m4c/TREE24L4_SEAL.json","work/build24m4c/UNCHANGED24L4.json","work/build24m4c/VALIDATION.json","work/build24m4c/PACKAGE_MANIFEST.json"):
    add(L/rel)
# Preserve failing-before replay sources in the deliverable without copying trees.
for n in ("q","n","n_go","qd"):add(L/"attic/build24m4d"/kit(n).relative_to(L)/"b/rv.py")
files={n:(p.read_bytes(),p.stat().st_mode&511) for n,p in sorted(selected.items())}
manifest={n:dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),mode=format(mode,"04o")) for n,(raw,mode) in files.items()}
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
target=L/"out"/("tree_rebuild_b24m4d_"+seal[:8]+".tar")
assert not target.exists()
up=J.load(L/"out/UPLOADS_24M4D.json")
inner=dict(schema="build24m4d-delivery-v1",status="PASS",package=str(target.relative_to(L)),package_seal=seal,
    tree_sha256=iv["tree_sha256"],tree_files=iv["tree_files"],kits=iv["kits"],
    base=dict(build="24m4c",package=base["package"],sha256=base["sha256"]),
    uploaded_diff_base="24m3: UPLOADS_24M3.json applied on top of 24m2d",uploaded=False,launched=False,
    uploads=dict(manifest="out/UPLOADS_24M4D.json",list="out/UPLOADS_24M4D.list",GO_manifest="out/UPLOADS_24M4D_GO.json",stream_root=up["stream_root"],files=up["total_files"],bytes=up["total_bytes"]),
    fixes=dict(vqa="rv.py delegates to the unchanged native census classifier; authentic tiered Binding path when twins enabled, strict Rooms otherwise; unresolved and pin-authentication errors refuse",
               arming="Reviewed selection plus db_bytes.json bind authenticated selection/database staging entries; q/n/n_go copies resealed and scanned; DB listed as already staged and excluded from upload bytes",
               permissions="Non-executable kit files are 0644; executable modes preserved"),
    checks="PASS",validation="work/build24m4d/VALIDATION.json",fixture_boundaries=validation["fixture_boundaries"],inherited_only=validation["inherited_only"],
    unchanged=iv["unchanged"],GO=False,GO_template="out/kit_n_go",GO_template_upload_authorized=False,armed_copies_GO=False,
    production_admission="NOT_RUN",production_database_and_runtime_catalog_availability="NOT_VERIFIED",
    no_deletions=True,original_packages_unchanged=True,original_kit_bytes_and_modes_preserved=True,disk_cap_bytes=150000000,
    archive_compression="xz; tar auto-detects compression despite .tar suffix",
    archive_hash_record="External DELIVERY_24M4D.json adds archive SHA256, byte count and verified member count; embedded delivery precedes archive hashing")
record=dict(schema="build24m4d-manifest-v1",package_seal=seal,files=manifest,seal_domain="files only; package manifest and delivery excluded")
files["work/build24m4d/PACKAGE_MANIFEST.json"]=((json.dumps(record,sort_keys=True,indent=2)+"\n").encode(),0o644)
files["out/DELIVERY_24M4D.json"]=((json.dumps(inner,sort_keys=True,indent=2)+"\n").encode(),0o644)
buffer=io.BytesIO();seen={};expected={}
with lzma.LZMAFile(buffer,"wb",preset=6) as compressed,tarfile.open(fileobj=compressed,mode="w|") as tar:
    for name,(raw,mode) in sorted(files.items()):
        h=hashlib.sha256(raw).hexdigest();info=tarfile.TarInfo(name);info.mode=mode;key=(h,mode);expected[name]=dict(sha256=h,mode=mode)
        if key in seen:info.type=tarfile.LNKTYPE;info.linkname=seen[key];tar.addfile(info)
        else:seen[key]=name;info.size=len(raw);tar.addfile(info,io.BytesIO(raw))
packed=buffer.getvalue();before=growth();assert before+len(packed)+2_000_000<150000000,(before,len(packed))
with tarfile.open(fileobj=io.BytesIO(packed)) as tar:
    actual={m.name:dict(sha256=hashlib.sha256(tar.extractfile(m).read()).hexdigest(),mode=m.mode) for m in tar}
assert actual==expected
for name,h in iv["kits"].items():assert J.seal(kit(name))==h
with target.open("xb") as f:f.write(packed)
J.write(D/"PACKAGE_MANIFEST.json",record)
storage=dict(new_allocated_bytes=growth(),conservative_upper_bound_bytes=growth()+2_000_000,cap_bytes=150000000,cap_met=True,transient_cap_met=True)
assert storage["conservative_upper_bound_bytes"]<150000000
J.write(D/"STORAGE_FINAL.json",storage)
delivery=dict(inner,sha256=hashlib.sha256(packed).hexdigest(),bytes=len(packed),verified_members=len(expected),storage=storage,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
J.write(L/"out/DELIVERY_24M4D.json",delivery)
J.write(D/"PACKAGE_CHECK.json",dict(status="PASS",members=len(expected),all_member_bytes_and_modes_verified=True,delivery_embedded=True,sha256=delivery["sha256"],bytes=len(packed),kit_seals=iv["kits"]))
print(json.dumps(dict(package=delivery["package"],sha256=delivery["sha256"],bytes=len(packed),members=len(expected),storage=storage),indent=2),flush=True)
