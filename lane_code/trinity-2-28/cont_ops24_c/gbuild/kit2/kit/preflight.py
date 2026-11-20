"""Fail-closed handoff; this incomplete kit cannot start GPU work."""
import argparse
import gzip
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--gpu',type=int,required=True)
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('manifest',nargs='?',default='INPUTS_REQUIRED.json')
    args=p.parse_args()
    root=Path(__file__).resolve().parent
    manifest=json.loads((root/args.manifest).read_text())
    tasks=json.loads((root/'tasks.json').read_text())
    first=tasks[0]
    checks={}
    for n in (32,64,96):
        indices=first['ground_indices'][str(n)]
        checks[str(n)]=dict(unique=len(set(indices)),ordered=indices==sorted(indices),
                            preserves_answer_frames=set(first['answer_indices'])<=set(indices))
    with gzip.open(root.parent/'work/step544.jsonl.gz','rt') as f:
        row=next(json.loads(x) for x in f if json.loads(x)['item_id']==first['item_id'])
    calls=[]
    for c in row['arms']['tower']['tool_calls']:
        if c.get('family')!='ground':continue
        d=c.get('stage1') or {}
        candidates=d.get('candidates',[])
        k=d.get('chosen_index')
        replay=max(range(len(candidates)),key=lambda i:candidates[i]['logit']) if candidates else -1
        calls.append(dict(call=c['call'],raw_proposals_per_frame=d.get('sam3',{}).get('kept_per_frame'),
                          linked_candidates=d.get('linked_candidates'),chosen=k,
                          logged_argmax_replay=replay,
                          logged_argmax_matches=(k==replay),raw_masks_available=False,
                          gt_visibility_available=False))
    out=dict(status='BLOCKED_BEFORE_RGB_AND_PROPOSAL_INFERENCE',gpu_requested=args.gpu,
             gpu_used=False,capture=first['scene'],item_id=first['item_id'],
             task_plan_checks=checks,baseline_call_replay=calls,
             missing=manifest['missing'],
             gpu_adapter_implemented=False,
             note='This dry run validates metadata and logged selection only; no real image was decoded.')
    destination=root.parent/'work/first_capture_dry.json'
    destination.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
    return 0 if args.dry_run else 2


if __name__=='__main__':
    raise SystemExit(main())
