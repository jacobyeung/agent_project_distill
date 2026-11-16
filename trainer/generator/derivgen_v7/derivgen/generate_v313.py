"""Bounded serial GT review builder. All outputs remain outside training admission."""
import argparse
import json
from pathlib import Path
from . import ground_v312 as old
from .ground_v313 import Session, GTInstances, render, balance_gap_positions
from .ground_v312_io import GTClip, reference, checked, agrees, sha
from .ground_v312_quality import shuffled_item
from .ground_v313_tokens import tokenizer_for_rows, gate_positions
from .ground_v313_pack import training_row
from .box_v313 import AnnotationBoxProvider, RULE


def build(config, output, *, legacy=False):
    c=json.loads(Path(config).read_text());out=Path(output);out.mkdir(parents=True,exist_ok=False)
    backend=old.load_backend(checked(c['backend']))
    scenes=json.loads(checked(c['scenes']).read_text())
    tokenizer=tokenizer_for_rows(checked(c['tokenizer']),keypoint_calls=False)
    count=lambda s:len(tokenizer.encode(s,add_special_tokens=False).ids)
    P,M,_=reference(c['rkit_root'])
    rows=[];refusals=[];clips={}
    with checked(c['items']).open() as f:
        for i,line in enumerate(f):
            if i >= c.get('max_rows',500):
                break
            item=json.loads(line)
            try:
                if item['scene'] not in clips:
                    e=scenes[item['scene']]
                    clips[item['scene']]=GTClip(checked(e['gt']),e['frame_indices'],P,M)
                clip=clips[item['scene']]
                if item['frame_indices'] != scenes[item['scene']]['frame_indices']:
                    raise old.RowRefusal('exact_frame_mismatch')
                if item['type'] in old.TYPES:
                    parsed=old.parse_roles(item,P.T)
                    if item.get('roles',parsed) != parsed:
                        raise old.RowRefusal('source_role_mismatch')
                    item['roles']=parsed
                    clip.validate_operands(item)
                elif item['type'] not in ('object_counting','object_appearance_order') or legacy:
                    raise old.RowRefusal('unsupported_type')
                elif item.get('question_rule') != 'observed_eligible_frames':
                    raise old.RowRefusal('instance_question_rule_unverified')
                if not legacy and item['type'] in ('object_abs_distance','object_rel_distance'):
                    item['target_distance_rule']=RULE
                    names=([item['roles']['a'],item['roles']['b']] if item['type']=='object_abs_distance' else
                           [item['roles']['target'],*item['roles']['cands']])
                    from .ground_v312_quality import normalized
                    item['independent_ordered_boxes']=[dict(name=n, **{k:__import__('numpy').asarray(v).tolist()
                        for k,v in clip.geo.obb[next(int(i) for i,l in zip(clip.geo.ids,clip.geo.labels)
                            if normalized(l)==normalized(n))].items()}) for n in names]
                item=shuffled_item(item)
                if item.get('independent_ordered_boxes') and item['type']=='object_rel_distance':
                    by_name={b['name']:b for b in item['independent_ordered_boxes']}
                    item['independent_ordered_boxes']=[by_name[n] for n in [item['roles']['target'],*item['roles']['cands']]]
                def session():
                    return Session(backend,clip.geo,clip.masks,enabled=not legacy,instances=GTInstances(clip),
                                   box_provider=AnnotationBoxProvider())
                row=render(item,session(),count)
                row.update(scene=item['scene'],frame_indices=item['frame_indices'],roles=item['roles'],
                           gt_agrees=agrees(row['answer'],item['gt_answer'],item['type']),
                           gt_authority=item.get('gt_authority'),training_admitted=False)
                row['mdg_gate_token_positions'] = gate_positions(tokenizer, row['suffix'])
                row['routing_and_main_adapters'] = 'closed'
                if not row['gt_agrees'] or not row['gt_authority']:
                    raise old.RowRefusal('independent_gt_disagreement_or_missing')
                old.replay(row,session())
                rows.append(row)
            except (old.RowRefusal,ValueError) as exc:
                refusals.append(dict(qid=item['qid'],reason=str(exc)))
    relative=[r for r in rows if r['type']=='object_rel_distance']
    balanced,position_report=balance_gap_positions(relative,c.get('max_rows',500)) if relative else ([],{})
    for name,values in [('rows',rows),('relative_balanced',balanced),('refusals',refusals)]:
        (out/(name+'.jsonl')).write_text(''.join(json.dumps(r,allow_nan=False)+'\n' for r in values))
    if not legacy:
        (out/'packed_review_rows.jsonl').write_text(''.join(json.dumps(training_row(r))+'\n' for r in rows))
    report=dict(rows=len(rows),refusals=len(refusals),position_report=position_report,
                training_admitted=False,config_sha256=sha(config),legacy=legacy,
                remaining_gates=['E3','production provenance','benchmark count/content histogram','consumer parity'])
    (out/'RECEIPT.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True)
    p.add_argument('--legacy',action='store_true');a=p.parse_args()
    print(json.dumps(build(a.config,a.output,legacy=a.legacy)))

if __name__=='__main__':main()
