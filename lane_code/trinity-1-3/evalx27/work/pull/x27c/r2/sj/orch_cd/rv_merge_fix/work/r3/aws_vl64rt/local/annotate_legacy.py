"""Write an authenticated copy; optionally merge it without changing historical bindings."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'evaluator'))
from provenance import annotate, request


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('request','source-archive','journal','output'):
        p.add_argument('--'+name, required=True, type=Path)
    p.add_argument('--cell', type=int, default=0)
    p.add_argument('--budget', type=int, choices=(2048,4096))
    p.add_argument('--on-journal', type=Path, help='Annotated ON journal beside the budget output')
    p.add_argument('--merge-attempt')
    p.add_argument('--tokenizer', type=Path)
    p.add_argument('--tokenizer-manifest', type=Path)
    a=p.parse_args()
    if a.budget is not None:
        if not a.on_journal or a.merge_attempt:
            p.error('--budget requires --on-journal; merge both arms after annotation')
        from budget_annotation import annotate_budget
        from token_audit import load_tokenizer
        cfg=request(a.request,a.source_archive)
        cfg=json.loads(json.dumps(cfg).replace('$Q',str(a.request.resolve().parent)))
        tokenizer=load_tokenizer(cfg,a.tokenizer,a.tokenizer_manifest)
        meta=annotate_budget(a.request,a.source_archive,a.journal,a.output,a.cell,
                             a.budget,a.on_journal,tokenizer)
    else:
        if a.on_journal:p.error('--on-journal requires --budget')
        meta=annotate(a.request,a.source_archive,a.journal,a.output,a.cell)
    if a.merge_attempt:
        if a.output.name!='g0.jsonl' or a.output.parent.name!=str(a.cell):
            raise ValueError('Merge output must be <result>/<cell>/g0.jsonl')
        cfg=request(a.request,a.source_archive)
        cfg=json.loads(json.dumps(cfg).replace('$Q',str(a.request.resolve().parent)))
        if cfg['gpus']!=1:raise ValueError('For multi-rank runs annotate each rank, then call merge')
        cfg['output']=str(a.output.resolve().parent.parent)
        from merge import merge
        kwargs={}
        if a.tokenizer:
            from token_audit import load_tokenizer
            kwargs['tokenizer']=load_tokenizer(cfg,a.tokenizer,a.tokenizer_manifest)
        result=merge(cfg,a.cell,a.merge_attempt,**kwargs)
        print(json.dumps(result,indent=1))
    else:print(json.dumps(meta,indent=1))

if __name__=='__main__':main()
