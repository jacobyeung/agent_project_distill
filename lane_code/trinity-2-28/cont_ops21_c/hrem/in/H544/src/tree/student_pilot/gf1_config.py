"""Bind GF1 stage settings onto the current pinned C1 run without changing its mix."""
import argparse
import copy
import json
from pathlib import Path
from . import gf1, g3t_online
from .carrier_c1_sweep import recipe_for


def bind(source, stage, output, preparation_output):
    if set(stage) != {'schema', 'world_size', 'steps', 'milestones', 'gf1'}:
        raise ValueError('Unknown or missing GF1 stage key')
    if stage.get('schema') != 'gf1-stage-v1' or stage['world_size'] != 4:
        raise ValueError('Invalid GF1 stage recipe')
    cfg=copy.deepcopy(source)
    geometry=cfg.get('geometry_online')
    if not geometry:
        raise ValueError('Source run must supply pinned GXC tower assets and the current carrier checkpoint')
    if not cfg.get('init_artifact'):
        raise ValueError('FUS-1 must initialize from the current checkpoint')
    if cfg.get('mdg') or cfg.get('align'):
        raise ValueError('GF1 current-mix binding requires a separate review for MDG/alignment objectives')
    if geometry.get('mode') != 'frozen':
        raise ValueError('GF1 requires a frozen geometry tower')
    cfg.update(world_size=stage['world_size'],training_mode='final',frame_layout='duplicate',
               steps=stage['steps'],milestones=stage['milestones'],output=str(output),
               preparation_output=str(preparation_output))
    geometry.pop('patch_fusion',None)
    geometry.update(input=g3t_online.INPUT,gf1=gf1.normalize(stage['gf1']))
    fusion = geometry['gf1']
    if fusion['stage'] == 2 and fusion['gf1_init'] == 'zero' and 'gf1' in cfg['init_artifact'].get('heads', []):
        raise ValueError('Explicit GF1 zero init conflicts with loading gf1 heads')
    if fusion['stage'] == 2 and fusion['gf1_init'] != 'zero':
        from .carrier_c1_run import validate_init
        from .p3_provenance import pinned, load
        spec = validate_init(cfg['init_artifact'])
        if 'gf1' not in spec['heads']:
            raise ValueError('Stage 2 requires gf1 in init heads or explicit gf1_init: zero')
        donor = load(pinned(spec['artifact']))
        if not (donor.get('geometry_online') or {}).get('gf1'):
            raise ValueError('Stage 2 donor does not carry gf1')
    # GXC fail-fast compares other arm identities; GF1 uses the FUS-1 pre-registration.
    geometry.pop('fail_fast',None)
    cfg['geometry_online']=g3t_online.normalize(geometry)
    cfg.pop('preparation',None)
    cfg.pop('admission',None)
    cfg['gate_stop']=False
    # Explicit reference grouping preserves the source global stream budgets at world 1 and 4.
    cfg.setdefault('reference_world_size',source['recipe'].get('reference_world_size',source['world_size']))
    cfg['recipe']=recipe_for(cfg)
    if cfg['recipe']['global_batch'] != source['recipe']['global_batch']:
        raise ValueError('GF1 binding changed the current global data mix')
    cfg['recipe']['export_at_stop']=True
    # recipe_for retains export_at_stop from the explicit recipe.
    cfg['recipe']=recipe_for(cfg)
    return cfg


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True);parser.add_argument('--stage',required=True)
    parser.add_argument('--config-output',required=True);parser.add_argument('--run-output',required=True)
    parser.add_argument('--preparation-output',required=True)
    args=parser.parse_args()
    load=lambda p:json.loads(Path(p).read_text())
    cfg=bind(load(args.source),load(args.stage),args.run_output,args.preparation_output)
    # Keep the native code/asset/admission checks; the new preparation and code seal must be bound before launch.
    with Path(args.config_output).open('x') as f:json.dump(cfg,f,indent=2);f.write('\n')
if __name__=='__main__':main()
