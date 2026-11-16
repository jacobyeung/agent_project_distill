"""Reproducible CPU proof commands. Every command runs synchronously."""
import argparse
import time
from collections import Counter
from .paths import OUT
from .io import read_json, write_json
from .episodes import load_split, load_ie, load_gt
from .lists import balanced, subsets, manifest, select_pairs, verify_manifest
from .audit import split_audit, audit_manifests
from .rows import prepare_tracks, replay_check, build_rows, location_replay_check
from .policies import action_statistics, RandomPolicy, ForwardPolicy, InstructionPolicy, OraclePolicy, OracleClickPolicy, OracleGTClickPolicy
from .sim import Environment
from .config import Config
from .runner import Runner
from .metrics import aggregate
from .r2rie import pair_drop

def make_lists():
    train, val, test = load_split('train'), load_split('val_unseen'), load_split('test')
    audit = split_audit(train, val, test)
    audit['provenance'] = audit_manifests(val, {})
    write_json(OUT/'tables/scene_audit.json', audit)
    small, large = subsets(train)
    sets = {'val_unseen_full_1839':val, 'val_unseen_600_s0':balanced(val,600),
            'train_1pct_s0':small, 'train_10pct_s0':large}
    for name, eps in sets.items():
        write_json(OUT/'lists'/f'{name}.json',manifest(name,eps,seed=0))
    _, _, pairs = load_ie()
    selected = select_pairs(pairs)
    paired_eps = [e for p in selected for e in (p['clean'],p['perturbed'])]
    write_json(OUT/'lists/r2rie_direction_300.json',manifest('r2rie_direction_300',paired_eps,seed=0,
               pairs=[dict(clean=p['clean'].episode_id,perturbed=p['perturbed'].episode_id) for p in selected]))
    write_json(OUT/'lists/rand100.json',dict(status='BLOCKED_IDS_MISSING',required='MIP OpenNav-100 position/episode_id/scene/trajectory_id records'))
    print({k:len(v) for k,v in sets.items()},flush=True)

def tracks_and_statistics():
    train = load_split('train')
    tracks = prepare_tracks(train, OUT/'tables/training_tracks.json')
    write_json(OUT/'tables/training_statistics.json', action_statistics(tracks))
    write_json(OUT/'tables/replay.json', replay_check(train, tracks))
    subsets = {name:set(read_json(OUT/'lists'/f'{name}.json')['ids'])
               for name in ('train_1pct_s0','train_10pct_s0')}
    write_json(OUT/'tables/location_replay.json', location_replay_check(train, tracks, subsets))
    return train, tracks

def plans():
    start=time.monotonic();train,tracks=tracks_and_statistics()
    small = verify_manifest(read_json(OUT/'lists/train_1pct_s0.json'),train)
    large = verify_manifest(read_json(OUT/'lists/train_10pct_s0.json'),train)
    result=build_rows(large,tracks,OUT/'rows',train,load_split('val_unseen'),load_split('test'),
                      nested_ids=[e.episode_id for e in small])
    result['wall_seconds']=time.monotonic()-start
    write_json(OUT/'tables/subset_plans.json',result)
    print({k:v for k,v in result.items() if k not in ('per_episode','audit')},flush=True)

def evaluations(only=None):
    val=load_split('val_unseen');ie,ie_gt,pairs=load_ie()
    split_audit(load_split('train'),val,load_split('test'))
    full=verify_manifest(read_json(OUT/'lists/val_unseen_full_1839.json'),val)
    small=verify_manifest(read_json(OUT/'lists/val_unseen_600_s0.json'),val)
    paired_eps=verify_manifest(read_json(OUT/'lists/r2rie_direction_300.json'),ie)
    pair_ids={e.metadata['old_episode_id'] for e in paired_eps}
    selected=[p for k,p in pairs.items() if int(k) in pair_ids]
    refs_ie={k:v['locations'] for k,v in ie_gt.items()}
    refs_val={k:v['locations'] for k,v in load_gt('val_unseen',episodes=val).items()}
    stat=read_json(OUT/'tables/training_statistics.json') if (OUT/'tables/training_statistics.json').exists() else None
    table={}
    for name in ('oracle','random','forward-only','instruction-prior','oracle-click','oracle-gt-click'):
        if only and name not in only: continue
        fmt='click' if name in ('oracle-click','oracle-gt-click') else 'text'
        cfg=Config(output_format=fmt);env=Environment(cfg);runner=Runner(env,cfg)
        if name=='oracle': policy=OraclePolicy(env)
        elif name=='oracle-click':policy=OracleClickPolicy(env)
        elif name=='oracle-gt-click':policy=OracleGTClickPolicy(env,refs_val)
        else:
            if stat is None: raise ValueError('Run tracks first')
            policy={'random':RandomPolicy,'forward-only':ForwardPolicy,'instruction-prior':InstructionPolicy}[name](stat)
        cells=[('val_unseen_600_s0',small,refs_val)] if fmt=='click' else [('val_unseen_full_1839',full,refs_val),('r2rie_direction_300',paired_eps,refs_ie)]
        for cell,eps,refs in cells:
            start=time.monotonic()
            results=runner.evaluate(eps,policy,OUT/'journals'/f'official_gt_{name}_{cell}.jsonl',refs,OUT/'STOP')
            if len(results)!=len(eps):
                print('Stopped before completion', name,cell,len(results),flush=True);env.close();return
            summary=aggregate(results)
            summary['wall_seconds']=time.monotonic()-start
            summary['episode_compute_seconds']=sum(r['wall_seconds'] for r in results)
            summary['episodes_per_hour']=len(results)*3600/summary['episode_compute_seconds']
            summary['parse_failures']=sum(len(r['parse_events']) for r in results)
            summary['reference_sources']={'supplied_dense_gt':sum(e.episode_id in refs for e in eps),
                                          'sparse_reference_path':sum(e.episode_id not in refs for e in eps)}
            if cell=='r2rie_direction_300':summary['paired']=pair_drop(selected,results)
            write_json(OUT/'tables'/f'{name}_{cell}.json',dict(summary=summary,results=results))
            table[name+'_'+cell]=summary
            print(name,cell,summary,flush=True)
            if cell=='val_unseen_full_1839':
                by_id={r['episode_id']:r for r in results};subset=[by_id[e.episode_id] for e in small]
                subsummary=aggregate(subset)
                subsummary['reference_sources']={'supplied_dense_gt':len(subset),'sparse_reference_path':0}
                write_json(OUT/'tables'/f'{name}_val_unseen_600_s0.json',dict(summary=subsummary,results=subset))
                table[name+'_val_unseen_600_s0']=subsummary
        env.close()
    write_json(OUT/'tables'/('evaluation_summary_'+('-'.join(only) if only else 'all')+'.json'),table)

def main():
    p=argparse.ArgumentParser();p.add_argument('proof',choices=['lists','tracks','plans','eval','all'])
    p.add_argument('--policies',nargs='+');a=p.parse_args()
    if a.proof in ('lists','all'):make_lists()
    if a.proof in ('tracks','all'):tracks_and_statistics()
    if a.proof in ('plans','all'):plans()
    if a.proof in ('eval','all'):evaluations(a.policies)
if __name__=='__main__':main()
