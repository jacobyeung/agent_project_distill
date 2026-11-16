"""Official extraction, metric adapters, and parity-gated summaries."""
from collections import Counter, defaultdict
import importlib.util
import math
from pathlib import Path
import re
import sys
import types
from evalpath import official

_METRIC_CLASS=None


def metric_for(tasks):
    """Load the unchanged metric with an offline ground-truth loader.

    Its datasets import receives an offline stub; no Hugging Face call is possible.
    The subclass changes only data loading. update() and compute() are verbatim.
    """
    global _METRIC_CLASS
    if _METRIC_CLASS is not None:
        return _METRIC_CLASS(tasks)
    stub = types.ModuleType('datasets')
    def refuse(*args, **kwargs):
        raise RuntimeError('Online metric loading is disabled')
    stub.load_dataset = refuse
    previous = sys.modules.get('datasets')
    previous_metric = sys.modules.get('torchmetrics')
    states=types.ModuleType('torchmetrics')
    class StateMetric:
        def add_state(self,name,default,dist_reduce_fx):
            setattr(self,name,default.clone())
    states.Metric=StateMetric
    sys.modules['torchmetrics']=states
    sys.modules['datasets'] = stub
    try:
        spec = importlib.util.spec_from_file_location('_pinned_metric', Path(__file__).with_name('metric.py'))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        if previous is None:
            sys.modules.pop('datasets', None)
        else:
            sys.modules['datasets'] = previous
        if previous_metric is None:
            sys.modules.pop('torchmetrics',None)
        else:
            sys.modules['torchmetrics']=previous_metric
    class OfflineMetric(mod.ReVSIMetric):
        def __init__(self,rows):
            self.rows=rows
            super().__init__(subset='32_frame')
        def _load_gt_data(self, split):
            self.gt_data = {int(t['example_id']): t for t in self.rows}
    _METRIC_CLASS=OfflineMetric
    return OfflineMetric(tasks)


def score_item(task, raw, tokens, cap=16384, finish='stop'):
    if task['benchmark']=='pointing_video':
        from pointing_video import parse_output
        return dict(response_text=raw,extracted_answer=None,extract_branch='pointing_video',score=None,
                    **parse_output(raw),empty_think=False,hit_token_cap=tokens>=64 or finish=='length',
                    output_tokens=tokens,max_new_tokens=64)
    if task['benchmark']=='pointing':
        from pointing import parsed
        cap=48
        return dict(response_text=raw,extracted_answer=None,extract_branch='pointing',score=None,
                    **parsed(raw),empty_think=False,hit_token_cap=tokens>=cap or finish=='length',
                    output_tokens=tokens,max_new_tokens=cap)
    answer, branch = official.extract_q35_final_answer(raw, True)
    fuzzy = official.official_fuzzy_matching(answer)
    if task['benchmark'] == 'revsi':
        m = metric_for([task])
        m.update({int(task['example_id']):answer})
        score = float(m.__dict__[task['question_type']+'_acc'])/1.0
        # Use the official first-token parse convention for the diagnostic.
        first = answer.strip().split(' ')[0].rstrip('.').strip()
        parse_failed = not first
        if task['question_type'] in m.numeric_question_types:
            try:
                parse_failed = not math.isfinite(float(first))
            except ValueError:
                parse_failed = True
    elif official.infer_answer_type(task) == 'multiple_choice':
        score = official.official_exact_match(fuzzy, str(task['ground_truth']).strip())
        parse_failed = not fuzzy
    else:
        v = official.official_to_float(fuzzy)
        score = official.official_mra(v, official.official_to_float(str(task['ground_truth']).strip()))
        parse_failed = v is None
    close = list(re.finditer(r'</think\s*>',raw,re.I))
    think = raw[:close[-1].start()] if close else raw
    think = re.sub(r'^<think\s*>\s*','',think,flags=re.I)
    return dict(response_text=answer, extracted_answer=answer, extract_branch=branch,
                score=score, parse_failed=parse_failed, empty_think=bool(close) and not think.strip(),
                hit_token_cap=tokens>=cap or finish=='length', output_tokens=tokens, max_new_tokens=cap)


def clean_metric(value):
    return {k:float(v) if math.isfinite(float(v)) else None for k,v in value.items()}


def benchmark_summary(rows, tasks, parity):
    completed = [r for r in rows if r.get('status')=='complete']
    result = dict(expected=len(tasks), completed=len(completed), errors=len(rows)-len(completed),
        cap_hits=sum(r.get('hit_token_cap',False) for r in rows),
        parse_failures=sum(r.get('parse_failed',True) for r in rows),
        empty_thinks=sum(r.get('empty_think',False) for r in rows),
        generated_tokens=sum(r.get('output_tokens',0) for r in rows),
        parity_pass=parity, numbers_status='eligible' if parity and len(completed)==len(tasks) else 'do not count')
    by_type=defaultdict(list)
    for r in completed:
        if r['score'] is not None:by_type[r['question_type']].append(r['score'])
    result['per_type']={k:dict(count=len(v),score=sum(v)/len(v)) for k,v in by_type.items()}
    if not completed:
        result['overall_score']=None
        return result
    benchmark=tasks[0]['benchmark']
    if benchmark in ('pointing','pointing_video'):
        result.update(overall_score=None,per_type={},numbers_status='Trinity GT scoring required',
                      raw_text_retained=True)
        return result
    if benchmark=='revsi':
        m=metric_for(tasks)
        m.update({int(r['example_id']):r['response_text'] for r in completed})
        scores=clean_metric(m.compute())
        result.update(overall_score=(scores['overall_acc']/100 if scores['overall_acc'] is not None else None),
                      official_metric=scores, per_category={k[:-4]:v for k,v in scores.items() if k!='overall_acc'})
        visible={int(t['example_id']) for t in tasks if t.get('visible_32') is True}
        m=metric_for(tasks)
        m.update({int(r['example_id']):r['response_text'] for r in completed if int(r['example_id']) in visible})
        # Official compute nanmean excludes categories absent from this subscore.
        result['visible_32']=dict(count=sum(int(r['example_id']) in visible for r in completed),
                                  official_metric=clean_metric(m.compute()))
    elif benchmark in ('vsi500','vsi500_slice','official5130','devrows'):
        s=official.score_official_vsibench(completed,expected_count=0)
        s.pop('scored_records')
        result.update(overall_score=s['overall_score'],official_metric=s,
                      per_official_group=s['per_task_score_pct'])
    else:
        s,_=official.score_our_cell(completed,'v','vstibench_repr450_v3',0)
        result.update(overall_score=s['fuzzy_primary_score'],per_official_group=s['fuzzy_primary_task_scores'],
                      strict_diagnostic=s['primary_score'])
    if benchmark == 'vstifull':
        result['item_flags'] = {f:sum(t[f] for t in tasks) for f in ('frame_ref_m_lt_32','erratum')}
        result['filtered_scores'] = {}
        for flag in ('frame_ref_m_lt_32',):
            keep = {t['example_id'] for t in tasks if not t[flag]}
            subset = [r for r in completed if r['example_id'] in keep]
            s, _ = official.score_our_cell(subset, 'v', 'vstibench_repr450_v3', 0)
            result['filtered_scores']['excluding_'+flag] = dict(expected=len(keep), completed=len(subset),
                overall_score=s['fuzzy_primary_score'])
    return result
