"""Render the bounded report and package this refusal kit without certifying new rows."""
import hashlib
import json
from pathlib import Path
import tarfile

BASE = Path(__file__).resolve().parent
OUT = BASE/'out'


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4<<20),b''):h.update(b)
    return h.hexdigest()


def main():
    counts=json.loads((OUT/'COUNTS.json').read_text())
    checks=json.loads((OUT/'CHECKS.json').read_text())
    plan=json.loads((OUT/'TWIN_PLAN.json').read_text())
    missing=json.loads((OUT/'MISSING.json').read_text())
    n=counts['direction_rows']; nr=checks['removal']['records']
    assert checks['status']=='MISSING' and checks['replacement_rows']==checks['twin_rows']==0
    cells=counts['cells']
    lines=[
        f'The row build is MISSING: all {n:,} direction rows lack source-bound GT geometry. No replacement or twin is certified.',
        f'The deliverable contains a full census, exact skeleton, proposed quotas, refusal ledger, and {nr:,} proven room removals. Binding remains the orchestrator’s decision.',
        '',
        'Command for all census, clause, refusal, room, validation and quota numbers: `PYTHONDONTWRITEBYTECODE=1 python build_rows.py` (exit 2 deliberately signals MISSING).',
        'Command for this report, file hashes and archive: `python finalize.py`.',
        'Independent artifact checks: `PYTHONDONTWRITEBYTECODE=1 python verify_outputs.py`; VERIFY.json distinguishes artifact integrity from row admission.',
        'N uses W/w19’s sealed tree `8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa`; imported code hashes match its seal.',
        'Store v7: `210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443`; 204,413 rows.',
        f'Clause counts: toward {counts["clauses"].get("toward",0):,}; away {counts["clauses"].get("away",0):,}; opposite {counts["clauses"].get("opposite",0):,}.',
        'The Step 1 group contains 49,901 toward rows in w1g with retrace rule rows_rebuild_d0_v1. That rule is not a separate pool.',
        '',
        '| Family | Pool | Opening | Clause | Rows |',
        '|---|---|---|---|---:|']
    for c in cells:
        lines.append('| '+ ' | '.join(str(c[k]).replace('object_rel_direction_','') for k in ('question_type','pool','opening','clause','rows'))+' |')
    lines += [
        '',
        f'Twin proposal: {plan["source_count"]:,} sources ({100*plan["proposed_share"]:.2f}% of Step 1) yield {plan["twins"]:,} twins, one away and one opposite per source.',
        'Each clause gets 810 easy, 971 medium and 1,336 hard rows per reference quadrant. All 24 cells are short: actual 0. No quota was silently reduced.',
        'GT must determine reference quadrants. The plan gives hard twins equal front/back truth counts; it does not fit R0-dev answers or flip old labels.',
        f'Room audit resolves {n:,} rows and excludes {nr:,} K1 rows; R0, withheld-80, dev-S1 and BENCH v2 each have zero hits. Proven aliases and pinned physical-room lists support these counts.',
        f'N’s native direct-row validator and trace grammar each pass all {n:,} source rows. These checks do not certify geometry.',
        'The sources use the direct VQA schema. N’s r2_contract.validate and trace_grammar.validate_row apply; ground_rows.pack requires routed grounding records absent here.',
        f'REMOVE.json contains {nr:,} JSONL records with exactly n.json’s five fields; N’s Removals parser accepts every record. It removes only proven excluded rooms.',
        'REMOVE_META.json records its hashes without changing the required removal schema. Missing GT alone does not remove the other source rows.',
        f'MISSING.json names {len(missing["sources"])} absent source packs and exact checked paths. REFUSED.jsonl records every refused source qid and source-row hash.',
        'The store carries no GT coordinates, instance roles, signed-up convention or ground record for these questions. R0-dev rasters are excluded training inputs.',
        'READ30.md prints 30 complete source rows; READ30_REVIEW.md records their text review. No generated rows exist for the required generated-row review.',
        'Normalized edit-distance filter: proposed cutoff 0.10 (NFKC, casefold, whitespace collapse; Levenshtein/max length). Comparisons 0, removed 0; clearance is MISSING.',
        'A complete dev/benchmark wording corpus is not bound. No new question was copied from development or benchmark items.',
        'Pack/validate of new rows, independent GT recomputation, candidate IDs, edited-field diffs and generated-row checks remain MISSING. CHECKS.json is not PASS.',
        'SKELETON.md specifies the exact common opening, quoted clause before the operation, source frame handling, GT relation rules and medium-angle caveat.',
        'No training, GPU, network, Git, SSH, process termination or external writes were performed. No binding or live-store modification was made.',
        'Borderline prose retained: none.',
    ]
    assert len(lines)<=80,len(lines)
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
    (BASE/'STATUS.md').write_text(f'The census and room-removal audit are complete for {n:,} direction rows. The bundle contains {nr:,} verified room-removal records, the common skeleton and 24 proposed twin cells. The row build remains MISSING because all source GT joins are absent; replacements and twins are empty, and CHECKS.json explicitly refuses certification. See out/REPORT.md.\n')
    include=[BASE/'build_rows.py',BASE/'finalize.py',BASE/'verify_outputs.py',BASE/'STATUS.md',
        BASE/'alias_inputs/out/TIERED_ALIAS_MAP.json',BASE/'alias_inputs/out/ROOM_AUDIT_TIERED.json',
        BASE/'alias_inputs/work/TEACHER_K1.raw']
    include += [OUT/n for n in ('COUNTS.json','COUNTS.md','CHECKS.json','MISSING.json','TWIN_PLAN.json',
        'REFUSED.jsonl','REPLACEMENTS.jsonl','TWINS.jsonl','REMOVE.json','REMOVE_META.json',
        'READ30.md','READ30_REVIEW.md','SKELETON.md','REPORT.md','VERIFY.json')]
    files={str(p.relative_to(BASE)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in include}
    manifest=dict(status='MISSING',command='python finalize.py',input_sha256=checks['input_sha256'],files=files)
    (OUT/'FILES.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    include.append(OUT/'FILES.json')
    with tarfile.open(OUT/'sb_rowD2.tar','w') as t:
        for p in include:t.add(p,arcname=str(p.relative_to(BASE)),recursive=False)
    digest=sha(OUT/'sb_rowD2.tar')
    (OUT/'sb_rowD2.tar.sha256').write_text(digest+'  sb_rowD2.tar\n')
    print(digest)


if __name__=='__main__':main()
