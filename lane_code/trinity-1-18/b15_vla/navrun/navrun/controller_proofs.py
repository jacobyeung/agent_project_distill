"""CPU controller ablation and the frozen Open-Nav rand100 harness check."""
from .config import Config
from .episodes import load_split, load_gt
from .io import read_json, write_json
from .lists import verify_manifest, freeze_rand100
from .metrics import aggregate
from .paths import OUT, RAND100
from .policies import (OracleClickPolicy, OracleGTClickPolicy, OraclePolicy,
                       RandomPolicy, ForwardPolicy, InstructionPolicy)
from .runner import Runner, execution_sha256
from .sim import Environment


def summarize(results):
    return dict(aggregate(results),
                step_caps=sum(r['termination']=='step_cap' for r in results),
                stationary_tails=sum(r['stationary_tail'] for r in results),
                capped_stationary_tails=sum(r['stationary_tail'] and r['termination']=='step_cap'
                                           for r in results))


def main():
    val=load_split('val_unseen')
    refs={k:v['locations'] for k,v in load_gt('val_unseen',episodes=val).items()}
    small=verify_manifest(read_json(OUT/'lists/val_unseen_600_s0.json'),val)
    rand=freeze_rand100(RAND100,val,OUT/'lists/rand100.json')
    stats=read_json(OUT/'tables/training_statistics.json')
    cells={}; comparisons={}
    fingerprint=execution_sha256()
    for name in ('oracle-click','oracle-gt-click'):
        # These tables preserve the published v1 streams for a full parity check.
        prior=read_json(OUT/'tables'/f'{name}_val_unseen_600_s0.json')
        by_id={r['episode_id']:r for r in prior['results']}
        for version in ('v1','v2'):
            cfg=Config(output_format='click',controller_version=version)
            env=Environment(cfg)
            policy=OracleClickPolicy(env) if name=='oracle-click' else OracleGTClickPolicy(env,refs)
            key=f'{name}_{version}_val_unseen_600_s0'
            try:
                results=Runner(env).evaluate(small,policy,OUT/'journals'/f'controller_{fingerprint[:12]}_{key}.jsonl',refs,OUT/'STOP')
            finally:
                env.close()
            if len(results)!=600:
                raise RuntimeError('Evaluation interrupted: '+key)
            if version=='v1':
                assert all(r['actions']==by_id[r['episode_id']]['actions'] for r in results)
                for metric in ('SR','SPL','OSR','nDTW','SDTW'):
                    assert all(r[metric]==by_id[r['episode_id']][metric] for r in results),metric
            summary=summarize(results)
            write_json(OUT/'tables'/f'{key}.json',dict(summary=summary,results=results,
                       config=cfg.to_dict(),execution_sha256=fingerprint))
            cells[key]=summary
            print(key,summary,flush=True)
        a=cells[f'{name}_v1_val_unseen_600_s0']; b=cells[f'{name}_v2_val_unseen_600_s0']
        comparisons[name]={metric:b[metric]-a[metric] for metric in
                          ('SR','SPL','OSR','nDTW','SDTW','step_caps','stationary_tails')}
    for name,cls in (('oracle',OraclePolicy),('random',RandomPolicy),
                     ('forward-only',ForwardPolicy),('instruction-prior',InstructionPolicy)):
        cfg=Config(output_format='text'); env=Environment(cfg)
        policy=cls(env) if name=='oracle' else cls(stats)
        key=f'{name}_rand100'
        try:
            results=Runner(env).evaluate(rand,policy,OUT/'journals'/f'controller_{fingerprint[:12]}_{key}.jsonl',refs,OUT/'STOP')
        finally:
            env.close()
        if len(results)!=100:
            raise RuntimeError('Evaluation interrupted: '+key)
        summary=summarize(results)
        write_json(OUT/'tables'/f'{key}.json',dict(summary=summary,results=results,
                   config=cfg.to_dict(),execution_sha256=fingerprint))
        cells[key]=summary
        print(key,summary,flush=True)
    write_json(OUT/'tables/controller_comparison.json',dict(cells=cells,v2_minus_v1=comparisons,
               v1_exact_action_replays=1200,execution_sha256=fingerprint,
               stationary_definition='At least 20 decisions; every last-20 decision position within 1e-4 m of final decision position'))


if __name__=='__main__': main()
