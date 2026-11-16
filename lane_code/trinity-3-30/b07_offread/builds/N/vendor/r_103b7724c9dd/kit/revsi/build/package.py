"""Deterministic package and complete byte inventory relative to the readonly VSI kit."""
from pathlib import Path
import difflib,hashlib,io,json,tarfile
K=Path(__file__).resolve().parents[1];base=K.parent/'kit'
base_names=json.loads((K/'build/BASE_FILES.json').read_text())
# Sources and current evidence only; environments, generated clips and runs stay local.
names=set(base_names)
for directory in ('inputs','media'):
    names.update(str(p.relative_to(K)) for p in (K/directory).iterdir() if p.is_file() and p.suffix in ('.py','.json'))
names.update(('cohort/c5.jsonl','proof/LOCAL_PROOF.json','build/package.py','build/evidence.py','build/BASE_FILES.json'))
names=sorted(names - {'inputs/cells_rv999_d32_cp1m200_on.json','inputs/cells_tr_rv999_cp1on.json'})
records={};diffs=[]
with tarfile.open(K/'package.tar','w',format=tarfile.USTAR_FORMAT) as archive:
    for name in names:
        raw=(K/name).read_bytes();h=hashlib.sha256(raw).hexdigest();item=tarfile.TarInfo(name)
        item.size=len(raw);item.mode=0o755 if name.endswith('.sh') else 0o644;item.mtime=0;item.uid=item.gid=0;item.uname=item.gname=''
        archive.addfile(item,io.BytesIO(raw))
        old=base/name;status='NEW';old_hash=None
        if old.is_file():
            previous=old.read_bytes();old_hash=hashlib.sha256(previous).hexdigest();status='IDENTICAL' if raw==previous else 'CHANGED'
            if status=='CHANGED':
                try:delta=''.join(difflib.unified_diff(previous.decode().splitlines(True),raw.decode().splitlines(True),fromfile='kit/'+name,tofile='kit_revsi/'+name))
                except UnicodeDecodeError:delta='Binary evidence changed; hashes are listed above.\n'
                diffs.append('### '+name+'\n\n```diff\n'+delta+'```\n')
        records[name]=dict(status=status,sha256=h,bytes=len(raw),base_sha256=old_hash)
sha=hashlib.sha256((K/'package.tar').read_bytes()).hexdigest();(K/'KIT_SHA256').write_text(sha+'  package.tar\n')
(K/'build/PACKAGE_FILES.json').write_text(json.dumps(records,indent=2)+'\n')
lines=['# Package inventory relative to kit/','',
'KIT_SHA256: `'+sha+'`','',
'package.tar contains sorted regular files with fixed modes, mtime 0, uid/gid 0 and empty owner/group names. REPORT.md, DIFF.md, KIT_SHA256 and generated build inventories are external sidecars to avoid circular hashes. Runtime payloads exclude both the unused VSI cohort and local media source provenance.','',
'The base consists of the 111 non-build files in the accepted VSI package. Environments, build outputs, test caches, generated proof runs, test_runs and the base package archive are excluded. Inherited unused VSI input files remain byte-identical but are never sent as ReVSI tasks.','',
'Only evaluator/data.py changes inside evaluator/: optional sorted question_types and proof example_ids filters run after all native membership/tier/video/source-index checks. evalpath/SOURCE_PINS.json does not pin data.py; it remains byte-identical. Bind code inventories pin the adapted source. The existing VSI kit_inputs.py filter is unchanged relative to kit/.','',
'The adapter binds official999 tier 32 and the five-category cohort. The same worker, scoring.score_item, metric.py, frame stage, budgets, merges, accepted dev Phase B, export verification and return code remain byte-identical. Frame-plan validation checks compact anchors plus reconstructed source timing. The launcher stages 261 byte/SHA-verified clips from CONFIG media_root and binds only job-local copies.','',
'The scorer averages subtype accuracies equally within each category, then averages the five categories equally. Paired bootstrap accepts parent merged budget items and uses identical scene weights. Real parent results are unavailable. Local metric checks use the unmodified metric with a NumPy tensor substitute; real torch/vLLM remains an Orchard check.','',
'NEED_261.json records 189 explicit durable sources and 72 paths inferred from the user-specified tier-32 directory because REVSI_PUSH_FILES.json omits them. Every source remains subject to byte/SHA validation by the operator archive builder.','',
'All 261 local proof clips are generated fixtures. Inherited coverage and proof reports are replaced with observed ReVSI evidence. No Orchard evidence is assumed.','',
'## Every packaged file','', '| File | Status | SHA256 | kit/ SHA256 |','|---|---|---|---|']
for n,r in records.items():lines.append(f"| {n} | {r['status']} | `{r['sha256']}` | `{r['base_sha256'] or '—'}` |")
lines+=['','## Unified diffs','']+diffs
(K/'DIFF.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(files=len(names),bytes=(K/'package.tar').stat().st_size,sha256=sha,identical=sum(r['status']=='IDENTICAL' for r in records.values()),changed=sum(r['status']=='CHANGED' for r in records.values()),new=sum(r['status']=='NEW' for r in records.values()))))
