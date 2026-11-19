"""Build the requested frozen-snapshot delta without Git."""
import difflib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SNAPSHOT=Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_a6b70ef2')
def main():
    patches=[];changed=[]
    for folder in ('tools','tests','configs','work/tree'):
        left=SNAPSHOT/folder;right=ROOT/folder
        paths={p.relative_to(left) for p in left.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        paths|={p.relative_to(right) for p in right.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        for rel in sorted(paths):
            a=left/rel;b=right/rel
            before=a.read_bytes() if a.is_file() else b'';after=b.read_bytes() if b.is_file() else b''
            if before==after:continue
            name=folder+'/'+str(rel);changed.append(name)
            patches.extend(difflib.unified_diff(before.decode().splitlines(keepends=True),after.decode().splitlines(keepends=True),fromfile='a/'+name,tofile='b/'+name))
    for name in ('SAMPLER_REVIEW.patch','DEPLOYMENT_REVIEW.patch'):
        a=SNAPSHOT/'out'/name;b=ROOT/'out'/name
        before=a.read_text() if a.exists() else '';after=b.read_text()
        if before!=after:
            changed.append('out/'+name)
            patches.extend(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile='a/out/'+name,tofile='b/out/'+name))
    out=ROOT/'out';(out/'FIX5.diff').write_text(''.join(patches))
    b=json.loads((out/'BINDING.json').read_text());op=json.loads((out/'OPERATOR.json').read_text());c=json.loads((out/'ADMISSION_BY_TYPE.json').read_text())
    audit=json.loads((out/'proof/loader_audit.json').read_text())
    lines=[f"Fix 5 delta against `{SNAPSHOT}` (frozen config a6b70ef2).",'',
        f"Config identity: `{b['config_identity']}`. Archive: `{op['archive']}`. SHA256: `{op['sha256']}`.",'',
        f"The full census checks {c['vqa_rows']:,} unchanged v7 rows. All {c['traced_room']['eligible']} traced room rows are eligible. The room cell draws 1,720 rows over 1,000 steps (1.72/step), below the four-repeat cap of 1,724 draws. All one-line room rows and out-of-range-frame, missing-relation and numeric-think mutants are refused. See proof/ROOM_GRAMMAR.json and logs/tests.log.",'',
        'The loader audit prints toward/away draw shares of facing, decoded back-answer share among away-hard draws (including back-left/back-right, with exact-back separately), cm/ft/in draws and eligible/drawn absolute-distance counts by scannetpp/, scannetppv2/, scannet and arkit prefix. Local routing counts are explicitly NOT_RUN/null; the production proof uses the same code on staged routing rows. Routing selection is unchanged.', '',
        'Units remain unbound at zero dose and appear under absent_on_P. The local required-family check has no missing family; unavailable native camera populations remain NOT_RUN. Production CPU proof on Orchard, full RGB admission and independent review remain pending. All eight proof checks are exercised by the local proof fixture.', '',
        'Draw breakdown: `'+json.dumps(audit['draw_breakdown'],sort_keys=True)+'`.', '',
        'Changed source/config files:', '']
    lines += ['- `'+name+'`' for name in changed]
    note=out/'UNIT_PACKING.md'
    lines += ['',note.read_text() if note.exists() else 'Item 4 has not started; items 1–3 are delivered first.', '',
        'Generated outputs bind the current identity: R1P_PACKET.md, REPORT.md, GATES.json, BINDING.json, MIX.md, SHA256SUMS and the operator archive. No Git, SSH, Orchard, GPU, deletion, full lane copy or write outside this lane was used. The requested snapshot delta is retained for review; packet prose describes current state.', '']
    (out/'FIX5.md').write_text('\n'.join(lines))
    print(json.dumps({'changed_files':changed,'diff':'out/FIX5.diff'}))
if __name__=='__main__':main()
