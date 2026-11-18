"""Generate local diffs and final pins without Git or deletion."""
import difflib
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    # Fixtures are retained. Only primary artifacts and bounded evidence enter this seal.
    documents=['REPORT.md','UPLOAD_PLAN.md','REMOVAL_CANDIDATES.md','h1pair.py']
    code=sorted(p for directory in ('kit','tools','tests') for p in (ROOT/directory).rglob('*')
                if p.is_file() and '__pycache__' not in p.parts and 'build' not in p.relative_to(ROOT).parts)
    candidates=code+[ROOT/n for n in documents]+[ROOT/'assets/e52a690b.jsonl']
    rows=[];patches=[]
    for p in sorted(candidates):
        rel=str(p.relative_to(ROOT));old=ROOT/'readk'/rel
        raw=p.read_bytes();previous=old.read_bytes() if old.is_file() else b''
        if previous==raw:continue
        if b'\0' in raw or b'\0' in previous:
            rows.append((rel,'binary',len(raw)));continue
        a=previous.decode().splitlines(keepends=True);b=raw.decode().splitlines(keepends=True)
        delta=''.join(difflib.unified_diff(a,b,fromfile='readk/'+rel if old.is_file() else '/dev/null',tofile=rel))
        patches.append(delta);rows.append((rel,len(a),len(b)))
    header=['# Exact candidate diff','','The baseline is `readk/`, whose FINAL_PINS.json SHA256 is `07582397649cdcb30e9bca8cd27396bf4a5797ce776f79132f992f9364121a0a`. The candidate preserves all reference kit files; no source file was removed. Reference tests remain in `readk/tests/`. The hunks below cover every changed line of candidate code, new tools/tests, documents, the asset registry and the rewritten item file. All paths are local.','','Generated evidence is pinned separately in `evidence/FINAL_PINS.json`. Test-fixture directories and ledgers are excluded from this source diff. The new binary tar is described by its exact byte count and SHA256 in UPLOAD_PLAN.md and SHA256SUMS.txt. DIFF.md, DIFF.patch, SHA256SUMS.txt and FINAL_PINS.json exclude their own recursive differences.','','| File | Baseline lines | Candidate lines |','|---|---:|---:|']
    header += [f'| `{n}` | {a} | {b} |' for n,a,b in rows]
    patch=''.join(patches)
    (ROOT/'DIFF.patch').write_text(patch)
    (ROOT/'DIFF.md').write_text('\n'.join(header)+'\n\nThe same exact hunks are available as `DIFF.patch`.\n\n````diff\n'+patch+'````\n')
    evidence_names=['ASSET_BUILD.json','ASSET_BUILD.log','ID_MAP.json','EXPORT_SOURCES.json',
        'NAME_AUDIT.json','NAME_AUDIT.log','D0_TESTS.log','NEW_TESTS.log','D0_SELF_PAIR.json',
        'RUNTIME_FIXTURE.json','RUNTIME_FIXTURE.log','BIND_100_main.log','BIND_200_main.log','VALIDATION.json']
    primary=code+[ROOT/n for n in documents+['DIFF.md','DIFF.patch']]
    primary += [ROOT/'assets/d81f4a26.tar',ROOT/'assets/e52a690b.jsonl']
    primary += [ROOT/'evidence'/n for n in evidence_names]
    primary += [ROOT/'in/out'/n for n in ['FRAMES_MANIFEST.json','DEFERRED.json','R0_REGISTRATION_NOTE.md',
                                       'qsets/R0_QUESTIONS_dev_f32.jsonl','qsets/R0_QUESTIONS_SUMMARY.json']]
    primary += [ROOT/'readk/evidence/FINAL_PINS.json']
    pins={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(primary))}
    (ROOT/'evidence/FINAL_PINS.json').write_text(json.dumps(pins,sort_keys=True,indent=2)+'\n')
    pins['evidence/FINAL_PINS.json']=sha(ROOT/'evidence/FINAL_PINS.json')
    (ROOT/'SHA256SUMS.txt').write_text(''.join(f'{h}  {p}\n' for p,h in sorted(pins.items())))
    print(json.dumps(dict(pinned_files=len(pins),changed_text_files=len(rows),final_pins_sha256=pins['evidence/FINAL_PINS.json'])))

if __name__=='__main__':main()
