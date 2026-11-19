"""Review package with exact code diffs and a complete member hash manifest."""
from common import *
import difflib,tarfile

def main():
 pins();dry=js(ROOT/'out/DRYRUN.json');checks=js(ROOT/'out/CHECKS.json')
 assert dry['status']=='PASS' and checks['status']=='PASS'
 previous=Path('/scratch/jjyeung/orch_n30/sb_kobj');changes=[]
 for folder in ('code','config','scripts'):
  for p in sorted((ROOT/folder).rglob('*')):
   if not p.is_file() or p.suffix not in ('.py','.sh','.json'):continue
   rel=p.relative_to(ROOT);old=previous/rel
   before=read(old).decode().splitlines() if old.is_file() else [];after=read(p).decode().splitlines()
   spans=[dict(kind=tag,old=[i+1,j],new=[a+1,b]) for tag,i,j,a,b in difflib.SequenceMatcher(a=before,b=after).get_opcodes() if tag!='equal']
   if spans:changes.append(dict(path=str(rel),source_sha256=sha(old) if old.is_file() else None,sha256=sha(p),spans=spans))
 write(ROOT/'out/IMPLEMENTATION_DIFF.json',dict(files=changes,baseline=str(previous)))
 selected=[]
 for folder in ('code','config','scripts','inputs/local','inputs/pack','inputs/rowsets'):
  selected += [p for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix not in ('.pyc',) and '__pycache__' not in p.parts]
 selected += [ROOT/'README.md',ROOT/'STATUS.md',ROOT/'inputs/KIT_SPEC_object_route_r0dev_v2.md']
 selected += [p for p in (ROOT/'out').rglob('*') if p.is_file() and 'inherited_v1' not in p.parts and 'passes' not in p.parts and p.suffix not in ('.tar','.sha256') and p.name not in ('PACKAGE.json','ARCHIVE_MANIFEST.json')]
 selected += [p for p in (ROOT/'work/guard_tests').rglob('*.json')]
 members={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(selected))}
 write(ROOT/'out/ARCHIVE_MANIFEST.json',dict(members=members));selected.append(ROOT/'out/ARCHIVE_MANIFEST.json')
 archive=ROOT/'out/sb_kobj2.tar'
 with tarfile.open(archive,'w') as tar:
  for p in sorted(set(selected)):tar.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
 archive_hash=sha(archive)
 with tarfile.open(archive) as tar:
  for name,h in members.items():assert hashlib.sha256(tar.extractfile(name).read()).hexdigest()==h
 (ROOT/'out/sb_kobj2.tar.sha256').write_text(archive_hash+'  sb_kobj2.tar\n')
 write(ROOT/'out/PACKAGE.json',dict(status='PASS',archive=str(archive),sha256=archive_hash,bytes=archive.stat().st_size,members_verified=len(members),command='nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python code/package_v2.py'))
 print(json.dumps(dict(status='PASS',sha256=archive_hash,bytes=archive.stat().st_size,members_verified=len(members))))
if __name__=='__main__':main()
