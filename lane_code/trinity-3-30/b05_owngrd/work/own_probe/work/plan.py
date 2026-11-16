"""CPU preflight: count calls/regions and report missing input files without loading weights."""
import argparse
import collections
import json
from pathlib import Path
from probe_common import *
from extract import chosen_instances


def run(a):
    cfg=rules();train=gate.read_manifest(a.train);tune=gate.read_manifest(a.tuning,'tuning')
    selected=[r for r in train if r['slot']%cfg['sampling']['training_frame_stride']==0]
    groups=read_tuning_metadata(O/'verify_kit/out/e1_k5_candidates.jsonl')
    ntrain=sum(len(chosen_instances(r)) for r in selected)
    ntune=sum(len(c['members']) for g in groups for c in g['candidates'])
    weights=json.loads(Path(a.weights).read_text());available={}
    for arm,(kind,size) in ARMS.items():
        if arm=='D2':continue
        keys=['qwen_vit','g3t'] if arm=='A8' else [kind]
        missing=[]
        for key in keys:
            value=weights.get(key,{})
            for field in ('path','source_root','receipt'):
                if field in value and not Path(value[field]).exists():missing.append(value[field])
            if not value:missing.append(key+' configuration')
            if key=='sam3_pe' and not value.get('source_root'):missing.append('SAM local source root')
            if key in ('cradio_v4_so400m','dinov3_vitl16','dinov2_vitl14_reg') and value.get('path'):
                if not (Path(value['path'])/'LOCAL_PIN.json').exists():missing.append('LOCAL_PIN.json for '+key)
        available[arm]=dict(status='missing' if missing else 'available',reason='; '.join(missing) if missing else 'Local inputs present; GPU smoke pending')
    calls={arm:0 if arm=='A8' else len({r['scene'] for r in train+tune}) if arm=='A4' else len(selected)+len(tune)
           for arm in cfg['execution_order']}
    known_dims={a:1024 for a in ('A1','A2','A3','A4','A5','A6','A7')}
    estimated=(ntrain+ntune)*sum(known_dims.values())*2*3
    calibration=[r for r in selected if r['split']=='train']
    calibration_calls={arm:0 if arm=='A8' else len({r['scene'] for r in calibration}) if arm=='A4' else len(calibration) for arm in cfg['execution_order']}
    output=dict(experiment='E-A',training_frames=len(train),selected_training_frames=len(selected),tuning_frames=len(tune),
                training_regions=ntrain,tuning_member_regions=ntune,extract_calls=calls,calibration_calls=calibration_calls,
                online_fit_steps={k:cfg['fit'][k+'_steps'] for k in ('T1','T2','T3','T4')},fusion_steps=300,
                smoke_calls_non_temporal=16,smoke_calls_g3t=2,
                online_eval_calls_non_temporal=992,online_eval_calls_g3t=31,
                feature_bytes_estimate=estimated,estimate_dimensions=known_dims,
                feature_estimate_note='Three readouts each store 1024 fp16 channels. A8 composes its component shards in RAM.',
                phase1_estimate_minutes=165,phase1_tasks=['smoke','calibrate+extract','T1','T4'],
                phase1_arms=['A1','A7','A2'],phase2_arms=['A3','A5','A6','A4','A8'],
                budget_note='Estimates, not measurements. The 240-minute ledger stops new phases; missing inputs/rules remain pending.',
                provenance=receipt([a.train,a.tuning,a.weights,RULES_PATH],[Path(__file__)],vars(a)))
    out=Path(a.out);write_json(out/'PLAN.json',output);write_json(out/'AVAILABILITY.json',available)
    print(json.dumps(dict(training_regions=ntrain,tuning_member_regions=ntune,feature_bytes_estimate=estimated,extract_calls=calls)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--weights',required=True);p.add_argument('--out',default=str(ROOT/'out'))
    p.add_argument('--train',default=str(ROOT/'out/b2_manifest.jsonl'));p.add_argument('--tuning',default=str(ROOT/'out/tuning_manifest.jsonl'))
    run(p.parse_args())
