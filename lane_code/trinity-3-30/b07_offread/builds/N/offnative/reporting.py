"""Trinity reports use offkit aggregation and labels without local rule copies."""
from .io import load, rows, digest
from .worker import merge
from offkit import report as R

def report(binding, cohort, returned, out, *, fixture=False, repetitions=10000):
    if binding['reader']['kind']=='harness' and binding.get('read_config',{}).get('g3t',{}).get('source') not in ('clip32','original'):
        raise ValueError('harness report lacks a bound G3T source')
    complete = load(returned/'COMPLETE.json')
    if not complete.get('complete') or bool(complete.get('fixture')) != fixture:
        raise ValueError('return is incomplete or fixture status differs')
    if complete['binding_sha256'] != binding['binding_sha256']:
        raise ValueError('return binding differs')
    ids = [R.key(r) for r in cohort]
    if complete['ids_sha256'] != digest(ids) or complete['items'] != len(ids):
        raise ValueError('completion cohort identity differs')
    mode = R.ReadMode(binding['benchmark'], binding['reader']['kind'])
    if fixture:
        mode.items = len(cohort)
        mode.spec = dict(mode.spec, scenes=len({(r['dataset'],r['scene_name']) for r in cohort}))
    R.check_cohort(mode, cohort)
    reports = {}
    for arm in binding['arms']:
        records = merge(ids, [rows(returned/(arm+'.jsonl'))])
        rep = R.aggregate(mode, cohort, records, repetitions=repetitions)
        rep = R.label_report(rep, binding=binding, arm=arm, role=arm,
                             arm_label='Synthetic CPU fixture; not a benchmark result.' if fixture else None)
        rep['binding_sha256'] = binding['binding_sha256']
        source = binding.get('read_config',{}).get('g3t',{})
        if binding['reader']['kind']=='harness' and source.get('source')=='clip32':
            from .source import CLIP_LABEL
            rep['g3t_source'] = CLIP_LABEL
            # offkit owns the label and report format.
            if not fixture:
                raise ValueError('clip32 is diagnostic only; claimed reports are refused')
            rep = R.label_report(rep, binding=binding, arm=arm, role=arm,
                                 arm_label=CLIP_LABEL+('; Synthetic CPU fixture; not a benchmark result.' if fixture else ''))
        reports[arm] = R.write(rep, out, arm)
    return reports
