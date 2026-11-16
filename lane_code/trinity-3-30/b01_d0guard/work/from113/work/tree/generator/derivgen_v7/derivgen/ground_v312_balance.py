"""Deduplicated content quotas with exact letter equality per option count."""
from collections import Counter, defaultdict
from .ground_v312_quality import deduplicate, set_report


def uniform_subset(rows, limit):
    if not rows:
        return []
    n = len(rows[0]['options'])
    buckets = {chr(65+i):[] for i in range(n)}
    for row in sorted(rows, key=lambda r:r['qid']):
        buckets[row['answer']].append(row)
    quota = min(limit//n, *(len(v) for v in buckets.values()))
    return [row for values in buckets.values() for row in values[:quota]]


def balance(rows, distributions, per_type, legacy):
    unique, duplicates = deduplicate(rows)
    selected, report = [], {}
    for typ in sorted({r['type'] for r in unique}):
        group = [r for r in unique if r['type']==typ]
        if typ == 'object_rel_distance' and all('options' in r for r in group):
            counts = Counter(len(r['options']) for r in group)
            if any(n < 2 for n in counts):
                raise ValueError('invalid option count')
            quotas = {n:per_type*count//len(group) for n,count in counts.items()}
            for n in sorted(counts, key=lambda n:(-(per_type*counts[n]%len(group)),n))[:per_type-sum(quotas.values())]:
                quotas[n] += 1
            chosen = [r for n in sorted(counts) for r in uniform_subset(
                [r for r in group if len(r['options'])==n], quotas[n])]
            report[typ] = dict(axis='answer_letter_within_option_count', target_by_option_count=quotas,
                              benchmark_option_counts=distributions.get(typ,{}).get('n_options',{}))
        else:
            chosen, old = legacy(group, distributions, per_type)
            report.update(old)
            if typ.startswith('object_rel_direction') and chosen:
                # Enforce uniform letters while preserving each content's quota as an upper bound.
                chosen = uniform_subset(chosen, per_type)
                report[typ]['axis'] = 'answer_content_then_uniform_letter'
                actual = Counter(r['answer_content'] for r in chosen)
                report[typ]['shortage'] = {k:max(0,v-actual[k]) for k,v in report[typ]['target'].items()}
        selected.extend(chosen)
        report[typ]['duplicates_removed'] = duplicates.get(typ,0)
        report[typ]['before'] = set_report(group)[typ]
        report[typ]['after'] = set_report(chosen).get(typ,dict(rows=0,unique_questions=0,letters={}))
    return selected, report
