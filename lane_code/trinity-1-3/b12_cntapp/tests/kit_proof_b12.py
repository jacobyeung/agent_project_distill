"""CPU kit proof for b12_cntapp rows: the D0 v5 preparation closure (kit_proof_v5.py) applied row by row to the new families,
with job A config 6224c536: removal files, held qids/sources, route table, benchmark/reported exclusions, sealed dev-S1/bench
scene filter, withheld-80, single-image check, and carrier_c1_data.layout_inputs(duplicate, verify_partners=True).
Usage: /scratch/jjyeung/envs/p1cpu/bin/python kit_proof_b12.py ROWS_DIR  (CUDA_VISIBLE_DEVICES='')"""
import collections, json, os, sys
from pathlib import Path
ROOT = Path('/scratch/jjyeung/orch_n30/rows_rebuild')
sys.path[:0] = ['/scratch/jjyeung/orch_n30/rows_rebuild/work/d0/stubs', str(ROOT / 'work/d0'), str(ROOT / 'work/tree/src'), str(ROOT / 'work')]
from build import W, K, load, pin, sha
CONFIG = Path('/scratch/jjyeung/orch_n30/rows_rebuild3/work/jobA_config_6224c536.json')
assert sha(CONFIG) == '911daa1e5d967266a3f406b1cfe04bd5fc2aa04fcdc1219e1800cef2d7c3d64b'

def main():
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '': raise ValueError('CPU proof requires empty CUDA_VISIBLE_DEVICES')
    from student_pilot import carrier_c1_data as data, carrier_c1_run as run
    from student_pilot.p3_provenance import pinned
    from student_pilot.row_removals import Removals
    from student_pilot.s1_exclusions import Exclusions
    D = Path(sys.argv[1]); cfg = load(CONFIG)
    def local(original, path):
        value = {'path': str(path.resolve()), 'sha256': original['sha256']}; pinned(value); return value
    for field in ('exclude_qids', 'exclusions', 'report_exclusions', 'dev_scene_exclusions', 'benchmark_scene_exclusions'):
        if cfg.get(field): cfg[field] = local(cfg[field], K / Path(cfg[field]['path']).name)
    removes = [{**spec, **local({k: spec[k] for k in ('path', 'sha256')}, K / Path(spec['path']).name)} for spec in cfg['remove_files']]
    qids = {k: set(v) for k, v in load(cfg['exclude_qids']['path']).items()}
    benchmark = run.routing.load_exclusions(cfg['exclusions']); reported = run.routing.load_exclusions(cfg['report_exclusions'])
    sf = Exclusions(cfg['dev_scene_exclusions'], cfg['benchmark_scene_exclusions']); removal = Removals(removes)
    withheld = load(W / 'withheld/WITHHELD_ROOMS_80.json'); wa = {a for v in withheld['aliases'].values() for a in v}
    settings = data.layout_settings(cfg); out = {}
    for fam in ('count_single', 'count_total', 'appearance', 'first_seen'):
        c = collections.Counter(); fails = []
        for line in open(D / (fam + '.jsonl')):
            row = json.loads(line); reasons = []; c['seen'] += 1
            if removal.match(row): reasons.append('REMOVE')
            if run.held_row(row, 'vqa', qids, cfg.get('exclude_sources') or {}): reasons.append('held_row')
            if run.routed_type(row, cfg) and not cfg.get('tool_mode_flag'): reasons.append('routed_type')
            hit, overlap = run.excluded_row(row, benchmark, reported, 'vqa'); c['reported_overlap'] += overlap
            if hit: reasons.append('prepare_exclusions')
            if not sf.keep(row, 'vqa'): reasons.append('s1_sealed_scene_exclusion')
            if row['dataset'] + '/' + row['scene'] in wa: reasons.append('vqa_withheld_room')
            try:
                if data.single_image_row(row, 'vqa', training_mode=cfg.get('training_mode', 'mixed'), geometry_online=cfg.get('geometry_online')):
                    reasons.append('single_image')
                lay = data.layout_inputs(row, *settings, verify_partners=True)
                if len(lay['frames']) != 2 * len(row['student_input']['frames']): reasons.append('layout frame count')
            except Exception as e: reasons.append('layout: ' + type(e).__name__ + ': ' + str(e)[:200])
            if not isinstance(row.get('target'), str) or not row['target'].strip(): reasons.append('empty target')
            if any(t in row['target'] for t in ('<|im_start|>', '<|im_end|>', '<|video_pad|>', '<|image_pad|>')): reasons.append('control token')
            if reasons: c.update(reasons); fails.append(dict(qid=row['qid'], reasons=reasons))
            else: c['admitted'] += 1
        out[fam] = dict(counts=dict(c), failures=fails[:20])
    res = dict(config=pin(CONFIG), layout_settings=list(settings), families=out,
               status='PASS' if all(v['counts'].get('admitted') == v['counts']['seen'] for v in out.values()) else 'FAIL')
    json.dump(res, open(D / 'KIT_PROOF.json', 'w'), indent=1); print(json.dumps({k: v['counts'] for k, v in out.items()}), res['status'])

if __name__ == '__main__':
    main()
