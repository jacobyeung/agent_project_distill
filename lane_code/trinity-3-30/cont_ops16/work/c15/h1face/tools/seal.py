"""Generate local diffs and final pins without Git or deletion."""
import difflib
import hashlib
import json
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main(diff_only=False, pre_test=False):
    # Fixtures are retained. Only primary artifacts and bounded evidence enter this seal.
    documents=['REPORT.md','UPLOAD_PLAN.md','REMOVAL_CANDIDATES.md','h1pair.py','f1f2.py','room_bootstrap.py']
    code=[]
    for directory in ('kit','tools','tests'):
        for parent, directories, names in os.walk(str(ROOT/directory)):
            directories[:] = [name for name in directories if name not in ('build', '__pycache__')]
            code.extend(Path(parent)/name for name in names if (Path(parent)/name).is_file())
    code.sort()
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
    intended=(ROOT/'evidence/INTENDED_PORTS.md').read_text()
    header[2] += ' The candidate runs its ported suite from tests/, against kit/.'
    header[4] += ' FIX1.md through FIX6.md and FIXF1.md are post-seal receipts containing FINAL_PINS hashes and are excluded from that manifest to avoid a hash cycle.'
    header[6:6]=[intended,'']
    header += [f'| `{n}` | {a} | {b} |' for n,a,b in rows]
    patch=''.join(patches)
    (ROOT/'DIFF.patch').write_text(patch)
    (ROOT/'DIFF.md').write_text('\n'.join(header)+'\n\nThe same exact hunks are available as `DIFF.patch`.\n\n````diff\n'+patch+'````\n')
    if diff_only:
        print(json.dumps(dict(changed_text_files=len(rows),final_pins='not rebuilt')))
        return
    evidence_names=['ASSET_BUILD.json','ASSET_BUILD.log','ID_MAP.json','EXPORT_SOURCES.json',
        'NAME_AUDIT.json','NAME_AUDIT.log','D0_TESTS.log','NEW_TESTS.log','D0_SELF_PAIR.json',
        'RUNTIME_FIXTURE.json','RUNTIME_FIXTURE.log','BIND_100_main.log','BIND_200_main.log','VALIDATION.json',
        'ID_KEY.json','FAMILY_ALIASES.json','INTENDED_PORTS.md','FIX1_REFUTE.log','FIX1_TESTS.log','FIX1_DETERMINISM.json',
        'FIX1_RESERVE.json','FIX1_RESERVE.log','FIX1_BUILD_FIRST.json','FIX1_BUILD_SECOND.log',
        'FIX1_READK_TESTS.log','FIX1c_TESTS.log','FIX1c_READK_TESTS.log','FIX1c_REFUTE.log',
        'FIX1c_DETERMINISM.json','FIX1c_IDS.json',
        'FIX2_BEFORE_PINS.json','FIX2_AUDIT.json','FIX2_AUDIT.log','FIX2_SEARCH_ERRORS.log','FIX2_CONFIG_SEARCH.log',
        'FIX2_TARGETED.log','FIX2_TESTS.log','FIX2_READK_PORTED.log','FIX2_READK_REFERENCE.log',
        'FIX2_REFUTE.log','FIX2_RUNTIME.log',
        'FIX3_BEFORE_PINS.json','FIX3_AUDIT.json','FIX3_TARGETED.log','FIX3_RUNTIME.log',
        'FIX3_TESTS.log','FIX3_READK_PORTED.log','FIX3_READK_REFERENCE.log','FIX3_REFUTE.log',
        'FIX4_BEFORE_PINS.json','FIX4_AUDIT.json','FIX4_NEW_TESTS.log','FIX4_TARGETED.log','FIX4_RUNTIME.log','FIX4_RUNTIME_DIRECT.log',
        'FIX4_TESTS.log','FIX4_READK_PORTED.log','FIX4_READK_REFERENCE.log','FIX4_REFUTE.log',
        'FIX5_BEFORE_PINS.json','FIX5_AUDIT.json','FIX5_NEW_TESTS.log','FIX5_FIX4_TESTS.log',
        'FIX5_TARGETED.log','FIX5_RUNTIME.log','FIX5_RUNTIME_DIRECT.log',
        'FIX5_TESTS.log','FIX5_READK_PORTED.log','FIX5_READK_REFERENCE.log','FIX5_REFUTE.log',
        'FIX6_BEFORE_PINS.json','FIX6_BEFORE_binding.py.txt','FIX6_BEFORE_orchard_launcher.py.txt',
        'FIX6_BEFORE_export_stage.py.txt','FIX6_build_manifest.py','FIX6_BASE_MANIFEST_dev-S1_544.json',
        'FIX6_BASE_MANIFEST_R0-dev_544.json','FIX6_PACKET_EVIDENCE.json','FIX6_AUDIT.json',
        'FIX6_NEW_TESTS.log','FIX6_FIX5_TESTS.log','FIX6_FIX4_TESTS.log','FIX6_TARGETED.log',
        'FIX6_RUNTIME.log','FIX6_RUNTIME_DIRECT.log','FIX6_TESTS.log','FIX6_READK_PORTED.log',
        'FIX6_READK_REFERENCE.log','FIX6_REFUTE.log',
        'FIXF1_BEFORE_SHA256SUMS.txt','FIXF1_BEFORE_PINS.json','FIXF1_BEFORE_orchard_launcher.py.txt',
        'FIXF1_BASELINE.log','FIXF1_FIXTURES.log','FIXF1_AUDIT.json','FIXF1_OPERATOR_COMMANDS.sh','FIXF1_F1.log',
        'FIXF1_CANDIDATE.log','FIXF1_FIX6.log','FIXF1_FIX5.log','FIXF1_FIX4.log',
        'FIXF1_TARGETED.log','FIXF1_PORTED.log','FIXF1_REFERENCE.log','FIXF1_REFUTE.log',
        'FIXF1_RUNTIME.log','FIXF1_RUNTIME_DIRECT.log']
    if pre_test:
        # Test logs must remain writable until their run finishes.
        pending = {'FIX2_TESTS.log','FIX2_READK_PORTED.log','FIX2_READK_REFERENCE.log','FIX2_REFUTE.log',
                   'FIX3_TESTS.log','FIX3_READK_PORTED.log','FIX3_READK_REFERENCE.log','FIX3_REFUTE.log'}
        evidence_names = [name for name in evidence_names if name not in pending and not name.startswith(('FIX4_', 'FIX5_', 'FIX6_', 'FIXF1_'))]
    primary=code+[ROOT/n for n in documents+['DIFF.md','DIFF.patch']]
    primary += [ROOT/'assets/d81f4a26.tar',ROOT/'assets/e52a690b.jsonl']
    primary += [ROOT/'evidence'/n for n in evidence_names]
    primary += [ROOT/'in/out'/n for n in ['FRAMES_MANIFEST.json','DEFERRED.json','R0_REGISTRATION_NOTE.md',
                                       'qsets/R0_QUESTIONS_dev_f32.jsonl','qsets/R0_QUESTIONS_SUMMARY.json']]
    primary += [ROOT/'readk/evidence/FINAL_PINS.json']
    primary += [ROOT/'in/20261116T2218Z_ORCH_RULING_r0dev_dup_qids.md']
    pins={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(primary))}
    (ROOT/'evidence/FINAL_PINS.json').write_text(json.dumps(pins,sort_keys=True,indent=2)+'\n')
    pins['evidence/FINAL_PINS.json']=sha(ROOT/'evidence/FINAL_PINS.json')
    (ROOT/'SHA256SUMS.txt').write_text(''.join(f'{h}  {p}\n' for p,h in sorted(pins.items())))
    print(json.dumps(dict(pinned_files=len(pins),changed_text_files=len(rows),final_pins_sha256=pins['evidence/FINAL_PINS.json'])))

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--diff-only',action='store_true')
    parser.add_argument('--pre-test',action='store_true',help='Exclude pending suite logs until final sealing')
    args=parser.parse_args()
    main(args.diff_only,args.pre_test)
