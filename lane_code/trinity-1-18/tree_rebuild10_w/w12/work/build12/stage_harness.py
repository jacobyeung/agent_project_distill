from pathlib import Path
import json, re, hashlib
L=Path(__file__).resolve().parents[2];N=L.parent; B=L/'work/build12'
def rewrite(s):
    for old in (str(N/'w10'),str(N/'wn2'),str(N/'w9f'),str(N/'w9g'),str(N/'wn2_w/w9f'),str(N/'wn2_w'),'/scratch/jjyeung/orch_n30/tree_rebuild_w/w12'):
        s=re.sub(re.escape(old)+r'(?=/|[\x27\x22\s])',str(L),s)
    s=re.sub(re.escape(str(N))+r'(?=/|[\x27\x22\s])',str(L),s)
    return s
records=[]
src=N/'w10/work/build10'; dst=L/'work/build10';dst.mkdir(exist_ok=True)
for p in src.iterdir():
    if p.is_file() and p.suffix in ('.py','.sh','.json','.md'):
        q=dst/p.name;q.write_text(rewrite(p.read_text()));records.append(str(q.relative_to(L)))
for sub in ('eat1','eat1_clean','b04_stage'):
    if not (src/sub).is_dir():continue
    for p in (src/sub).rglob('*'):
        if p.is_file() and p.suffix in ('.py','.json','.md','.txt','.sh','.toml'):
            q=dst/p.relative_to(src);q.parent.mkdir(parents=True,exist_ok=True);q.write_text(rewrite(p.read_text()));records.append(str(q.relative_to(L)))
for root in (L/'work/n1fix2', dst):
    for p in root.iterdir():
        if p.is_file() and p.suffix in ('.py','.sh'):
            p.write_text(rewrite(p.read_text()))
(B/'HARNESS_PATHS.json').write_text(json.dumps(records,indent=2)+'\n')
(B/'MERGE_TABLE.json').write_text(json.dumps([dict(file='student_pilot/carrier_c1_run.py',n1fix2='R0 reservation also applies to vehicle N rows',build10='Heading threshold initialization, readout export and evaluation config match',resolution='Retain N R0 reservation and insert all three disjoint build10 hunks; training init unchanged')],indent=2)+'\n')
(B/'STATUS.md').write_text('# Build 11 status\n\nSteps 1 and 2 complete. The sole shared file combines all disjoint changes. CHANGESETS.json and MERGE_TABLE.json bind the merge. Harness copies are localized; proof preparation is in progress. GO=false.\n')
print(json.dumps(dict(staged=len(records))))
