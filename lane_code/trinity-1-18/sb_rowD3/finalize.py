"""Write the bounded report, checksums and review archive from audited artifacts."""
import hashlib,json,tarfile
from pathlib import Path
BASE=Path(__file__).resolve().parent
OUT=BASE/'out'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4<<20),b''):h.update(b)
    return h.hexdigest()
def main():
    c=json.loads((OUT/'COUNTS.json').read_text());p=json.loads((OUT/'PLAN.json').read_text())
    v=json.loads((OUT/'VERIFY.json').read_text());checks=json.loads((OUT/'CHECKS.json').read_text())
    vc=json.loads((OUT/'VOCABULARY_CHECK.json').read_text());assert vc['status']=='PASS_TEXT_VOCABULARY_ONLY'
    assert v['status']=='PASS_ARTIFACT_INTEGRITY_ONLY' and checks['status']=='MISSING'
    fields=('question_type','pool','retrace_rule','opening','clause')
    allowed={tuple(r[f] for f in fields):r['rows'] for r in c['room_eligible']}
    vocab={}
    for x in c['vocabulary']:vocab.setdefault(x['opening'],set()).update(x['names'])
    lines=[
        'The row build is MISSING. No new row or replacement has passed GT admission; this archive must not be bound as a completed row patch.',
        'All 11 named source packs are absent at their recorded paths and checked local mirrors. MISSING.json gives each exact location and required fields.',
        'The direction rows contain no source-bound coordinates or instance roles. D2 supplies classification and room/validator checks, but no GT recomputation code for these rows.',
        'Command for all census, vocabulary, room, operation and lower-bound numbers: `PYTHONDONTWRITEBYTECODE=1 python build_rows.py` (exit 2 means MISSING).',
        'Independent recount: `PYTHONDONTWRITEBYTECODE=1 python verify_outputs.py`. Vocabulary: `PYTHONDONTWRITEBYTECODE=1 python vocabulary_check.py`. Report/archive: `PYTHONDONTWRITEBYTECODE=1 python finalize.py`.',
        'N tree: W/w19, seal `8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa`; imported kit files match the seal.',
        'Store v7: sha256 `210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443`; 204,413 total rows, 93,370 direction rows.',
        '',
        '| Opening | Clause | Before | Room-eligible | Actual after |',
        '|---|---|---:|---:|---:|']
    eligible={(r['opening'],r['clause']):r['rows'] for r in c['opening_clause_room_eligible']}
    for r in c['opening_clause_before']:
        lines.append(f"| {r['opening']} | {r['clause']} | {r['rows']} | {eligible[r['opening'],r['clause']]} | {r['rows']} |")
    lines += ['', 'Actual after equals before because no change is bound. The room-eligible column applies N’s five exclusion lists; 3,026 rows hit K1, and none hits R0, withheld-80, dev-S1 or BENCH v2.',
        '', '| Family | Pool | Rule | Opening | Clause | Before | Room-eligible |', '|---|---|---|---|---|---:|---:|']
    for r in c['before']:
        k=tuple(r[f] for f in fields)
        lines.append(f"| {r['question_type'].removeprefix('object_rel_direction_')} | {r['pool']} | {r['retrace_rule']} | {r['opening']} | {r['clause']} | {r['rows']} | {allowed.get(k,0)} |")
    lines += ['',
        'Equal shares means the two openings × two clause groups (toward and away/opposite) have equal counts. Retaining all eligible rows gives a count-only minimum of 101,004 additions: 47,837 per final cell, minus 90,344 retained rows. This also permits equal cells within each difficulty family; PLAN.json lists the exact shortages.',
        'The 30,000 cap cannot meet this requirement while preserving compliant rows. Even equal toward/turn shares only within each opening need 56,348 additions; equal shares across all six literal opening/clause cells need 196,678. Before room exclusions, these minima are 106,234, 58,412 and 206,036 respectively.',
        'These are count lower bounds, not achieved quotas: GT reference-quadrant and object-frame availability may require more rows. No compliant row is removed to force balance; new rows must restore at least today’s 25,990 away/opposite coverage after the 481 K1 away exclusions.',
        f"The opening text contains {len(vocab['Step 1'])} normalized object names in Step 1 rows and {len(vocab['Seen'])} in Seen rows. Room-eligible Step 1 rows contain 1,080 names. The full-store count of 1,096 differs from the prompt’s 1,089; VOCABULARY_CHECK.json independently reproduces the literal-name count without alias merging. Generated coverage is zero.",
        'SKELETON.md retains both openings. The quoted question clause selects a separate keep-heading step or half-turn step for toward, away and opposite. Seen variants require verified sampled-frame citations, which the Step 1 sources do not provide.',
        'D2’s pinned full-source checks pass N’s direct VQA validator and trace grammar (93,370 each) for this identical DB/tree; the recount verifies unique source qids. The source schema has no ground_record/events, so routed ground_rows.pack cannot certify these direct rows.',
        'New-row pack/validate, candidate IDs, edited-field diffs, independent GT, quadrant counts and generated-row source-reuse checks are MISSING. Every required addition cell is short; CHECKS.json is not PASS.',
        'NEW_ROWS.jsonl and REPLACEMENTS.jsonl are empty. REMOVE.json is empty because no source is replaced. ROOM_EXCLUSIONS.json separately lists 3,026 exact n.json-format records and passes N’s Removals parser; REMOVE_META.json pins its inputs. Neither patch is bound.',
        'The wording filter threshold is 0.10 normalized Levenshtein distance (NFKC, casefold, whitespace collapse). Comparisons: 0; removals: 0. WORDING_CORPUS.json inventories available kit wordings; full corpus coverage and generated-wording clearance remain MISSING.',
        'READ30.md prints 30 full source rows, one per occupied census cell. READ30_REVIEW.md records the text review; no generated-row correctness review is possible without GT.',
        'VERIFY.json passes artifact integrity only: it independently recounts the store, matches source hashes and 30 samples, checks removal identities and size arithmetic, and confirms that no rows were admitted.',
        'No training, GPU, network, SSH, Git, process termination, deletion or writes outside this workspace were performed. Borderline prose retained: none.'
    ]
    assert len(lines)<=80,len(lines)
    report='\n'.join(lines)+'\n'
    (OUT/'REPORT.md').write_text(report);(OUT/'sb_rowD3_REPORT.md').write_text(report)
    (BASE/'STATUS.md').write_text('The audit is complete; the row build remains MISSING. All 93,370 direction rows are classified and pass N’s direct validators, and the independent recount passes. N’s room rule leaves 90,344 rows. Four equal opening × toward/turn cells require at least 101,004 additions, exceeding the 30,000 cap before GT constraints. All 11 source packs are absent. Zero rows or replacement removals are admitted; the archive contains the census, exact missing paths, both-opening skeleton, lower bounds, source review, and separate proven room exclusions. See out/REPORT.md.\n')
    code=[BASE/'build_rows.py',BASE/'d2_support.py',BASE/'verify_outputs.py',BASE/'vocabulary_check.py',BASE/'finalize.py',BASE/'STATUS.md']
    outputs=[f for f in OUT.iterdir() if f.is_file() and f.name not in {'FILES.json','SHA256SUMS.txt','sb_rowD3.tar'}]
    files=sorted(code+outputs+[BASE/'work/LOCAL_FILES.txt',BASE/'reference/COVERAGE_V2_PUB.tar'])
    manifest=dict(status='MISSING_ROW_BUILD',command='PYTHONDONTWRITEBYTECODE=1 python finalize.py',
        input_sha256={str(f):sha(f) for f in files},
        files=[dict(path=str(f.relative_to(BASE)),bytes=f.stat().st_size,sha256=sha(f)) for f in files])
    (OUT/'FILES.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    files.append(OUT/'FILES.json')
    archive=OUT/'sb_rowD3.tar'
    with tarfile.open(archive,'w') as tar:
        for f in sorted(files):tar.add(f,arcname=str(f.relative_to(BASE)),recursive=False)
    digest=sha(archive)
    (OUT/'SHA256SUMS.txt').write_text(digest+'  sb_rowD3.tar\n')
    with tarfile.open(archive) as tar:assert len(tar.getmembers())==len(files)
    print(json.dumps(dict(status='MISSING_ROW_BUILD',report_lines=len(lines),archive=str(archive),bytes=archive.stat().st_size,sha256=digest),indent=2))
if __name__=='__main__':main()
