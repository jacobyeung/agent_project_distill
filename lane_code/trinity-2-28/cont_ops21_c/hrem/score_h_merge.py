"""Merge authenticated H parent/remainder publications and score paired camera wording."""
import argparse
import json
from pathlib import Path
import score_base_h as base
from return_tools_h import segment, require, subset
from fetch_validation import digest

def merged(spec,work):
    work=Path(work)
    if 'parent' not in spec:
        rows,meta,info=segment(spec,work/'complete')
        require('remainder' not in info['manifest'] and len(rows)==900,'Expected complete 900-item H return')
        return rows,dict(segments=[meta]),info
    left,lm,li=segment(spec['parent'],work/'parent')
    right,rm,ri=segment(spec['remainder'],work/'remainder')
    require('remainder' not in li['manifest'] and 'remainder' in ri['manifest'],'Expected full parent and remainder')
    require(not lm['publication']['complete'] and rm['publication']['complete'],'Need partial parent and complete remainder')
    prov=dict(parent_plan=li['plan'],parent_token=li['token'],parent_items_sha256=li['items_sha256'],
        partial_archive_sha256=digest(spec['parent']['archive']),partial_return_token=lm['publication']['token'],export_binding=li['export_binding'])
    done=[i['id'] for i in li['manifest']['items'] if i['id'] in left]
    require(ri['manifest']==subset(li['manifest'],done,prov),'Remainder differs from exact parent complement')
    require(not set(left)&set(right),'Overlapping segment IDs')
    require(li['binding']==ri['binding'] and li['serving_pins']==ri['serving_pins'],'Mixed export/serving identity')
    require(lm['settings']==rm['settings'],'Mixed settings')
    # Membership and mapping hashes change with the subset; serving identities cannot.
    ignore={'items_sha256','item_set_sha256','count','mapping_sha256'}
    require({k:v for k,v in lm['binding'].items() if k not in ignore}=={k:v for k,v in rm['binding'].items() if k not in ignore},'Mixed journal serving identity')
    rows=dict(left);rows.update(right)
    require(set(rows)==set(i['id'] for i in li['manifest']['items']) and len(rows)==900,'Incomplete merged coverage')
    return rows,dict(segments=[lm,rm],completed=900,pairs=450),li

def score(spec,work,other=None):
    rows,meta,info=merged(spec,Path(work)/'current');m=info['manifest']
    twins=json.loads(info['payload']['items/HELDOUT_CAMERA_TWINS.json'])['twins']
    result=dict(meta=meta,cells={k:base.metrics(rows,v) for k,v in base.cells(m,twins).items()},reworded_minus_original=base.paired(rows,m,twins))
    if other:
        old,om,oi=merged(other,Path(work)/'other')
        require(info['export_binding']['step']!=oi['export_binding']['step'],'Step comparison requires distinct steps')
        require(info['serving_pins']==oi['serving_pins'],'Step comparison serving pins differ')
        result.update(other_meta=om,current_minus_other=base.compare(rows,old,m,twins))
    result.update(bootstrap=dict(draws=10000,seed=17,unit='room_key',interval=.95),
        answer_source='patched scorers.accuracy task_accuracy: sealed output.scores.answer, max_calls=0',
        denominator='Completed items for cell rates; complete pairs for differences; missing IDs reported')
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('spec','work','out'):p.add_argument('--'+n,required=True)
    p.add_argument('--other',help='JSON specification for another merged or complete return')
    a=p.parse_args();spec=json.loads(Path(a.spec).read_text());other=json.loads(Path(a.other).read_text()) if a.other else None
    result=score(spec,a.work,other)
    with Path(a.out).open('x') as f:json.dump(result,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
if __name__=='__main__':main()
