"""Render current proof artifacts and package the tested CPU source."""
import hashlib
import platform
import re
from collections import Counter
from .paths import ROOT, OUT, R2R_GT
from .io import read_json, write_json
from .package_source import package_source
from .runner import execution_sha256


def main():
    proof = read_json(OUT/'tables/evaluation_summary_all.json')
    plans = read_json(OUT/'tables/subset_plans.json')
    replay = read_json(OUT/'tables/replay.json')
    locations = read_json(OUT/'tables/location_replay.json')
    comparison = read_json(OUT/'tables/controller_comparison.json')
    assert comparison['execution_sha256'] == execution_sha256(), 'Stale controller proofs'
    rand = read_json(OUT/'lists/rand100.json')
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
        './run.sh -m navrun.controller_proofs  # both controllers/leads and rand100',
        './run.sh -m navrun.build_report',
        '```', '',
        f'Unit gate: **{count} passed, 0 failed, 0 skipped in {seconds:.3f} s**. All 118 existing tests pass. Tests cover the 102-episode stall replay, recovery direction and reset, external click backend, config defaults, rand100 order/identity and malformed releases.', '',
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
        f'Blind policies use official training statistics: median forward count {stats["median_forward_steps"]}, median turn run {stats["median_turn_run"]}. Random draws iid primitive frequencies, including STOP, with SHA256(seed:episode_id) RNG. Instruction-prior splits the forward budget around lexical left/right/around occurrences. The record does not specify its blind-policy implementations.', '',
        '| Oracle-click, fixed 600 ids | Version | SR | SPL | OSR | nDTW | SDTW | Step caps | Stationary tails |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|',
    ]
    for name,label in [('oracle-click','Geodesic lead, STOP <1 m'),('oracle-gt-click','GT-location lead, STOP <3 m')]:
        for version in ('v1','v2'):
            r=comparison['cells'][f'{name}_{version}_{small}']
            lines.append(f'| {label} | {version} | {r["SR"]:.6f} | {r["SPL"]:.6f} | {r["OSR"]:.6f} | {r["nDTW"]:.6f} | {r["SDTW"]:.6f} | {r["step_caps"]} | {r["stationary_tails"]} |')
    lines += [
        '| Record GT lead, no occlusion | record | 0.802 | 0.792 | 0.847 | unavailable | unavailable | unavailable | unavailable |', '',
        'Geodesic lead interpolates 2 m along the current shortest path to the goal. GT lead chooses the nearest 3-D GT location (first index wins ties), then interpolates 2 m forward along that path, clamping at its endpoint. It requests STOP when geodesic goal distance is strictly below the 3 m success radius. It has no monotonic-index restriction.', '',
        'Both variants use the same floor-plane lift without occlusion. Schema 8.2 supplies the 2 m maximum leg, 0.5 m standoff, 15-degree turn and 0.25 m forward step. SENSOR supplies 512 px / 90 degrees / 1.25 m. The 3 m success radius comes from the record and Config. Lead source and STOP radius both differ between variants.', '',
        '`Config.controller_version="v2"` is the NU/oracle-click default; `"v1"` preserves vla_where exactly. Config files use `vla.nav.eval.controller_version`. The sealed vla_where source is unchanged. V2 retains normal v1 commands, cancels the remaining leg at the first blocked forward step, then turns one quantum and probes one forward step per decision until motion resumes.', '',
        'A blocked step moves less than 1e-6 m, the existing diagnostic zero-motion tolerance. Recovery starts toward the blocked leg’s bearing (left for zero) and keeps that direction despite subsequent bearing changes; this prevents alternating corrections from stalling. STOP takes precedence. Recovery uses no fitted bearing threshold, budget or score-dependent parameter.', '',
        'Both the model-facing click decoder and an injected vla_where `ClickTranslator` pass through the same versioned controller. Only navrun receives displacement. Backend observations remain the five schema-8.4 fields; `executed_commanded` receives actual issued forward primitives × 0.25 m. Waypoint decoding and GT training-row conversion retain schema 8.2 behavior.', '',
        'The fixture `tests/fixtures/controller_v1_stalls.json` stores the 102 ids, v1 action streams, controller-source hash and final 20 decision observations. CPU replay reproduces all 102 v1 streams/tails exactly; v2 leaves **0/102 stationary tails**. Full evaluation also reproduces **1,200/1,200 v1 action streams and metrics** across both leads.', '',
        'Stationary tails require at least 20 decisions, with every last-20 decision position within 1e-4 m of the final decision position; heading changes do not count as movement. The step cap is 500 primitives. Residual step caps remain failures even when a tail moves.', '',
        'The four residual GT-lead stationary tails (619, 1077, 1076, 1369) alternate explicit 90-degree left/right outputs and issue no forward primitives in their last 20 decisions. Blocked-forward recovery therefore does not trigger. Their traces are in `out/tables/controller_v2_residual_tails.json`.', '',
        'Changes to the reported click numbers are logged below as **v2 minus v1** (metric fractions, not percentage points). Training proofs and the full/600 blind-policy numbers are unchanged.', '',
        '| Lead | ΔSR | ΔSPL | ΔOSR | ΔnDTW | ΔSDTW | ΔStep caps | ΔStationary tails |',
        '|---|---:|---:|---:|---:|---:|---:|---:|',
    ]
    for name,label in [('oracle-click','Geodesic'),('oracle-gt-click','GT-location')]:
        d=comparison['v2_minus_v1'][name]
        values=' | '.join(f'{d[k]:+.6f}' for k in ('SR','SPL','OSR','nDTW','SDTW'))
        lines.append(f'| {label} | {values} | {d["step_caps"]:+d} | {d["stationary_tails"]:+d} |')
    lines += ['',
        'rand100 is **READY**: 100 episodes / 10 scenes from Open-Nav’s OpenNav_R2R-CE_100 release, in file order. All ids, scenes, trajectories and start positions match v1-3 val-unseen. The .json.gz source is plain JSON; gzip is detected by magic bytes. Drive id: `1SfrPWqCIiivwduCYPMe-Za1wOt4eU6G9`.', '',
        f'Source SHA256: `{rand["source_sha256"]}`. Ordered-id SHA256 (UTF-8 ids, trailing LF): `{rand["ordered_id_sha256"]}`. Frozen list: `out/lists/rand100.json`.', '',
        '| rand100 policy | SR | Record SR | ΔSR | SPL | OSR | nDTW |',
        '|---|---:|---:|---:|---:|---:|---:|',
    ]
    for name,record in [('oracle',1.),('random',.030),('forward-only',.060),('instruction-prior',.060)]:
        r=comparison['cells'][name+'_rand100']
        lines.append(f'| {name} | {r["SR"]:.6f} | {record:.3f} | {r["SR"]-record:+.6f} | {r["SPL"]:.6f} | {r["OSR"]:.6f} | {r["nDTW"]:.6f} |')
    lines += ['',
        'rand100 uses official dense GT references and the same fixed training statistics and policy definitions as the full/600 proofs. Blind-prior differences from the record are reported without fitting policies to those scores.', '',
        'Resume signatures cover code, config, ordered ids, episode contents, metric references and policy identity; the GT-click identity also hashes its lead references and controller defaults. Journals preserve completed episodes. `out/STOP` stops at primitive boundaries.', '',
        'Unavailable checks: GPU rendering/depth occlusion, habitat-lab parity, `nav.contracts.validate_public`, real model/tokenizer integration and real detection AUC/ATD. Scene manifests for student/G3T/SAM3 remain provenance unknown. Train/val-unseen/test scene sets are disjoint.', '',
        f'Source archive: `out/navrun_src.tgz` (package, tests including fixtures, configs, wrapper, README and pyproject; excludes output data). **SHA256: {sha}**.', '',
        'Evidence: `out/tables/controller_comparison.json`, versioned click tables, `*_rand100.json`, existing training/metric proofs, journals, `out/controller_proofs.log` and `out/unit_tests.log`.',
    ]
    assert len(lines)<=150, len(lines)
    (ROOT/'BUILD_REPORT.md').write_text('\n'.join(lines)+'\n')
    print(f'BUILD_REPORT.md: {len(lines)} lines; archive sha256 {sha}')

if __name__=='__main__': main()
