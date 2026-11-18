"""Authenticate one room return, pair rows to fixed keys, and recompute official MRA."""
import argparse,hashlib,json,re,statistics,sys
from pathlib import Path
O=Path(__file__).resolve().parent;P=O/'src'
sys.path[:0]=[str(P/'b'),str(P/'tree'),str(P)]
import e2e_reader
from h1eval.items import load_manifest,sha
from h1eval import scorers
from h1eval.cli import code_hash
from orchard_h10.common import canonical
from h1eval.h10.parity_adapter import reader_code_hash
from h1eval.h10 import parity_adapter
from unpack_return import validate_journals

def score_return(root,allow_fixture=False):
    root=Path(root);validate_journals(root)
    manifest=load_manifest(P/'items/room134.json');items={r['id']:r for r in manifest['items']}
    public=json.loads((O/'package/0.json').read_text());inputs=json.loads((O/'inputs_tower.json').read_text())
    identity=json.loads((root/'metadata/IDENTITY.json').read_text())
    import tower_sequence as sequence
    expected=dict(plan=public['plan_sha256'],inputs=canonical({k:v for k,v in inputs.items() if k!='resume'}),operator_sha256=sha(O/'tower_sequence.py'),cards=1,reads=sequence.descriptors(P),schedule=json.loads(json.dumps(sequence.SCHEDULE)))
    if identity!=expected:raise ValueError('Return identity differs')
    policies=dict(stage1_select_rule='candidates_argmax',perception_memo='on',perception_memo_modules=['g3t'],perception_memo_verify_ids=[],save_own_depth=False,types=['room_size_estimation'])
    hashes=dict(item_set_sha256=manifest['item_set_sha256'],items_sha256=sha(P/'items/room134.json'),reader_sha256=code_hash(P/'b/e2e_reader'),evaluator_code_sha256=code_hash(),parity_code_sha256=reader_code_hash(P/'b'),maker_sha256=sha(Path(parity_adapter.__file__)))
    rows={};sources=[];binding_identity=None
    journals=sorted(root.glob('metadata/reads/*/metadata/journals/*/*/items.jsonl'))
    for path in journals:
        if path.relative_to(root).parts[2:6]!=('0','metadata','journals','4') or path.parent.name!='0':raise ValueError('Unplanned journal')
        env=json.loads((path.parent/'environment.json').read_text());b=env['binding']
        if b.get('fixture') and not allow_fixture:raise ValueError('Fixture return cannot be scored as a real read')
        for k,v in {**policies,**hashes,'arms':['tower'],'modes':[{'name':'none'}],'lineage':'SFT','step':544,'count':134,'ids':list(items)}.items():
            if b.get(k)!=v:raise ValueError('Journal binding differs: '+k)
        for k,v in policies.items():
            if env['settings'].get(k)!=v:raise ValueError('Settings differ: '+k)
        if b['settings_sha256']!=canonical(env['settings']):raise ValueError('Settings digest differs')
        current={k:b.get(k) for k in ('export_sha256','artifact_manifest_sha256','settings_sha256','mapping_sha256')}
        if binding_identity is not None and current!=binding_identity:raise ValueError('Mixed journals')
        binding_identity=current
        sources.append(dict(path=str(path.relative_to(root)),sha256=sha(path)))
        text=path.read_text()
        if text and not text.endswith('\n'):raise ValueError('Incomplete JSONL tail')
        for line in text.splitlines():
            r=json.loads(line);key=r['id']
            if key in rows or key not in items:raise ValueError('Duplicate or unknown item key')
            if (r.get('complete') is not True or r.get('arm')!='tower' or r.get('mode')!='none'
                or r.get('type')!='room_size_estimation' or r.get('room_key')!=items[key]['room_key']):raise ValueError('Row pairing differs')
            out=r['output'];measurement=scorers.benchmark(out,items[key])
            # Match the parity reader's think-close and strict-no-answer rule, but score the
            # item's ground_truth rather than trusting a serialized native answer score.
            mra=measurement['score']
            if out.get('strict_no_answer') or not re.search(r'</think\s*>',out.get('text',''),re.I):mra=0.0
            # Job 1 (tower_pair.py:74) and the H1 evaluator score the native answer label; report both labels.
            mra_answer=scorers.accuracy(out,items[key])['task_accuracy']
            calls=scorers.records(out)
            malformed=sum('malformed' in (str(c.get('response',''))+' '+str(c.get('code',''))+' '+str(c.get('error',''))).lower() for c in calls)
            rows[key]=dict(id=key,room_key=r['room_key'],mra=mra,mra_answer=mra_answer,finish=out['finish'],capped=out['finish'] in ('max_calls','max_new_tokens','length'),malformed_calls=malformed,call_count=len(calls),parse_failed=measurement.get('parse_failed',False))
    sets={}
    for name,keys in {**manifest['sets'],'all':list(items)}.items():
        available=[rows[k] for k in keys if k in rows]
        sets[name]=dict(expected=len(keys),completed=len(available),complete=len(available)==len(keys),mra=statistics.mean(r['mra'] for r in available) if available else None,mra_answer=statistics.mean(r['mra_answer'] for r in available) if available else None,capped_reads=sum(r['capped'] for r in available),malformed_calls=sum(r['malformed_calls'] for r in available),missing=sorted(set(keys)-set(rows)))
    return dict(token=public['token'],plan_sha256=public['plan_sha256'],item_set_sha256=manifest['item_set_sha256'],labels=dict(mra='ground_truth (released label)',mra_answer='native answer label, the job-1 tower_pair.py and H1 evaluator path; leg R1 room gate uses this one'),development_only=True,fitting_permitted=False,synthetic=allow_fixture,sets=sets,per_item=[rows[k] for k in sorted(rows)],sources=sources,malformed_definition='Calls whose recorded response, code, or error contains malformed; unserved calls without diagnostics are not classified as malformed.',score_definition='Official VSI MRA against item ground_truth; strict-no-answer and absent think-close score zero. Missing rows stay missing and do not enter available MRA.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--return-root',required=True);p.add_argument('--out',required=True);p.add_argument('--allow-fixture',action='store_true');a=p.parse_args()
    result=score_return(a.return_root,a.allow_fixture);dest=Path(a.out);dest.mkdir(parents=True,exist_ok=True)
    (dest/'scores.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    (dest/'per_item.jsonl').write_text(''.join(json.dumps(r,allow_nan=False)+'\n' for r in result['per_item']))
    print(json.dumps(result['sets'],sort_keys=True))
if __name__=='__main__':main()
