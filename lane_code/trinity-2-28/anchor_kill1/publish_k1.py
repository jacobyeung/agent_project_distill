"""Write the K1 result into the shared record without regenerating Locate results."""
import argparse
import hashlib
import json
from pathlib import Path

W = Path(__file__).resolve().parent
D = Path('/data2/jjyeung/agent_project_data/distill_design')
B = Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30')


def fmt(r, signed=False):
    sign = '+' if signed else ''
    return f"{r['rate']*100:{sign}.2f} [{r['ci95'][0]*100:{sign}.2f}, {r['ci95'][1]*100:{sign}.2f}]"


def publish(stamp):
    s = json.loads((W/'k1_summary.json').read_text())
    v = json.loads((W/'k1_adapter_validation.json').read_text())
    assert s['rows'] == v['baseline_distances_equal_published'] == 1012
    verdict = 'PASSES' if all(s['bars'].values()) else 'FAILS'
    decision = ('The K1 oracle clears its registered gate; held-out admission remains untested.' if verdict == 'PASSES'
                else 'The registered rule drops ANCHOR; this result does not clear binding at N’s second boundary.')
    result = f'''ANCHOR **{verdict}** the registered K1 kill test. {decision}

The decision population contains 1,012 rows, 2,024 operand occurrences, 204 captures and {s['rooms']} rooms. Every baseline candidate ID, largest-mask frame and IoU agrees with the pinned S_A0 audit; all 1,012 printed baseline distances exactly match the stored deployed replay. The following intervals are percentile 95% intervals from 10,000 paired room draws (seed 20261120).

| K1 measure | Value [95% interval], percent or points | Registered bar | Verdict |
|---|---|---|---|
| Deployed on-target rate | {fmt(s['baseline_right'])} | Reference | — |
| A3x on-target rate | {fmt(s['a3x_right'])} | Diagnostic | — |
| Paired on-target change | {fmt(s['paired_on_target_delta'],True)} | Distinct from distance-type points | — |
| Deployed not-seen rate | {fmt(s['baseline_not_seen'])} | Reference | — |
| A3x not-seen rate | {fmt(s['a3x_not_seen'])} | Empty-frame calls count | — |
| Deployed distance MRA | {fmt(s['baseline_distance_mra'])} | Reference | — |
| A3x distance MRA | {fmt(s['a3x_distance_mra'])} | Diagnostic | — |
| Paired distance-type gain | {fmt(s['paired_distance_mra_delta'],True)} | >=+2.0 points; lower bound >0 | {'PASS' if s['bars']['distance_gain'] else 'FAIL'} |
| Wrong picks corrected, f | {fmt(s['f_fixed_wrong'])} | >=50% | {'PASS' if s['bars']['f_fixed_wrong'] else 'FAIL'} |
| Right picks damaged, h | {fmt(s['h_broken_right'])} | <=5% | {'PASS' if s['bars']['h_broken_right'] else 'FAIL'} |

Correction counts are {int(s['f_fixed_wrong']['numerator'])}/{int(s['f_fixed_wrong']['denominator'])}; damage counts are {int(s['h_broken_right']['numerator'])}/{int(s['h_broken_right']['denominator'])}. On-target means IoU >=0.5 on the selected track’s largest served mask frame, as registered. The percentages quoted in the consumer specification describe a different read and are not substituted for this K1 baseline.

Of the damaged right picks, {s['failure_breakdown']['damaged_to_not_seen']} become not seen and {s['failure_breakdown']['damaged_to_wrong_track']} select a wrong track. Across all calls, {s['failure_breakdown']['not_seen_no_eligible_gt_anchor']} have no GT anchor reaching 1% area, and {s['failure_breakdown']['not_seen_empty_best_frame']} have an eligible best anchor but no linked candidate there. Both groups remain in the primary denominator.

### Neighbouring-anchor sensitivity

The nearest different GT-visible anchor (>=1% area; earlier anchor breaks equal-distance ties) exists for {s['nearest_visible']['calls']}/2,024 operand occurrences. On that same subset, best-anchor A3x is {fmt(s['nearest_visible']['a3x_right'])}% on target; perturbed A3x is {fmt(s['nearest_visible']['neighbor_right'])}%, a paired change of {fmt(s['nearest_visible']['delta_vs_best'],True)} points. Perturbed not-seen is {fmt(s['nearest_visible']['neighbor_not_seen'])}%. The selected candidate changes for {fmt(s['nearest_visible']['candidate_changed'])}%.

An immediate adjacent eligible anchor exists for {s['immediate_adjacent']['calls']} occurrences. That subset scores {fmt(s['immediate_adjacent']['neighbor_right'])}% on target after perturbation, changing {fmt(s['immediate_adjacent']['delta_vs_best'],True)} points against its own best-anchor score. There are {s['no_eligible_gt_anchor']} occurrences without a >=1% GT anchor and {s['no_alternative_visible_anchor']} without an eligible different anchor. Missing alternatives are excluded only from perturbation contrasts, never from the primary kill test.

For the {s['neighbor_distance']['rows']} rows with eligible alternatives for both operands, perturbed distance MRA is {fmt(s['neighbor_distance']['mra'])}; its paired change against best-anchor A3x is {fmt(s['neighbor_distance']['delta_vs_best'],True)} points. This sensitivity has no separately registered pass/fail bar.

### Dataset breakdown

| Dataset | Rows / calls | Deployed on target | A3x on target | Distance-type change |
|---|---|---|---|---|
'''
    for ds, r in s['by_dataset'].items():
        result += f"| {ds} | {r['rows']} / {r['calls']} | {fmt(r['baseline_right'])} | {fmt(r['a3x_right'])} | {fmt(r['paired_distance_mra_delta'],True)} |\n"
    result += f'''
The unique capture/operand diagnostic contains {s['unique_object_diagnostic']['objects']} objects: deployed on-target {fmt(s['unique_object_diagnostic']['baseline'])}%, A3x {fmt(s['unique_object_diagnostic']['a3x'])}%. The primary denominator weights each operand occurrence in each decision row. Both operands are on target in {fmt(s['both_operands_right']['baseline'])}% of deployed rows and {fmt(s['both_operands_right']['a3x'])}% of A3x rows.

If identity is instead tested at the cited frame, best-anchor A3x scores {fmt(s['cited_frame_identity']['best'])}%; the perturbed subset scores {fmt(s['cited_frame_identity']['neighbor'])}%. These are sensitivity measures, not replacements for the registered identity definition.

### Completed Locate diagnostic
'''
    record_path = D/'ANCHOR_KILL_TEST_20261120.md'
    old = record_path.read_text()
    start = old.index('ANCHOR is not cleared to bind.')
    end = old.index('The existing direct-read Locate diagnostic', start)
    out = old[:start]+result+'\n'+old[end:]
    a = out.index('## Missing K1 inputs and transfer')
    b = out.index('## Options rejected',a)
    provenance = f'''## K1 inputs and validation

The staged input root is W/k1_inputs (684 files, 2,619,379,318 bytes according to the transfer receipt). Candidate pools, GT rasters and serving tables are read there. Exact source hashes are checked for every scored pool, raster, serving table, geometry array and selector weight file. The raw adapter records all read paths, sizes and SHA256 values in k1_adapter_validation.json.

The exact decision IDs come from the content-verified sb_cachk/out/v2/POPULATION.json (population ID f0ecd8ee39f1e668027d2fbdf16d4b6bff56d9568dfedd4a90698929f4171bf0). Manifest train flags and the pinned GUARD receipt exclude the withheld captures and every recorded R0, dev-S1, benchmark and K1-held-out hit. This frozen diagnostic uses that receipt; it does not certify a fresh training-admission audit of the specification’s complete current union, including PE-K1 and V1 reserves.

The adapter uses the pinned raw-name retention (joint >=0.05, cap 30), conditional lift floor 0.3, and unchanged linked-candidate producer. Stored selector vectors and pinned weights reproduce the deployed candidate. Candidate IDs and member-frame sets match the serving tables for all {v['objects']} unique objects. Each selected S_A0 seed matches its stored ID, largest frame, mask IoU and on-target flag. Every baseline frame list and all 1,012 printed distances match the published replay.

A3x compares served 240 x 320 member-mask areas. Native-resolution GT rasters supply the >=1% best anchor. The unchanged best1 box and box_grid_5cm reader compute distance from the selected track; the cited anchor selects identity. Corrected distance labels are read from train_labels.json, and refusals score zero. Two captures use the pinned tower and own-gravity inputs to construct the same serving geometry because their saved REFUSED_GEOMETRY files are absent; both still pass candidate, mask and distance parity.

Validation: three focused K1 tests pass. A separate explicit candidate scan verifies all 2,024 best-frame and neighbouring-frame selections; {s['validation']['best_frame_area_ties']} primary calls have equal maximum areas, resolved by frozen pool order. No independent reviewer or launch approval is claimed. The full adapter completed in {v['seconds']:.1f} seconds on one CPU thread.

Artifacts in W: k1_adapter.py, k1_summarize.py, run_k1.sh, k1_calls.jsonl, k1_scored_calls.json, k1_distance_rows.json, k1_adapter_validation.json, k1_summary.json, k1_run.log, k1_tests.log. The record and event persist on shared storage; the runnable code and detailed outputs are named here for review.

'''
    out = out[:a]+provenance+out[b:]
    out = out.replace('The kill test, on-target noninferiority, gap MRA, 95% preceding-Locate coverage and R0 confirmation remain uncomputed.',
                      'N’s held-out on-target noninferiority, gap MRA, 95% preceding-Locate coverage and R0 confirmation remain uncomputed.')
    out = out.replace('The GT half-extent audit is not used here because no box, distance or gap MRA is scored.',
                      'The K1 distance replay uses the pinned corrected K1 labels. The unresolved dev-S1 half-extent audit still prevents a held-out gap-MRA claim.')
    a = out.index('Stage the named K1 inputs through the authorized owner,')
    b = out.index('\n\n## Code, outputs and provenance',a)
    out = out[:a]+'The registered K1 result settles the oracle kill gate. A proposed replacement design needs a new registered test. Any future N admission claim also requires the serialized-candidate dev-S1 replay, preceding-Locate coverage, raster visibility and R0-dev confirmation.'+out[b:]
    out = out.replace('The raw-pool adapter is not complete; the normalized scoring kernel is tested but has not run on K1.',
                      'The raw-pool adapter and complete K1 scoring outputs are listed above; K1_INPUT_SCHEMA.md defines their contract.')
    a = out.index('## Status\n')
    out = out[:a]+f'''## Status

K1 kill test and neighbour sensitivity complete: ANCHOR {verdict}. {decision} The completed Locate diagnostic is preserved without rescoring. N’s full held-out admission gate is not computable from these inputs and is not claimed. No labels, training rows, GPU jobs, SSH connections, Git commands, deletions, paid API calls or >20 MB NFS reads were used. No independent launch review has been claimed.

Writing check: no borderline project-history sentence retained; experiment provenance and read identity are necessary for interpreting the result.
'''
    record_path.write_text(out)
    (W/'FINAL_RECORD.md').write_text(out)
    index = D/'INDEX.md'
    lines = index.read_text().splitlines()
    matches = [i for i,l in enumerate(lines) if l.startswith('- [ANCHOR_KILL_TEST_20261120.md]')]
    assert len(matches) == 1
    lines[matches[0]] = f'- [ANCHOR_KILL_TEST_20261120.md](ANCHOR_KILL_TEST_20261120.md): ANCHOR {verdict} the K1 oracle kill test on 1,012 rows: distance-type gain {fmt(s["paired_distance_mra_delta"],True)}, f={s["f_fixed_wrong"]["rate"]:.3f} (bar >=0.5), h={s["h_broken_right"]["rate"]:.3f} (bar <=0.05). All deployed distances reproduce; neighbour sensitivity complete. Existing Locate diagnostic remains 24.0% / 30.3% against 90%; no N held-out admission claim or training rows. Code and outputs: /scratch/jjyeung/orch_n30/anchor_kill1.'
    index.write_text('\n'.join(lines)+'\n')
    event = f'''# RESULT anchor_kill1: ANCHOR {verdict} the registered K1 kill test
- Population: 1,012 rows / 2,024 operand occurrences / 204 captures / {s['rooms']} rooms; exact frozen IDs, train flags and pinned exclusion receipt checked.
- On-target: deployed {fmt(s['baseline_right'])}%; A3x {fmt(s['a3x_right'])}%; paired change {fmt(s['paired_on_target_delta'],True)} points.
- Not seen: deployed {fmt(s['baseline_not_seen'])}%; A3x {fmt(s['a3x_not_seen'])}%; all empty-frame calls count.
- Distance MRA: deployed {fmt(s['baseline_distance_mra'])}; A3x {fmt(s['a3x_distance_mra'])}; delta {fmt(s['paired_distance_mra_delta'],True)} points vs >=+2.0 and lower bound >0: {'PASS' if s['bars']['distance_gain'] else 'FAIL'}.
- f={fmt(s['f_fixed_wrong'])}% vs >=50%: {'PASS' if s['bars']['f_fixed_wrong'] else 'FAIL'}; h={fmt(s['h_broken_right'])}% vs <=5%: {'PASS' if s['bars']['h_broken_right'] else 'FAIL'}.
- Nearest-visible neighbour: {s['nearest_visible']['calls']} calls, on-target {fmt(s['nearest_visible']['neighbor_right'])}%, not-seen {fmt(s['nearest_visible']['neighbor_not_seen'])}%; paired change vs best {fmt(s['nearest_visible']['delta_vs_best'],True)} points; no registered sensitivity bar.
- Immediate-adjacent subset: {s['immediate_adjacent']['calls']} calls; paired change {fmt(s['immediate_adjacent']['delta_vs_best'],True)} points; no eligible alternative for {s['no_alternative_visible_anchor']} calls.
- Locate results preserved, not rerun: step 400 24.0% [8.9,37.0], step 600 30.3% [7.4,51.5], both FAIL the 90% diagnostic bar; these are forecasts, not N’s export.
- Intervals: 95% percentile, 10,000 paired room draws, seed 20261120. All 1,012 deployed distances match; all {v['objects']} seed IDs/IoUs match; three focused tests and 2,024 explicit choice scans pass.
- Not computable: N’s dev-S1/R0 routed admission (no N candidate replay); direct citations cannot certify 95% call coverage. No current training-admission audit or independent review is claimed.
- Decision: {decision}
- Record: {record_path}; existing INDEX entry updated, no new line.
- Code: {W}/{{k1_adapter.py,k1_summarize.py,run_k1.sh}}.
- Outputs: {W}/{{k1_summary.json,k1_scored_calls.json,k1_distance_rows.json,k1_adapter_validation.json,k1_run.log,k1_tests.log}}.
- CPU only; no SSH, GPU, Git, paid API, deletion, training rows or >20 MB NFS read. Independent result review requested through this event.
'''
    assert len(event.splitlines()) <= 20
    slug = 'fails_registered_bars' if verdict == 'FAILS' else 'passes_oracle_gate'
    event_path = B/'events/anchor'/f'{stamp}_RESULT_anchor_kill1_{slug}.md'
    assert not event_path.exists()
    event_path.write_text(event)
    status = f'Complete: ANCHOR {verdict} K1. Distance-type delta {fmt(s["paired_distance_mra_delta"],True)}; f={s["f_fixed_wrong"]["rate"]:.4f}; h={s["h_broken_right"]["rate"]:.4f}. All 1,012 baseline distances reproduce; neighbouring-anchor read complete. Locate results preserved. Record: {record_path}. Event: {event_path}. Code and detailed outputs: {W}. No training or N held-out admission claim. No independent review claimed.\n'
    (W/'STATUS.md').write_text(status)
    (B/'events/anchor/STATUS.md').write_text(status)
    (W/'PUBLISHED_EVENT_PATH.txt').write_text(str(event_path)+'\n')
    print(str(event_path))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('stamp')
    publish(p.parse_args().stamp)
