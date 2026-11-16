"""Describe every production delta against the sealed C8r archive itself."""
from pathlib import Path, PurePosixPath
import difflib
import hashlib
import json
import sys
import tarfile
B=Path(__file__).resolve().parents[1];O=B/'out';K=O/'guard_kit'
sys.path.insert(0,str(K))
from guard_core import read,write,sha
archive=B.parent/'build/in_c8r_kit/code_c8r.tar'
assert sha(archive).startswith('f4535bc0')
with tarfile.open(archive) as stream:
    original={str(PurePosixPath(m.name)):stream.extractfile(m).read() for m in stream if m.isfile()}
inventory=read(O/'CODE_MANIFEST.json')['members']
current={name:(K/name).read_bytes() for name in inventory}
assert set(original)<=set(current)
reasons={
 'admission.py':'Native journal merge and request/score/geometry admission; G2 item 2, G3 item 1',
 'checkpoint.py':'Fresh checkpoint process, identity proof, published canary and native read; G1 items 3–5, G2 item 2',
 'closure.py':'Candidate config, source-seal, preparation and initialization-chain authentication; G2 item 1',
 'fetch.py':'Verify and unpack the plan-bound returned archive; G2 item 2',
 'guard_backend.py':'Re-derive export-dependent contracts while preserving C8r pins and restoration; G1 items 1–2',
 'guard_core.py':'Completion parsing, byte pins, ordered proof, canary and native rows; G1 items 1–5',
 'guard_export.py':'Bind candidate completion bytes and invoke unchanged reviewed export admission; G1 item 1',
 'names.py':'Neutral-name projection and byte-preserving round-trip audit; G1 item 6, G2 item 3',
 'native_arm.py':'Select only the native arm without editing kernel bytes or converting answers; G1 item 3',
 'packet.py':'Candidate plan and authority gates, pinned payload and command-line Slurm resources; G1 items 1,4,7, G2 item 2',
 'pool.py':'Reserve exclusive publication tokens and enforce result-pool bounds; G2 item 2',
 'stage_candidate.py':'Run the reviewed full export checker inside the C8r namespace; G2 items 1–2',
 'staging.py':'Stage both exports, bind closure artifact bytes, reject hard links; G2 items 1–2',
 'transport.py':'Bound and authenticate publication, archive and returned stage evidence; G2 items 2,4, G4 fix 3',
 'worker.py':'Coordinate proof/candidate processes, retain stage receipts and bind report artifact/source; G2 item 2, G4 fixes 1,3',
}
rows=[];patch=[];changes=[]
for name in sorted(set(original)|set(current)):
    old,new=original.get(name,b''),current.get(name,b'')
    if old==new:continue
    before,after=old.decode().splitlines(keepends=True),new.decode().splitlines(keepends=True)
    patch.extend(difflib.unified_diff(before,after,fromfile='C8r/'+name,tofile='G4/'+name))
    reason=reasons.get(name)
    if name.startswith('reviewed/'):
        reason='Byte-identical reviewed stager/checker dependency added to authenticate D0 exports; G1 item 1, G2 item 1'
    assert reason,name
    blocks=[]
    for kind,i,j,k,l in difflib.SequenceMatcher(a=before,b=after,autojunk=False).get_opcodes():
        if kind=='equal':continue
        span=f'{k+1}–{l}' if l>k else f'after {k}'
        rows.append(f'| `out/guard_kit/{name}` | {span} | {kind} | {reason} |')
        blocks.append(dict(operation=kind,c8r_lines=[i+1,j],current_lines=[k+1,l]))
    changes.append(dict(file='out/guard_kit/'+name,sha256=sha(K/name),blocks=blocks,reason=reason))
text=''.join(patch)
(O/'DIFF_C8R.patch').write_text(text)
(O/'DIFF.patch').write_text(text)
(O/'DIFF.md').write_text('''# Production changes against sealed C8r

The baseline is `../build/in_c8r_kit/code_c8r.tar`, SHA256 `'''+sha(archive)+'''`.
`DIFF_C8R.patch` and `DIFF.patch` contain the same complete unified diff against that archive, including newly bundled reviewed dependencies. The table lists every added or changed production block and its current line range. All inherited C8r members and the reviewed dependency bytes remain unchanged (`SOURCE_IDENTITY.json`).

The code inventory comes from `CODE_MANIFEST.json`; rehearsal scripts, tests, operator transfer helpers and backup files stay outside the production tar. The stage receipt fix changes `worker.py` and `transport.py`. Report commands use the operator-updated source pin and CONFIG artifact (`REPORT_PIN_G4.json`). ORCH accepted the seven sealed trainer-tree names at 1601Z; the naming projections do not alter trainer bytes.

| File | Current lines | Change | Reason / brief item |
|---|---|---|---|
'''+ '\n'.join(rows)+'\n')
write(O/'DIFF_C8R.json',dict(baseline=str(archive),baseline_sha256=sha(archive),
      patch_sha256=sha(O/'DIFF_C8R.patch'),changed_files=changes,
      unchanged_files=sorted(name for name in original if original[name]==current.get(name))))
print('C8r diff:',len(changes),'files;',len(rows),'changed blocks')
