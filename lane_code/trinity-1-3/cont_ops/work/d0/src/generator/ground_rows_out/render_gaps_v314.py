"""Admission and independent replay for the four added scene question types."""
import copy
import hashlib
import re
from collections import Counter
from functools import lru_cache
from derivgen import ground_v312 as G, ground_v313 as I
from derivgen.gaps_v314 import NEW_TYPES, COUNT_TYPES, circular_error, comparison, question, validate_computation
from derivgen.ground_v312_io import operands
from derivgen.ground_v312_quality import normalized, shuffled_item, question_identity
from derivgen.ground_v313_tokens import gate_positions


def instance_provider(clip):
    # Exact category resolution follows the same adapter as the original scene renderer.
    class Provider(I.GTInstances):
        def labels_for(self, name):
            return {normalized(x) for x in clip.programs.T.match_labels(name,clip.geo.labels)}
    return Provider(clip)


def session(backend,clip,typ):
    if typ in COUNT_TYPES:
        return I.Session(backend,clip.geo,clip.masks,instances=instance_provider(clip),multi_instance=True)
    return G.Session(backend,clip.geo,clip.masks)


def independent_label(item,clip,P):
    r,t=item['roles'],item['type']
    def ids(n):
        labels=P.T.match_labels(n,clip.geo.labels)
        return [int(i) for i,l in zip(clip.geo.ids,clip.geo.labels) if l in labels]
    if t == 'object_counting':
        value=str(len(ids(r['obj'])))
        return G.letter(item['options'],value) if item['options'] else value
    if t == 'relative_count':
        return comparison(len(ids(r['a'])),len(ids(r['b'])),item['options'])[0]
    points=[clip.geo.obb[ids(r[k])[0]]['centroid'] for k in ('stand','face','query')]
    theta=P.T.floor_angle(*points)[0]
    if t == 'absolute_direction_object':
        return (theta if r['ccw'] else -theta)%360
    return G.letter(item['options'],P.T.direction_label(t,theta))


def prepare(source,clip,P,backend,token_count,entry):
    item=copy.deepcopy(source);t=item['type'];names=operands(item)
    if (item['frame_indices'] != entry['frame_indices'] or
        item['source_provenance']['canonical'] != entry['canonical'] or
        item['authority']['gt']['sha256'] != entry['gt']['sha256']):
        raise G.RowRefusal('scene_frame_or_gt_binding_mismatch')
    if item['question'] != question(item):
        raise G.RowRefusal('question_template_mismatch')
    ids={}
    for n in names:
        labels=P.T.match_labels(n,clip.geo.labels)
        ids[n]=[int(i) for i,l in zip(clip.geo.ids,clip.geo.labels) if l in labels]
        if not ids[n]: raise G.RowRefusal('missing_name')
        if normalized(n) not in {normalized(l) for l in labels}:
            raise G.RowRefusal('unresolved_qualified_name')
    if t not in COUNT_TYPES:
        clip.validate_operands(item)
    else:
        item['expected_instance_ids']=ids
        from derivgen.instance_policy314 import valid_mask
        for values in ids.values():
            for iid in values:
                if not any(clip.geo.has(k) and valid_mask(clip.geo.inst[k-1] == iid) for k in range(1,33)):
                    raise G.RowRefusal('instance_not_visible')
    native=independent_label(item,clip,P)
    item['native_independent_label']=native
    item['source_gt_answer']=item['gt_answer']
    # Never replace a pool answer with the native answer to manufacture agreement.
    equal=(circular_error(native,item['gt_answer'])<=15 if t=='absolute_direction_object'
           else str(native)==str(item['gt_answer']))
    if not equal: raise G.RowRefusal('native_label_disagrees_pool')
    item['gt_authority']=dict(item['authority'],native_independent_label=native)
    item=shuffled_item(item)
    if t in ('relative_count','absolute_direction_object'):
        item['question']=question(item)
    s=session(backend,clip,t)
    from derivgen.programs_v314 import render
    row=render(item,s,token_count)
    row.update(candidate_id=row.get('candidate_id'),scene=item['scene'],canonical=entry['canonical'],
        roles=item['roles'],frame_indices=item['frame_indices'],gt_answer=item['gt_answer'],
        source_gt_answer=item['source_gt_answer'],native_independent_label=native,
        gt_authority=item['gt_authority'],source_join=item['source_join'],
        question_identity=question_identity(item),option_shuffle=item.get('option_shuffle'),
        option_letter_map=item.get('option_letter_map',{}),diagnostic_only=True,training_admitted=False,
        gt_accepted=True,gt_agrees=True,selection_refusal=None,geometry_source='gt',mask_source='gt',
        scene_gt_sha256=entry['gt']['sha256'],not_seen=False,simulated_misses=[],spec_version='3.14',
        trace_program_version='3.14')
    return row,item


def check_row(row,item,clip,backend,tokenizer,templates,dev,devrooms):
    from render_full import room
    from test_v312_benchmark import expected_question
    from orchard_ground_adapter import pack,validate
    c=Counter()
    if row['frame_indices'] != item['frame_indices']:
        raise ValueError('row frame binding mismatch')
    G.replay(row,session(backend,clip,row['type']));c['exact_replay']+=1
    validate_computation(row);c['printed_computation']+=1
    if row['question'] != expected_question(row,templates): raise ValueError('question template mismatch')
    c['templates']+=1
    source=item['source_join'];opts=G.option_map(source['options'])
    if opts:
        order=sorted(opts,key=lambda k:hashlib.sha256((row['qid']+'\0'+k).encode()).digest())
        mapping={k:chr(65+i) for i,k in enumerate(order)}
        if (row['options'] != [f'{chr(65+i)}. {opts[k]}' for i,k in enumerate(order)] or
            row['option_letter_map'] != mapping or str(row['gt_answer']) != mapping[str(source['gt_answer'])]):
            raise ValueError('option shuffle or label map mismatch')
        if G.option_map(row['options'])[row['answer']] != row['answer_content']:
            raise ValueError('option content mismatch')
    c['shuffles']+=1
    equal=(circular_error(row['answer'],row['gt_answer'])<=15 if row['type']=='absolute_direction_object'
           else str(row['answer'])==str(row['gt_answer']))
    if not equal: raise ValueError('label equality failed')
    c['label_equality']+=1
    canonical=item['source_provenance']['canonical']
    physical=item['source_provenance'].get('physical_group',room(canonical))
    if canonical in dev or room(canonical) in devrooms or physical in devrooms:
        raise ValueError('dev scan/room leakage')
    if (row['not_seen'] or row['simulated_misses'] or not row['gt_accepted'] or
        not row['gt_agrees'] or row['training_admitted']): raise ValueError('membership flag mismatch')
    c['flags_and_dev_exclusion']+=1
    if (gate_positions(tokenizer,row['suffix'])!=row['mdg_gate_token_positions'] or
        row['suffix_tokens']!=len(tokenizer.encode(row['suffix'],add_special_tokens=False).ids) or
        row['suffix_tokens']>5000): raise ValueError('token count or gate positions mismatch')
    c['tokens_and_gate_positions']+=1
    return c
