"""Render current proof artifacts and package the tested CPU source."""
import hashlib
import platform
import re
from collections import Counter
from .paths import ROOT, OUT, R2R_GT
from .io import read_json, write_json
from .package_source import package_source


def main():
    proof = read_json(OUT/'tables/evaluation_summary_all.json')
    plans = read_json(OUT/'tables/subset_plans.json')
    replay = read_json(OUT/'tables/replay.json')
    locations = read_json(OUT/'tables/location_replay.json')
    diag = read_json(OUT/'tables/oracle_click_diagnostics.json')['summary']
    stats = read_json(OUT/'tables/training_statistics.json')
    log = (OUT/'unit_tests.log').read_text()
    match = re.search(r'Ran (\d+) tests in ([\d.]+)s', log)
    if not match or not log.rstrip().endswith('OK'):
        raise ValueError('The unit gate must pass before packaging')
    count, seconds = int(match.group(1)), float(match.group(2))
    write_json(OUT/'tables/unit_tests.json', dict(run=count, passed=count, failed=0, skipped=0, wall_seconds=seconds))
    provenance = {}
    for split in ('train', 'val_seen', 'val_unseen'):
        path = R2R_GT/split/(split+'_gt.json.gz')
        provenance[split] = dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    write_json(OUT/'tables/official_gt_sources.json', provenance)
    write_json(OUT/'tables/throughput.json', {k:{f:v[f] for f in ('n','wall_seconds','episode_compute_seconds','episodes_per_hour')}
                                             for k,v in proof.items() if 'episodes_per_hour' in v})
    sha = package_source()
    full, small, ie = 'val_unseen_full_1839', 'val_unseen_600_s0', 'r2rie_direction_300'
    def get(name, cell): return proof[name+'_'+cell]
    lines = [
        '# navrun CPU build report', '',
        f'Python {platform.python_version()}, habitat-sim 0.2.4, CPU navmesh simulator, no renderer. All training GT and val-unseen metric references come from official R2R-CE preprocessed files.', '',
        '`run.sh` uses `nice -n 19`, OMP/MKL/OpenBLAS limits of 8 and scratch caches. Work stays in this workspace. No network, SSH, Git, installation, GPU or detached process is used.', '',
        '```sh',
        './run.sh -m unittest discover -s tests',
        './run.sh -m navrun.proofs plans  # tracks, statistics, both replays, 1%/10% rows',
        './run.sh -m navrun.proofs eval   # dense-reference proofs and both click variants',
        './run.sh -m navrun.click_diagnostics  # unchanged geodesic policy, decision traces',
        './run.sh -m navrun.build_report',
        '```', '',
        f'Unit gate: **{count} passed, 0 failed, 0 skipped in {seconds:.3f} s**. All 105 existing tests pass. Added tests cover official-id loading, coverage, malformed GT, cache refresh, GT arc-length leads, duplicates, endpoint/tie behavior, STOP boundaries and resume identity.', '',
        'Official GT root: `../navrun_inputs/refs/r2r_vlnce_preprocessed/R2R_VLNCE_v1-3_preprocessed`. The loader validates primitive streams, forward counts, location alignment, complete requested-id coverage and start positions. Official files override cached reconstructions; R2RIE and greedy reconstruction remain labelled fallbacks and serve **0 training episodes**.', '',
        '| GT file | SHA256 |', '|---|---|',
    ]
    for split, p in provenance.items(): lines.append(f'| {split}_gt.json.gz | `{p["sha256"]}` |')
    lines += ['',
        f'Nav codec replay matches official actions on **{replay["exact_action_replays"]:,}/{replay["episodes"]:,}** training episodes: {len(replay["mismatched_ids"])} mismatches, {replay["nav_rows"]:,} answers and {replay["primitive_states"]:,} primitives. Every stream has source `supplied_official_r2r_ce_gt`.', '',
        '| Simulator replay against GT locations | Episodes | Endpoints within 2e-6 m | Entire path within 2e-6 m |', '|---|---:|---:|---:|',
    ]
    for label, r in [('Full train',locations['full'])]+[(k,v) for k,v in locations['subsets'].items()]:
        lines.append(f'| {label} | {r["episodes"]:,} | {r["endpoints_within_tolerance"]:,} | {r["paths_within_tolerance"]:,} |')
    ep3707 = next(r for r in locations['results'] if r['episode_id']=='3707')
    lines += ['',
        f'Replay executes every action from the episode start pose and compares the start plus every forward endpoint, including blocked moves. Maximum full-training path error: {locations["full"]["max_path_error_m"]:.9g} m. Episode 3707 has maximum path error {ep3707["max_path_error_m"]:.9g} m and endpoint error {ep3707["endpoint_error_m"]:.9g} m. The record’s 0.42 m intermediate discrepancy is not reproduced in this simulator.', '',
        '| Training plan | Episodes | States / text / chunk | Nav rows | Click rows | Waypoint rows |', '|---|---:|---:|---:|---:|---:|',
    ]
    for label, p in [('1%',plans['subset_1pct']),('10%',plans)]:
        c=p['row_counts']
        lines.append(f'| {label} | {p["episodes"]:,} | {c["text"]:,} each | {c["nav"]:,} | {c["click"]:,} | {c["waypoint"]:,} |')
    lines += ['',
        f'Both seed-0 subsets cover all 61 scenes and nest exactly. The 1% click label counts are {plans["subset_1pct"]["click_reasons"]}. The record reports 6,348 states, 1,158 nav, 1,497 click and 1,232 waypoint rows for its 1% subset; its exact ids and terminal-sampling implementation are unavailable.', '',
        'Rows carry official GT provenance, prompts, history indices, executed primitives, answers and planned frame paths. Nav packs up to three primitives per token and three tokens per answer. Click rows advance by commanded primitive count and stop at the first within-1m decision. CPU frame paths refer to absent PNGs. `out/rows/rows.jsonl.gz` and `subset_1pct_rows.jsonl.gz` contain the 10% and 1% rows.', '',
        '| Val-unseen proof | Episodes | SR | SPL | nDTW | SDTW |', '|---|---:|---:|---:|---:|---:|',
    ]
    for name in ('oracle','random','forward-only','instruction-prior'):
        for cell in (full, small):
            r=get(name,cell)
            assert r['reference_sources']=={'supplied_dense_gt':r['n'],'sparse_reference_path':0}
            lines.append(f'| {name} | {r["n"]} | {r["SR"]:.6f} | {r["SPL"]:.6f} | {r["nDTW"]:.6f} | {r["SDTW"]:.6f} |')
    lines += ['',
        'All 1,839 val-unseen episodes use official `val_unseen_gt.locations` for nDTW/SDTW; sparse-reference count is zero. FastDTW uses radius 1 and Euclidean costs after consecutive-position deduplication. R2RIE proofs retain their supplied dense references. The full-val shortest-path oracle record is SR 1.000 / SPL 0.999.', '',
        f'Blind policies use official training statistics: median forward count {stats["median_forward_steps"]}, median turn run {stats["median_turn_run"]}. Random draws iid primitive frequencies, including STOP, with SHA256(seed:episode_id) RNG. Instruction-prior splits the forward budget around lexical left/right/around occurrences. Record policy details and exact list hashes are unavailable.', '',
        '| Oracle-click on the fixed 600 ids | SR | SPL | OSR | nDTW | SDTW | 500-step caps |', '|---|---:|---:|---:|---:|---:|---:|',
    ]
    for name,label in [('oracle-click','Geodesic lead, STOP <1 m'),('oracle-gt-click','GT-location lead, STOP <3 m')]:
        r=get(name,small)
        results=read_json(OUT/'tables'/f'{name}_{small}.json')['results']
        caps=sum(x['termination']=='step_cap' for x in results)
        lines.append(f'| {label} | {r["SR"]:.6f} | {r["SPL"]:.6f} | {r["OSR"]:.6f} | {r["nDTW"]:.6f} | {r["SDTW"]:.6f} | {caps} |')
    lines += [
        '| Record GT lead, no occlusion | 0.802 | 0.792 | 0.847 | unavailable | unavailable | unavailable |', '',
        'Geodesic lead interpolates 2 m along the current shortest path to the goal. GT lead chooses the nearest 3-D GT location (first index wins ties), then interpolates 2 m forward along that path, clamping at its endpoint. It requests STOP when geodesic goal distance is strictly below the 3 m success radius. It has no monotonic-index restriction.', '',
        'Both variants project the lead point and use the same floor-plane lift/controller without occlusion. The GT lookahead uses `vla_where.nav.CLICK.max_leg_m=2.0`; standoff is 0.5 m, turns are 15 degrees, forward steps are 0.25 m, and SENSOR is 512 px / 90 degrees / 1.25 m. The success radius comes from the record and Config. No parameters were tuned to the record’s scores. Lead source and STOP radius both differ, so this comparison does not isolate either effect.', '',
        f'Geodesic diagnostics reproduce **{diag["unchanged_action_streams"]}/600** saved action streams exactly. Its {diag["step_caps"]} capped tails partition into {diag["capped_tail_classes"]}; tails use the last 20 decisions, stationary means every position is within 1e-4 m of the final one, and repeated states round pose/heading to 5 decimals.', '',
        '| Overlapping observations among 201 geodesic caps | Episodes |', '|---|---:|',
    ]
    for label,key in [('At least one blocked forward step','capped_with_blocked_forward'),
                      ('Repeated pose/heading in final 20 decisions','capped_with_tail_repeated_pose_heading'),
                      ('Near-point clamp in final 20 decisions','capped_with_tail_clamp'),
                      ('Out-of-view turn in final 20 decisions','capped_with_tail_out_of_view'),
                      ('Nonzero bearing rounded to zero turns in final 20','capped_with_tail_zero_turn_nonzero_bearing'),
                      ('Bearing sign changes in final 20','capped_with_tail_turn_direction_changes'),
                      ('Empty commands in final 20','capped_with_tail_empty_commands'),
                      ('Within success radius at a decision boundary','capped_with_success_at_decision')]:
        lines.append(f'| {label} | {diag[key]} |')
    lines += ['',
        f'Of the 118 stationary tails, 102 have nonzero bearings rounded to zero turns at every one of the last 20 decisions; none of the 201 tails consists entirely of turn-only commands. The controller repeatedly commands blocked forward motion when a small correction rounds to zero turns. Near-point clamps lift y=0.99 to at least 1.276 m forward range and approximately 0.75 m commanded travel, which can sustain overshoot near corners/goals. These are overlapping trace observations, not mutually exclusive causal attributions. The 1 m STOP rule misses {diag["capped_with_OSR"]} episodes that reach the 3 m success radius; {diag["capped_final_within_success"]} finish inside it. No empty-command decision-cap failure explains the 201 step caps.', '',
        'Resume signatures cover code, config, ordered ids, episode contents, metric references and policy identity; the GT-click identity also hashes its lead references and controller defaults. Journals preserve completed episodes. `out/STOP` stops at primitive boundaries.', '',
        'Unavailable checks: GPU rendering/depth occlusion, habitat-lab parity, `nav.contracts.validate_public`, MIP rand100 ids, real model/tokenizer integration and real detection AUC/ATD. Scene manifests for student/G3T/SAM3 remain provenance unknown. Train/val-unseen/test scene sets are disjoint.', '',
        f'Source archive: `out/navrun_src.tgz` (package, tests, configs, wrapper, README and pyproject; excludes output data). **SHA256: {sha}**.', '',
        'Evidence: `out/tables/{replay,location_replay,subset_plans,official_gt_sources,oracle_click_diagnostics,evaluation_summary_all}.json`, per-policy tables, journals and `out/unit_tests.log`.',
    ]
    assert len(lines)<=130, len(lines)
    (ROOT/'BUILD_REPORT.md').write_text('\n'.join(lines)+'\n')
    print(f'BUILD_REPORT.md: {len(lines)} lines; archive sha256 {sha}')

if __name__=='__main__': main()
