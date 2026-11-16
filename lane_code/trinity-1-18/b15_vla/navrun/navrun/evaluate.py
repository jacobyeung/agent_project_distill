"""Evaluate an explicitly supplied policy factory; no model is downloaded or loaded implicitly."""
import argparse
import dataclasses
import importlib
from .config import load_arm
from .episodes import load_split, load_gt
from .io import read_json, write_json
from .lists import verify_manifest, manifest
from .audit import split_audit, audit_manifests
from .runner import Runner
from .sim import Environment
from .metrics import aggregate

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--config',required=True);p.add_argument('--list',required=True)
    p.add_argument('--policy',required=True,help='local module:factory; factory(Config) returns a policy')
    p.add_argument('--journal',required=True);p.add_argument('--output',required=True)
    p.add_argument('--render',action='store_true');p.add_argument('--allow-control',action='store_true')
    p.add_argument('--stop-file')
    for key in ('student','g3t','sam3'):p.add_argument('--'+key)
    a=p.parse_args();_,cfg=load_arm(a.config,a.allow_control)
    cfg=dataclasses.replace(cfg,render=a.render)
    val=load_split('val_unseen');split_audit(load_split('train'),val,load_split('test'))
    episodes=verify_manifest(read_json(a.list),val)
    provenance=audit_manifests(episodes,vars(a))
    allowed=set(provenance['retained_ids']);episodes=[e for e in episodes if e.episode_id in allowed]
    write_json(a.output+'.list.json',manifest('frozen_evaluation',episodes,provenance=provenance))
    module,name=a.policy.split(':',1);policy=getattr(importlib.import_module(module),name)(cfg)
    env=Environment(cfg)
    refs={k:v['locations'] for k,v in load_gt('val_unseen',episodes=episodes).items()}
    try:results=Runner(env,cfg).evaluate(episodes,policy,a.journal,references=refs,stop_file=a.stop_file)
    finally:env.close()
    write_json(a.output,dict(summary=aggregate(results),results=results,provenance=provenance,
                             complete=len(results)==len(episodes)))
if __name__=='__main__':main()
