"""Package failed-gate evidence; never label this archive as an admitted row patch."""
import hashlib
import json
from pathlib import Path
import tarfile
B=Path(__file__).resolve().parent
O=B/'out'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4<<20),b''):h.update(b)
    return h.hexdigest()

def main():
    g=json.loads((O/'TRANSFORMATION_CHECK.json').read_text())
    c=json.loads((O/'COUNTS.json').read_text())
    v=json.loads((O/'VERIFY.json').read_text())
    assert g['status']=='FAIL_STOP' and v['failures']==g['failed']
    lines=[f"The build stopped at the required exactness gate: {g['failed']:,} of {g['pairs']:,} paired-clause comparisons disagree with the stored-answer half turn.",
        f"Of those failures, {g['both_eligible_failed']:,} survive N's room rule and n/z/u removal lists. NEW_ROWS.jsonl and SOURCE_MAP.jsonl are empty; this archive is evidence, not an admitted row patch.",
        "Command for census, pair comparisons, eligibility and source checks: `PYTHONDONTWRITEBYTECODE=1 python build_rows.py` (exit 2 = failed gate).",
        "Independent verification: `PYTHONDONTWRITEBYTECODE=1 python verify_outputs.py`. Packaging: `PYTHONDONTWRITEBYTECODE=1 python finalize.py`.",
        f"N tree: W/w19, seal `{g['tree_sha256']}`. Store v7: `{g['input_sha256']['/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite']['sha256']}`.",
        "Pairs share dataset, scene, family, ordered A/B/C names and pair_id; frames and provenance source identity also match. Answers are decoded through each row's options.",
        "",'| Family | Clause pair | Pass | Fail |','|---|---|---:|---:|']
    stat={(x['family'],x['clause'],x['result']):x['rows'] for x in g['by_family_clause']}
    for f in ('easy','medium','hard'):
        for cl in ('away','opposite'):lines.append(f"| {f} | toward → {cl} | {stat.get((f,cl,'pass'),0)} | {stat.get((f,cl,'fail'),0)} |")
    lines.extend(['',
        "The geometric half turn is valid. The medium answer labels lose information: N defines back as |theta| ≥ 135°, while both left and right span 135°. A stored left can become right or back; a stored back can become left or right. The three-label vocabulary is not closed under the proposed front/back label swap.",
        "N's definition is in `generator/derivgen_v7/derivgen/ground_v312.py`, lines 218–227. Existing opposite rows declare a half turn and match their away partner's answer.",
        "The following are existing row counterexamples, not invented geometry:"])
    examples=[]
    for x in g['disagreements']:
        if not x['both_eligible']:continue
        transition=(x['toward_label'],x['stored_turn_label'])
        if transition in {t for t,_ in examples}:continue
        examples.append((transition,x))
        if len(examples)==4:break
    for _,x in examples:
        lines.append(f"- `{x['toward_qid']}` → `{x['turn_qid']}`: stored {x['toward_label']} → {x['stored_turn_label']}; label flip predicts {x['expected_turn_label']}.")
    lines.extend(['', '| Opening | Clause | Before | Eligible | After |','|---|---|---:|---:|---:|'])
    eligible={(x['opening'],x['clause']):x['rows'] for x in c['eligible_after_room_and_removal_lists']}
    for x in c['before']:
        lines.append(f"| {x['opening']} | {x['clause']} | {x['rows']} | {eligible[x['opening'],x['clause']]} | {x['rows']} |")
    lines.extend(['',
        "After equals before because no patch is emitted. Eligible counts apply K1, R0, withheld-80, dev-S1 and BENCH v2 exclusions plus N's n.json, z.json and sb_k1list/out/u_union.json. Exclusion hits can overlap.",
        "A smaller count-only design would select 7,000 eligible Step 1 sources and 7,000 eligible Seen sources and emit each source under both toward and away clauses: 28,000 kit rows, 7,000 per opening × clause cell, using each source at most twice. This avoids balancing all 93,370 legacy rows. It is only a proposed kit size; eligibility, wording and quadrant capacity have not been established, and the global legacy-store cells would remain unequal.",
        "No smaller compliant build is claimed: the explicit stop rule prevents source selection or generation after a disagreement. Existing Seen frame citations cannot be invented for Step 1 sources; widening Seen vocabulary requires source-bound frame evidence or a separate approved opening change.",
        "All 93,370 direction sources pass N's direct VQA validator and trace grammar. All 204,413 store qids are unique. Imported N files match the seal. VERIFY.json independently recomputes every comparison and checks input hashes.",
        "New-row cell quotas, source reuse, pack/validate, candidate IDs, field diffs, independent transformed truth, vocabulary/quadrant balance and wording clearance are NOT_RUN_GATE_FAILED. Ground-truth geometry was neither sought nor required for this counterexample audit.",
        "The planned wording threshold is normalized Levenshtein distance ≤ 0.10. Comparisons and removals are zero because no new wording was generated; this is not a passed wording filter.",
        "READ30.md contains 30 full existing source rows from 15 eligible failing pairs. Their question, options and traces are reproduced in READ30_REVIEW.txt. The review checks the label failure; it does not certify physical geometry. No generated-row READ30 check is claimed.",
        "REMOVE.json is not emitted because no rows are replaced. No training, GPU, network, SSH, Git, deletion, process termination or writes outside this workspace occurred.",
        "The package omits the reference coverage archive because generation never passed its prerequisite gate. No lost GT pack is listed as a blocker: the demonstrated blocker is the non-exact medium label transformation.",
        "Borderline prose retained: none."])
    assert len(lines)<=80
    (O/'REPORT.md').write_text('\n'.join(lines)+'\n')
    (B/'STATUS.md').write_text(f"The build is stopped and packaged as failed-gate evidence. The audit found {g['failed']:,} disagreements among {g['pairs']:,} clause pairs, including {g['both_eligible_failed']:,} eligible failures. Easy and hard results are reported separately; medium's stored labels do not determine the rotated label. No new rows or replacement list are emitted. out/REPORT.md and out/CHECKS.json state the unrun checks; out/sb_rowD4.tar and its SHA256 file contain the reproducible audit.\n")
    paths=[B/'build_rows.py',B/'verify_outputs.py',B/'finalize.py',B/'STATUS.md']+[O/n for n in ('TRANSFORMATION_CHECK.json','COUNTS.json','CHECKS.json','VERIFY.json','READ30.md','READ30_REVIEW.txt','REPORT.md','NEW_ROWS.jsonl','SOURCE_MAP.jsonl')]
    manifest=dict(command='PYTHONDONTWRITEBYTECODE=1 python finalize.py',status='FAILED_GATE_EVIDENCE_ONLY',
                  input_sha256={str(p):{'sha256':sha(p)} for p in paths},
                  files=[dict(path=str(p.relative_to(B)),bytes=p.stat().st_size,sha256=sha(p)) for p in paths])
    (O/'FILES.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    with tarfile.open(O/'sb_rowD4.tar','w') as t:
        for p in paths+[O/'FILES.json']:t.add(p,arcname=str(p.relative_to(B)),recursive=False)
    digest=sha(O/'sb_rowD4.tar')
    (O/'sb_rowD4.tar.sha256').write_text(digest+'  sb_rowD4.tar\n')
    print(digest)
if __name__=='__main__':main()
