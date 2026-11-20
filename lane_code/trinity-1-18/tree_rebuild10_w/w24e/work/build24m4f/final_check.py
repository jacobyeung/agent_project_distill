from common import *
v=J.load(L/"out/DELIVERY_24M4F.json");assert J.sha(L/v["package"])==v["sha256"]
assert len((L/"out/BUILD24M4F_REPORT.md").read_text().splitlines())<12
assert not (L/"out/UPLOADS_24M4F.json").exists() and not (L/"out/UPLOADS_24M4F.list").exists()
assert v["member_diff_against_24m4c"]["removed"]==[]
original=J.load(D/"ORIGINAL_FILES.json")
for name,s in original.items():
 p=L/v["preserved_originals"].get(name,name);now=p.stat()
 assert (now.st_ino,now.st_dev,now.st_size,now.st_mode&511,now.st_mtime_ns)==(s["inode"],s["device"],s["size"],s["mode"],s["mtime_ns"]),name
known=J.load(D/"DISK_BASELINE.json");seen=set();growth=0
for parent,dirs,names in os.walk(L):
 dirs[:]=[n for n in dirs if n!=".git" and not Path(parent,n).is_symlink()]
 for n in dirs+names:
  s=Path(parent,n).lstat();key=f"{s.st_dev}:{s.st_ino}"
  if key not in seen:growth+=max(0,s.st_blocks-known.get(key,0))*512;seen.add(key)
assert growth+1_000_000<100_000_000
v["storage"].update(new_allocated_bytes=growth,conservative_upper_bound_bytes=growth+1_000_000)
J.write(L/"out/DELIVERY_24M4F.json",v);J.write(D/"STORAGE_FINAL.json",v["storage"])
print(json.dumps(dict(status="PASS",package=v["package"],sha256=v["sha256"],original_files_preserved=len(original),report_lines=len((L/"out/BUILD24M4F_REPORT.md").read_text().splitlines()),new_allocated_bytes=growth)))
