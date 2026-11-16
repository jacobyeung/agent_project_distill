"""Run the unchanged DEPLOY fitting functions and compare exported coefficients.

This is a fixture-only proof, never an eligible training-model producer. It does
not persist either fitted model. Run with the authorized planner_local_v1 interpreter.
"""
import hashlib
import importlib
import json
import os
import pickle
from pathlib import Path
import sys
import traceback

LANE = Path(__file__).resolve().parents[2]
SOURCE = LANE.parent / 'grd_selector/work/setsel'
REFERENCE = LANE.parent / 'devs1_masks/out/kit/work/vendor/MODELS.json'


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def exported(model, features):
    scaler, logistic = [step for _, step in model.steps]
    return dict(features=features, mean=scaler.mean_.tolist(),
                scale=scaler.scale_.tolist(), coef=logistic.coef_[0].tolist(),
                intercept=float(logistic.intercept_[0]))


def compare(actual, expected):
    import numpy as np
    assert actual['features'] == expected['features'], 'feature-order mismatch'
    differences = {
        key: float(np.max(np.abs(np.asarray(actual[key]) - np.asarray(expected[key]))))
        for key in ('mean', 'scale', 'coef', 'intercept')
    }
    return differences


def proof():
    # Import the exact upstream modules; never replace their estimator or solver.
    sys.path.insert(0, str(SOURCE))
    fit = importlib.import_module('fit')
    pairs = importlib.import_module('fit_pairs')
    setlib = importlib.import_module('setlib')
    reference = json.loads(REFERENCE.read_text())
    pickle_deltas = {}
    for tag, path in [('accept', SOURCE / 'data/probs2/deploy_portable_np_logistic.pkl'),
                      ('pairs', SOURCE / 'data/pairs_fit/deploy_pairs_logistic.pkl')]:
        with path.open('rb') as stream:
            deployed = pickle.load(stream)
        pickle_deltas[tag] = compare(exported(deployed['model'], deployed['feats']), reference[tag])
    _, groups = setlib.load(SOURCE / 'data/dev_tab.jsonl')
    candidates = [row for group in groups.values() for row in group]
    _, accept, _ = fit.fit_predict(
        candidates, candidates, setlib.FEATS['portable_np'], 'logistic')
    accept_export = exported(accept, setlib.FEATS['portable_np'])
    accept_delta = compare(accept_export, reference['accept'])
    pair_rows, matrix, labels = pairs.load(SOURCE / 'data/dev_pairs.jsonl')
    labelled = labels >= 0
    pair_model = fit.model('logistic').fit(matrix[labelled], labels[labelled])
    pair_export = exported(pair_model, setlib.PFEATS)
    pair_delta = compare(pair_export, reference['pairs'])
    return dict(accept_max_abs_differences=accept_delta,
                pair_max_abs_differences=pair_delta,
                deployed_pickle_vs_numpy_differences=pickle_deltas,
                largest_difference=max(*accept_delta.values(), *pair_delta.values(),
                                       *(v for d in pickle_deltas.values() for v in d.values())),
                candidate_count=len(candidates), pair_count=len(pair_rows),
                fitted_models_persisted=False)


def main():
    for variable in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
                     'NUMEXPR_NUM_THREADS'):
        os.environ[variable] = '1'
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    out = LANE / 'out'
    files = [SOURCE / name for name in ('build.py', 'fit.py', 'fit_pairs.py',
             'setlib.py', 'data/dev_tab.jsonl', 'data/dev_pairs.jsonl',
             'data/probs2/deploy_portable_np_logistic.pkl',
             'data/pairs_fit/deploy_pairs_logistic.pkl')] + [REFERENCE]
    result = dict(proof='P2', status='NOT_RUN', interpreter=sys.executable,
                  python=sys.version, tolerance=1e-9,
                  input_sha256={str(path): sha256(path) for path in files},
                  fixture_only=True)
    hits = {}

    def trace(frame, event, arg):
        name = frame.f_code.co_filename
        if event == 'line' and (name == __file__ or name.startswith(str(SOURCE) + '/')):
            lines = hits.setdefault(name, {})
            line = str(frame.f_lineno)
            lines[line] = lines.get(line, 0) + 1
        return trace

    sys.settrace(trace)
    try:
        import numpy, sklearn
        result.update(numpy=numpy.__version__, sklearn=sklearn.__version__)
        result.update(proof(), status='PASS')
        if result['largest_difference'] > result['tolerance']:
            result.update(status='FAIL', cause='Pending version, solver and data-order comparison')
    except Exception as error:
        result.update(status='BLOCKED' if isinstance(error, ModuleNotFoundError) else 'FAIL',
                      error_type=type(error).__name__, error=str(error),
                      traceback=traceback.format_exc())
    finally:
        sys.settrace(None)
    result['coverage_path'] = str(out / 'P2_LINE_HITS.json')
    (out / 'P2_LINE_HITS.json').write_text(json.dumps(hits, indent=2) + '\n')
    (out / 'P2_RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
