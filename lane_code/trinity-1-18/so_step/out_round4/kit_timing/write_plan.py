"""Write a bounded row plan at the pinned continuation step without loading a model."""
import argparse
import json
from pathlib import Path
import sys


def build_plan(run, cfg, receipt, start_step, steps):
    if type(start_step) is not int or start_step < 0 or not 1 <= steps <= 100:
        raise ValueError('Need a nonnegative continuation step and 1..100 audit updates')
    recipe = run.recipe_for(cfg)
    offset = cfg.get('row_start_step', 0)
    counts = {k:v['count'] for k,v in receipt['streams'].items()}
    plans = list(run.data.mixed_indices(counts, offset + start_step + steps,
        start_step=offset + start_step, training_mode=cfg.get('training_mode','mixed'),
        mix=recipe['mix'], world=recipe['world_size'], r2_sampling=cfg.get('r2_sampling'),
        require_r2='r2_identity' in cfg))
    if len(plans) != steps:
        raise ValueError('Sampler did not produce the requested bounded audit')
    return dict(start_step=start_step, row_start_step=offset, world_size=recipe['world_size'], plans=plans)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('tree','config','receipt','resume-pin','out'):
        p.add_argument('--'+name, required=True)
    p.add_argument('--steps',type=int,default=10)
    args=p.parse_args()
    sys.path.insert(0,str(Path(args.tree).resolve()))
    from student_pilot import carrier_c1_run as run
    cfg, receipt = run.load(args.config), run.load(args.receipt)
    checkpoint = run.load(run.pinned(run.load(args.resume_pin)))
    if checkpoint.get('schema') != 'c1-checkpoint-v1':
        raise ValueError('RESUME_PIN must pin a completed native checkpoint manifest')
    if checkpoint['binding']['world_size'] != run.recipe_for(cfg)['world_size']:
        raise ValueError('Checkpoint and audit world sizes differ')
    # Pin all inputs in the audit plan; replay also checks the full native binding.
    result=build_plan(run,cfg,receipt,checkpoint['step'],args.steps)
    result.update(config_sha256=run.identity(cfg), receipt_sha256=run.file_pin(args.receipt)['sha256'],
                  resume=run.load(args.resume_pin))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'kit_profile'))
    from privacy import scrub
    with Path(args.out).open('x') as output:
        output.write(json.dumps(scrub(result),indent=2)+'\n')
    print(json.dumps(dict(start_step=result['start_step'], steps=args.steps, world_size=result['world_size'])))


if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'kit_profile'))
    from privacy import filter_streams
    filter_streams()
    main()
