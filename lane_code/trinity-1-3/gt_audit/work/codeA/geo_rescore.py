"""Re-run the GEO_TOWERS decide.py (copy, unchanged) on K1 capture files whose distance labels are half-extent-corrected.

Writes capture copies under work/geo/{stored,corrected,drop}/ and runs decide.py on each with the original ORCH GO note.
"""
import glob, json, os, pathlib, subprocess, sys

LANE = pathlib.Path('/scratch/jjyeung/orch_n30/gt_audit')
SRC = LANE / 'work/k1b/orch_n30/geo_k1/harness/out_merged_mdp'
DEC = LANE / 'work/k1b/orch_n30/geo_k1/k1towers/decide.py'
GO = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/b14_k1towers/20261116T1453Z_ORCH_GO_heldout.md'
LAB = {json.loads(l)['id']: json.loads(l) for l in open(LANE / 'work/k1audit/K1_LABELS_CORRECTED.jsonl')}
sys.path.insert(0, str(DEC.parent))
import importlib.util
spec = importlib.util.spec_from_file_location('decide_copy', str(DEC)); D = importlib.util.module_from_spec(spec); spec.loader.exec_module(D)


def main():
    out = LANE / 'work/geo'
    for variant in ['stored', 'corrected', 'drop']:
        d = out / variant; d.mkdir(parents=True, exist_ok=True)
        changed = dropped = 0
        for p in sorted(glob.glob(str(SRC / '*.json'))):
            cap = json.load(open(p)); items = []
            for it in cap['items']:
                if it['type'] == 'object_abs_distance':
                    lab = LAB[it['row_id']]
                    assert abs(lab['stored'] - it['gt']) < 1e-9
                    if variant == 'corrected' and lab['convention'] == 'half':
                        it = dict(it, gt=lab['corrected'], mra=D.mra(it['pred'], lab['corrected'])); changed += 1
                    elif variant == 'drop' and lab['affected']:
                        dropped += 1; continue
                    elif variant == 'stored':
                        assert abs(D.mra(it['pred'], it['gt']) - it['mra']) < 1e-12
                items.append(it)
            json.dump(dict(cap, items=items), open(d / os.path.basename(p), 'w'))
        res = subprocess.run([sys.executable, '-B', str(DEC), str(d), str(out / ('decide_' + variant + '.json')), '--heldout-go', GO],
                             capture_output=True, text=True)
        open(out / ('decide_' + variant + '.stdout'), 'w').write(res.stdout + res.stderr)
        print(variant, 'changed', changed, 'dropped', dropped, 'rc', res.returncode, res.stdout.strip().splitlines()[-1] if res.stdout.strip() else res.stderr[-500:], flush=True)


if __name__ == '__main__':
    main()
