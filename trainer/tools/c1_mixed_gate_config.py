"""Render the C1 final-mode (mixed gate) run config from an existing C1 arm config.

The base config supplies the site paths (code seal, A1 pose stream, readout bank,
base identity, frame layout). This tool sets the mixed-gate fields and embeds the
exact recipe the trainer recomputes. Unbound stream receipts are written as null
and listed under `unbound`, so a config with gaps can never pass `validate`.
"""
import argparse
import json
from pathlib import Path

from student_pilot.carrier_c1_data import PLACEMENTS
from student_pilot.carrier_c1_sweep import recipe_for

PLACEMENT = dict(a=PLACEMENTS[0], b=PLACEMENTS[1], c=PLACEMENTS[2])
# SELF_ROUTING_DESIGN 1.5/1.6: six microsteps, 48 rows per update at world 8.
GATE_MIX = ['pose', 'pose', 'vqa', 'pointing', 'routing', 'routing']
# Per-head gates (1.2): own pose opens below 20 deg and reaches p = 0.5 at 10 deg (orchestrator 12:56Z);
# the test run forces both open at p = 0.5 from step 2 (its first steps are the smoke).
GATE_SAMPLING = dict(seed=17, max_own_probability=.5, pose_open_deg=20., pose_full_deg=10., fov_open_deg=2.,
                     depth_open_absrel=.25, ema_steps=100, force_from_step=2,
                     exposure_from_step=None, exposure_probability=0.)


def pin(text):
    return None if text in (None, '', 'PENDING') else json.loads(text)


def render(base, placement, streams, output, preparation_output, world=8, steps=200,
           milestones=(100, 200), mix=GATE_MIX, sampling=GATE_SAMPLING, weights=None,
           p95_step_seconds=100., depth_init=None, exclusions=None, report_exclusions=None):
    cfg = {k: v for k, v in base.items() if k != 'recipe'}
    cfg.update(training_mode='final', carrier_placement=PLACEMENT[placement], depth_enabled=True,
               depth_fov_source='pose_head', mix=list(mix), world_size=world, steps=steps,
               milestones=list(milestones), scheduled_sampling=dict(sampling), weights=dict(weights or {}),
               output=output, preparation_output=preparation_output, preparation=None, admission=None,
               authorization=None, milestone_gate=None, depth_init=depth_init, exclusions=exclusions, report_exclusions=report_exclusions,
               streams={'pose': base['streams']['pose'], **{k: streams.get(k) for k in ('vqa', 'pointing', 'routing')}})
    if depth_init is not None:
        # The Stage-1 V-C head starts trained: raise its weight from 0.05 (set with depth off).
        cfg['weights'] = {'depth': .25, **cfg['weights']}
    cfg['schedule'] = {**base.get('schedule', {}), 'p95_step_seconds': p95_step_seconds}
    cfg['recipe'] = recipe_for(cfg)
    cfg['unbound'] = sorted([k for k, v in cfg['streams'].items() if v is None] + (['depth_init'] if depth_init is None else [])
                            + (['exclusions'] if exclusions is None else []))
    return cfg


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True, type=Path, help='An existing carrier-c1-run-v1 arm config')
    parser.add_argument('--placement', required=True, choices=sorted(PLACEMENT))
    parser.add_argument('--vqa'), parser.add_argument('--pointing'), parser.add_argument('--routing')
    parser.add_argument('--output', required=True, help='Run output directory on the training site')
    parser.add_argument('--preparation-output', required=True)
    parser.add_argument('--world', type=int, default=8)
    parser.add_argument('--steps', type=int, default=200)
    parser.add_argument('--milestones', default='100,200')
    parser.add_argument('--depth-init', help='JSON pin of the Stage-1 V-C p3-head-artifact-v1')
    parser.add_argument('--exclusions', help='JSON pin of the TEST-split scene list (alias form)')
    parser.add_argument('--report-exclusions', help='JSON pin of the wider overlap list (reported only)')
    parser.add_argument('--mix', default=','.join(GATE_MIX))
    parser.add_argument('--sampling', default=json.dumps(GATE_SAMPLING))
    parser.add_argument('--weights', default='{}')
    parser.add_argument('--p95-step-seconds', type=float, default=100.)
    parser.add_argument('--write', required=True, type=Path)
    args = parser.parse_args()
    base = json.loads(args.base.read_text())
    if base.get('schema') != 'carrier-c1-run-v1':
        raise ValueError('Base must be a carrier-c1-run-v1 config')
    cfg = render(base, args.placement, {k: pin(getattr(args, k)) for k in ('vqa', 'pointing', 'routing')},
                 args.output, args.preparation_output, args.world, args.steps,
                 [int(m) for m in args.milestones.split(',')], args.mix.split(','), json.loads(args.sampling),
                 json.loads(args.weights), args.p95_step_seconds, pin(args.depth_init), pin(args.exclusions), pin(args.report_exclusions))
    if args.write.exists():
        raise FileExistsError(args.write)
    args.write.write_text(json.dumps(cfg, indent=1, sort_keys=True) + '\n')
    print(json.dumps(dict(placement=cfg['carrier_placement'], unbound=cfg['unbound'], mix=cfg['mix'],
                          global_batch=cfg['recipe']['global_batch']), indent=1))


if __name__ == '__main__':
    main()
