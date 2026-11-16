"""Authenticate source, receipt, arm and reconstructed scoring text before budget merge."""
from copy import deepcopy
import json
from pathlib import Path
from budget import BUDGETS, Journal, source_lines
from budget_admission import BudgetContext, POLICY
from data import tasks_for
from evalpath.items import digest
from token_audit import load_tokenizer


def merge_budgets(cfg, cell, attempt, *, tokenizer=None):
    from merge import merge
    tokenizer=tokenizer or load_tokenizer(cfg)
    out=Path(cfg['output'])
    tasks={t['benchmark']+':'+t['example_id']:t for s in cfg['datasets']
           if s['benchmark'] in cfg['cells'][cell]['benchmarks'] for t in tasks_for(s,cfg['roots'])}
    for budget in BUDGETS:
        context=BudgetContext(cfg,cell,budget,tokenizer)
        derived=deepcopy(cfg)
        derived['binding']=context.arm_binding
        derived['output']=str(out/f'budget_{budget}')
        derived['budget_arm']=dict(arm=f'B{budget}',budget=budget,frames=32,layout='duplicate',**POLICY)
        directory=Path(derived['output'])/str(cell)
        directory.mkdir(parents=True,exist_ok=True)
        all_rows,all_meta,all_records={},{},{}
        annotations=[]
        for rank in range(cfg['gpus']):
            sources=source_lines(out/str(cell)/f'g{rank}.jsonl',strict=True)
            arm_path=out/str(cell)/f'budget_{budget}.g{rank}.jsonl'
            if arm_path.with_suffix('.annotation.json').exists():
                from budget_annotation import verify_budget_annotation
                annotations.append(verify_budget_annotation(arm_path,cfg,cell,budget,
                    out/str(cell)/f'g{rank}.jsonl',tokenizer))
            journal=Journal(arm_path,context.arm_binding,sources)
            if set(journal.done)!=set(sources):raise ValueError('Budget merge count mismatch')
            projected_rows=[]
            for key,(row,raw) in journal.done.items():
                if key not in tasks:raise ValueError('Unexpected budget membership')
                meta=journal.receipts[key][0]
                projected=context.add(sources[key][0],row,raw,meta,tasks[key])
                if key in all_records:
                    if all_records[key]!=row or all_meta[key]!=meta:
                        raise ValueError('Conflicting complete rows: '+key)
                    continue
                all_rows[key],all_meta[key],all_records[key]=raw,meta,row
                projected_rows.append(projected)
            with (directory/f'g{rank}.jsonl').open('w') as stream:
                for row in projected_rows:stream.write(json.dumps(row,allow_nan=False)+'\n')
            parity=out/str(cell)/f'p{rank}_{attempt}.json'
            if parity.exists():(directory/parity.name).write_bytes(parity.read_bytes())
        (Path(derived['output'])/'request.json').write_text(json.dumps(derived,indent=2)+'\n')
        summary=merge(derived,cell,attempt,tokenizer=tokenizer,budget_context=context)
        if any(s['completed']!=s['expected'] or s['missing'] for s in summary['benchmarks'].values()):
            raise ValueError('Budget merge expected count mismatch')
        if annotations:summary['annotations']=annotations
        summary['derivation']=dict(total=len(all_meta),per_type={
            typ:{flag:sum(bool(meta.get(flag)) for key,meta in all_meta.items() if all_records[key]['question_type']==typ)
                 for flag in ('forced_close','stopped_unclosed','derivation_error')}
            for typ in sorted({row['question_type'] for row in all_records.values()})})
        (directory/f'summary_{attempt}.json').write_text(json.dumps(summary,indent=1)+'\n')
        (out/str(cell)/f'budget_{budget}.jsonl').write_text(''.join(all_rows[k]+'\n' for k in sorted(all_rows)))
        (out/str(cell)/f'budget_{budget}.meta.jsonl').write_text(''.join(json.dumps(all_meta[k])+'\n' for k in sorted(all_meta)))
