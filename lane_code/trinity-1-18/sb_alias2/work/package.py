"""Package outputs and reproducibility inputs without self-referential digests."""
import hashlib,json,tarfile
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
names=['out/TIERED_ALIAS_MAP.json','out/TIER_CHECKS.json','out/ROOM_AUDIT_TIERED.json','out/ROOM_AUDIT_REPORT.md','work/enumerate_candidates.py','work/audit.py','work/recover_k1.py','work/package.py','work/validate.py','work/finalize_report.py','work/CANDIDATE_SCENES.json','work/CANDIDATE_SCENES_FINAL.json','work/finish_candidates.py','candidate_paths.txt','work/SCAN_MANIFEST.tsv','work/K1_RECOVERY.json','work/TEACHER_K1.raw','work/VALIDATION.json','in/build_a2_other.py','work_inventory.txt']
archive=BASE/'out/sb_alias2.tar'
with tarfile.open(archive,'w') as t:
 for name in names:
  p=BASE/name;info=t.gettarinfo(str(p),arcname=name);info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
  with p.open('rb') as f:t.addfile(info,f)
h=hashlib.sha256()
with archive.open('rb') as f:
 for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
sha=h.hexdigest();(BASE/'out/sb_alias2.tar.sha256').write_text(sha+'  sb_alias2.tar\n')
r=BASE/'out/ROOM_AUDIT_REPORT.md';s=r.read_text();s+='\nArchive SHA256: `'+sha+'` (`out/sb_alias2.tar`). The packaged report omits this digest to avoid self-reference.\n';assert len(s.splitlines())<=80;r.write_text(s)
a=json.loads((BASE/'out/ROOM_AUDIT_TIERED.json').read_text())
(BASE/'STATUS.md').write_text(f"The whole-store audit and validation are complete for all {a['rows']:,} v7 rows: {a['hits']}; {a['unresolved_rows']:,} unresolved rows. The baseline and exact list hashes pass. The report is out/ROOM_AUDIT_REPORT.md. Outputs, input digests, candidate origins and reproducible scripts are packaged in out/sb_alias2.tar (SHA256 {sha}).\n")
print(sha,archive)
