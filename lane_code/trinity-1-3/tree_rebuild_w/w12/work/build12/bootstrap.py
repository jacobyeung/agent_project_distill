from pathlib import Path
import difflib, hashlib, json, re

L=Path(__file__).resolve().parents[2]
N=L.parent
B=L/'work/build12'
B.mkdir(parents=True,exist_ok=True)
(L/'work/tmp').mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
def localize(s):
    s=re.sub(r'/scratch/jjyeung/orch_n30/tree_rebuild_w/(?:wn2_w/w9f|wn2_w|w9f|w9g|w10|wm|wn2|wn3)(?=/|[\x27\x22\s])',str(L),s)
    s=re.sub(r'/scratch/jjyeung/orch_n30/tree_rebuild(?=/|[\x27\x22\s])',str(L),s)
    return s
for p in (L/'work/merge11').iterdir():
    if p.is_file() and p.suffix in ('.py','.sh') and p.name!='bootstrap.py':
        (B/p.name).write_text(localize(p.read_text()).replace('work/merge11','work/build12'))
for folder in ('n1fix2','build10'):
    for p in (L/'work'/folder).rglob('*'):
        if p.is_file() and p.suffix in ('.py','.sh') and not set(p.parts)&{'kits','proofs'}:
            p.write_text(localize(p.read_text()).replace('work/merge11','work/build12'))
for name in ('STATUS.md','DECISIONS.md','MERGE_TABLE.json'):
    source=N/'wm/work/merge11'/name
    (B/('BUILD11_'+name)).write_bytes(source.read_bytes())
rows=[]
for name in ('student_pilot/carrier_c1_run.py','student_pilot/r1_handover.py',
             'student_pilot/row_text_audit.py','tests/test_r2_n1fix.py','tests/test_r2_n1fix3.py'):
    old=N/'wn2/work/tree_r1'/name;new=N/'wn3/work/tree_r1'/name;target=L/'work/tree_r1'/name
    row=dict(file=name,n1fix2=sha(old),n1fix3=sha(new),build11=sha(target))
    if name.endswith('carrier_c1_run.py'):
        before=old.read_text().splitlines(True);after=new.read_text().splitlines(True)
        text=target.read_text()
        for tag,a,b,c,d in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
            if tag=='equal':continue
            # Match surrounding unchanged context, preserving all build-11 hunks.
            left=''.join(before[max(0,a-3):a]);right=''.join(before[b:b+3])
            needle=left+''.join(before[a:b])+right
            assert text.count(needle)==1,(name,a,b)
            text=text.replace(needle,left+''.join(after[c:d])+right,1)
        target.write_text(text)
        row['resolution']='Apply each n1fix3 hunk with unique unchanged context; retain all build-11 hunks.'
    elif row['n1fix2']!=row['n1fix3']:
        assert row['build11']==row['n1fix2'] or name.startswith('tests/'),name
        target.write_text(localize(new.read_text()))
        row['resolution']='Take n1fix3 bytes; localize test workspace paths.'
    row['merged']=sha(target);rows.append(row)
(B/'MERGE12.json').write_text(json.dumps(rows,indent=2)+'\n')
# The safe runner and proof helpers are copied, not executed from other workspaces.
for name in ('mutations.py','proof_mutation9.py','proof_mutation_extra.py'):
    src=N/'wn3/work/n1fix3'/name
    if src.exists():(B/('n1_'+name)).write_text(localize(src.read_text()).replace('work/n1fix3','work/build12'))
(B/'DECISIONS.md').write_text('''# Build 12 decisions

- Missing packaged merge records: read the named records from the read-only build-11 workspace and preserve copies here.
- Handover config comparison: default-deny all differences except the explicit mapping, output, initialization-artifact transition and input-attestation keys documented with the implementation. Unknown keys refuse.
- P topology: reconstruct a meta-device model from P configuration and pinned model metadata, then use the native base parameter-group builder. No production weights are copied.
- Legacy evaluation: bind absent fixed buffers only after matching the export config identity to the evaluation config, including heading_plane_min; validate every present buffer against its code constant.
- Text normalization: try ASCII-only authored think text, retaining it only if all original bounded-slice verdicts are unchanged; otherwise keep expanded character mappings and disclose the residual class.
- The EAT-1 observer cannot detect a buffer that changes and is restored between its observations. Record this limit; do not claim continuous integrity.
- GO=false. FRAME64_ALL_READERS_UNQUALIFIED and real P/GPU qualification remain blockers.
''')
(B/'STATUS.md').write_text('# Build 12 status\n\nGO=false. Source merge is staged; targeted proofs and review fixes remain. MERGE12.json records input hashes and resolutions.\n')
print(json.dumps(rows,indent=2))
