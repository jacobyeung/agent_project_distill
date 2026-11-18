from pathlib import Path
import json, hashlib
L=Path(__file__).resolve().parents[2]; B=L/'work/n1fix3'; old=L/'work/n1fix2'
B.mkdir(exist_ok=True); (L/'work/tmp').mkdir(exist_ok=True)
replacements=[('/scratch/jjyeung/orch_n30/tree_rebuild_w/wn2',str(L)),
 ('/scratch/jjyeung/orch_n30/tree_rebuild_w/w9f',str(L)),
 ('/scratch/jjyeung/orch_n30/tree_rebuild_w',str(L)),
 ('/scratch/jjyeung/orch_n30/tree_rebuild',str(L))]
records=[]
for p in old.iterdir():
    if p.is_file() and p.suffix in ('.py','.sh','.json'):
        raw=p.read_text()
        for before,after in replacements:
            raw=raw.replace(before+'/', '@LOCAL@/')
            raw=raw.replace("'"+before+"'", "'@LOCAL@'")
        raw=raw.replace('@LOCAL@',str(L)).replace('work/n1fix2','work/n1fix3')
        raw=raw.replace("L.parent/'w9f'",'L').replace("L.parent/'wn2'",'L')
        raw=raw.replace('tree_rebuild_bn1f2_','tree_rebuild_bn1f3_')
        (B/p.name).write_text(raw)
        records.append(dict(path=p.name,original_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
for folder in ('inputs','inherited'):
    for p in (old/folder).rglob('*'):
        if p.is_file() and not p.is_symlink():
            dest=B/p.relative_to(old);dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(p.read_bytes())
for p in (L/'work/tree_r1').rglob('*'):
    if p.is_file() and not p.is_symlink():
        dest=B/'original'/p.relative_to(L/'work/tree_r1');dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(p.read_bytes())
(B/'HARNESS_ORIGINS.json').write_text(json.dumps(records,indent=2))
(B/'REQUALIFICATION.json').write_text('{"pending":false}\n')
(B/'STATUS.md').write_text('State read. Harness copied; localization and handover implementation are in progress. GO=false.\n')
(B/'DECISIONS.md').write_text('Missing copied status and decisions were read from the named prior workspace. All new work stays here.\n\nThe sealed P export does not authenticate checkpoint preparation. Options: change the producer format, or document the missing trust anchor. Default: preserve the sealed producer and report the required producer-written hash binding; do not claim that an operator pin authenticates itself.\n')
print(json.dumps(dict(harness_files=len(records))))
