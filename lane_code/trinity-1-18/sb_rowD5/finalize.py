"""Package the gate-failure evidence; never mark it as a usable row patch."""
import collections as C
import hashlib
import json
from pathlib import Path
import tarfile

BASE=Path(__file__).resolve().parent
OUT=BASE/'out'

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4<<20),b''):h.update(b)
    return h.hexdigest()

def main():
    gate=json.loads((OUT/'GATE.json').read_text())
    counts=json.loads((OUT/'COUNTS.json').read_text())
    checks=json.loads((OUT/'CHECKS.json').read_text())
    verify=json.loads((OUT/'VERIFY.json').read_text())
    assert gate['status']=='FAIL_STOP' and checks['binding_ready'] is False
    assert verify['status']=='PASS_FAILURE_EVIDENCE_ONLY'
    text=[
        'The required 8,511-of-8,511 exactness gate FAILED. No new rows were generated; this archive is failure evidence and must not be bound as a row patch.',
        f"Only {gate['exact_unique']:,} pairs have an exact, unique answer mapping. All {gate['ambiguous_or_disagreeing']:,} medium pairs have two allowed answers and fail the one-to-one option requirement.",
        'The supplied generator build_away.py rewords admitted v6 away rows and preserves their answers. It does not generate away answers from toward labels.',
        'The supplied check_away.py tests medium answers against sets: left permits right/back, right permits left/back, and back permits left/right. This is consistency, not exact reproduction.',
        f"All {gate['set_consistency_pass']:,} pairs pass that original consistency rule. A literal label flip disagrees with {gate['literal_flip_diagnostic_disagreements']:,} stored answers; it is reported only as a diagnostic, not substituted for the original rule.",
        'GATE.json names every pair, all ambiguous failures, and every literal-flip disagreement. EXAMPLES.json contains full source/twin records. Both checks compare option content and then option letters.',
        'Example: toward label left maps to stored back for vsi590k_116616 but to stored right for vsi590k_243209. EXAMPLES_REVIEW.md records the text review of 12 source/twin pairs; no new mapping was inferred from their traces.',
        'Commands: `PYTHONDONTWRITEBYTECODE=1 python build_rows.py` produces every gate, census and exclusion number (expected exit 2); `PYTHONDONTWRITEBYTECODE=1 python verify_outputs.py` independently checks all 8,511 pairs; `PYTHONDONTWRITEBYTECODE=1 python finalize.py` writes this report and archive.',
        f"Store v7: `{checks['input_sha256'][str(Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite'))]['sha256']}`; 204,413 rows, including 93,370 direction rows.",
        f"N uses the newer sealed W/w19 tree: `{checks['tree_sha256']}`. Imported validator and room modules match that seal.",
        '',
        '| Family | Exact unique reproduction | Ambiguous |',
        '|---|---:|---:|',
    ]
    for family in ('easy','medium','hard'):
        rows=[r for r in gate['by_family'] if r['family']==family]
        text.append(f"| {family} | {sum(r['rows'] for r in rows if r['result']=='PASS')} | {sum(r['rows'] for r in rows if r['result']!='PASS')} |")
    text.extend(['','Medium transitions below show why a toward answer alone cannot select the away answer.','| Toward label | Stored away label | Rows |','|---|---|---:|'])
    for r in verify['medium_transitions']:text.append(f"| {r['toward']} | {r['away']} | {r['rows']} |")
    labels=['left','right','back','front-left','front-right','back-left','back-right']
    text.extend(['','Counts per opening × literal clause × answer label follow. Each entry is `v7 / admitted by N`; before and after are identical because the gate stopped generation.',
        'Easy labels do not identify quadrants; medium back/left/right use the source’s 135-degree rule. The hard labels are quadrants.',
        '| Opening | Clause | '+' | '.join(labels)+' |',
        '|---|---|'+'---:|'*len(labels)])
    before={(r['opening'],r['clause'],r['answer_label']):r['rows'] for r in counts['before']}
    admitted={(r['opening'],r['clause'],r['answer_label']):r['rows'] for r in counts['admitted_before']}
    for o in ('Step 1','Seen'):
        for c in ('toward','away','opposite'):
            text.append('| '+o+' | '+c+' | '+' | '.join(f'{before.get((o,c,l),0)} / {admitted.get((o,c,l),0)}' for l in labels)+' |')
    clause=C.Counter()
    for (o,c,l),n in before.items():clause[c,l]+=n
    text.extend(['','Per-clause v7 answer histogram, unchanged after:'])
    for c in ('toward','away','opposite'):
        text.append(c+': '+', '.join(f'{l}={clause[c,l]}' for l in labels)+'.')
    text.extend([
        '',
        'The split is 0 away and 0 toward additions. The mandatory gate prohibits proceeding with a partial easy/hard build; the 8,000-row allocation and object-name balancing are not attempted.',
        f"N’s direct schema and trace validators each pass all {checks['direct_source_validator_pass']:,} direction sources. All 8,511 pair identities preserve scene, ordered objects, frame metadata and source provenance; all stored away answers/options equal their admitted v6 away sources.",
        'N’s K1, R0, withheld-80, dev-S1 and BENCH v2 room authorities and n/z/u removal lists were applied to every direction row. Input hashes are in CHECKS.json. Exclusion hits: '+json.dumps(counts['exclusion_hits'],sort_keys=True)+'.',
        f"The admitted direction census contains {sum(r['rows'] for r in counts['admitted_before']):,} rows. The K1 and u-union hits overlap; their union excludes {counts['direction_rows']-sum(r['rows'] for r in counts['admitted_before']):,} rows.",
        'New-row checks are NOT RUN: exact quotas, source reuse, pack/validate, candidate IDs, field differences, independent truth, removal inheritance, wording-distance clearance and READ60. READ60.md explicitly records the gate stop; no source examples are passed off as generated rows.',
        'No new wording was emitted: wording comparisons and wording removals are 0. No geometry was recovered or inferred. Direct v7 rows lack routed ground_record/events; source validation does not claim routed packing.',
        'VERIFY.json passes failure-evidence integrity only. NEW_ROWS.jsonl and SOURCE_MAP.jsonl are empty. Every output JSON includes input hashes; the tar checksum is in sb_rowD5.tar.sha256.',
        'No GPU, network, SSH, Git, process termination, deletion, training or writes outside this workspace were used. Borderline prose retained: none.',
    ])
    assert len(text)<=80,len(text)
    (OUT/'REPORT.md').write_text('\n'.join(text)+'\n')
    (BASE/'STATUS.md').write_text(f"The exactness gate failed: {gate['exact_unique']:,}/8,511 pairs reproduce a unique answer; {gate['ambiguous_or_disagreeing']:,} medium pairs remain ambiguous. All 8,511 pass the original set-valued consistency check. The independent verifier confirms the failure evidence. Zero rows were generated; out/REPORT.md and out/sb_rowD5.tar deliver the audit, not a training patch.\n")
    members=[BASE/'build_rows.py',BASE/'verify_outputs.py',BASE/'finalize.py',BASE/'STATUS.md']
    members+=sorted(p for p in (BASE/'reference').iterdir() if p.is_file())
    members+=sorted(p for p in OUT.iterdir() if p.is_file() and p.name not in ('sb_rowD5.tar','sb_rowD5.tar.sha256','PACKAGE.json'))
    package=dict(status='FAILURE_EVIDENCE_ONLY',binding_ready=False,new_rows=0,
        command='PYTHONDONTWRITEBYTECODE=1 python finalize.py',input_sha256={str(p.relative_to(BASE)):sha(p) for p in members})
    (OUT/'PACKAGE.json').write_text(json.dumps(package,indent=2,sort_keys=True)+'\n')
    members.append(OUT/'PACKAGE.json')
    archive=OUT/'sb_rowD5.tar'
    with tarfile.open(archive,'w') as tar:
        for p in members:tar.add(p,arcname=str(p.relative_to(BASE)),recursive=False)
    digest=sha(archive)
    (OUT/'sb_rowD5.tar.sha256').write_text(digest+'  sb_rowD5.tar\n')
    with tarfile.open(archive) as tar:
        assert len(tar.getmembers())==len(members)
        for p in members:
            assert hashlib.sha256(tar.extractfile(str(p.relative_to(BASE))).read()).hexdigest()==sha(p)
    print(json.dumps(dict(archive=str(archive),sha256=digest,bytes=archive.stat().st_size,members=len(members),report_lines=len(text))))

if __name__=='__main__':main()
