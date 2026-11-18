from pathlib import Path
import json, hashlib
L=Path(__file__).resolve().parent
B=L/'work/n1fix2'
B.mkdir(exist_ok=True)
(L/'work/tmp').mkdir(exist_ok=True)
old='/scratch/jjyeung/orch_n30/tree_rebuild_w'
def local(s):
    for prefix in (old+'/w9g',old+'/w9f','/scratch/jjyeung/orch_n30/tree_rebuild',old):
        # Protect the replacement from subsequent shorter-prefix replacements.
        s=s.replace(prefix,'@@LOCAL@@')
    return s.replace('@@LOCAL@@',str(L)).replace('work/n1fix/','work/n1fix2/').replace("work/n1fix'","work/n1fix2'")
files=[]
for p in (L/'work/n1fix').iterdir():
    if p.is_file() and p.suffix in ('.py','.sh','.json'):
        target=B/p.name
        target.write_text(local(p.read_text()))
        files.append(dict(file=p.name,source_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
for folder in ('inputs','inherited'):
    for p in (L/'work/n1fix'/folder).rglob('*'):
        if p.is_file() and not p.is_symlink():
            target=B/p.relative_to(L/'work/n1fix');target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(p.read_bytes())
(B/'HARNESS_COPY.json').write_text(json.dumps(files,indent=2))
(B/'STATUS.md').write_text('Build n1fix2 is in progress. Host is trinity-1-3. Prior STATUS.md and DECISIONS.md are absent from the supplied package. The copied harness is local; individual entry points require path review before execution.\n')
(B/'DECISIONS.md').write_text('''# Build decisions

The sealed producer excludes preparation from its export config hash. Options: change the sealed export format, or retain its hash for export authentication and add a preparation-inclusive continuation identity. Default: retain the sealed format and bind the preparation through checkpoint complete.json and its embedded binding. The checkpoint receipt is a required pinned input; production P bytes remain unavailable.

N identity excludes its own derived identity fields, handover mapping, and host/review attestations to avoid circular hashes. All remaining config fields and authenticated stream receipt database hashes define the target. Mapping values cannot replace them.

The host script requires Python 3.12 or newer, stated in its kit and checked before using modern pathlib/tarfile APIs. This build does not stage an interpreter or launch a job.
''')
print(json.dumps(dict(harness_files=len(files),workspace=str(L))))
