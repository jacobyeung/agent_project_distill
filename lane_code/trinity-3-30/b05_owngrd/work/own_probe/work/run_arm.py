"""Resume completed E-A stages for one arm; never retry a failed subprocess."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from probe_common import ROOT,ARMS,RULES_PATH,gate,rules
from provenance import sha256,digest,write_json


def run(a):
    cfg=rules();gate.read_manifest(a.train);gate.read_manifest(a.tuning,'tuning')
    out=Path(a.results)/a.arm
    if getattr(a,'readout','four')!='four':out=out/a.readout
    out.mkdir(parents=True,exist_ok=True)
    weights=json.loads(Path(a.weights).read_text());kind=ARMS[a.arm][0]
    required=['qwen_vit','g3t'] if a.arm=='A8' else [kind]
    missing=[]
    for key in required:
        if key not in weights:missing.append(key+' configuration');continue
        for field in ('path','source_root','receipt','config'):
            if field in weights[key] and not Path(weights[key][field]).exists():missing.append(weights[key][field])
        if key in ('cradio_v4_so400m','dinov3_vitl16','dinov2_vitl14_reg') and not (Path(weights[key]['path'])/'LOCAL_PIN.json').exists():missing.append(key+' LOCAL_PIN.json')
    if missing:
        write_json(out/'SKIPPED.json',dict(arm=a.arm,status='missing',reason='; '.join(missing)))
        print('skip',a.arm,missing,flush=True);return
    if a.arm=='A8':
        components=[]
        for component in ('A2','A4'):
            path=Path(a.results)/component/'CHANNEL_ENERGY.json'
            if path.exists():
                components.extend(dict(row,tap=component+'/'+str(row['tap']),component=component)
                                  for row in json.loads(path.read_text())['summary'])
        if components:write_json(Path(a.results)/'A8/CHANNEL_ENERGY.json',dict(arm='A8',summary=components,note='Component tap shares before fusion'))
    code={str(p.relative_to(ROOT)):sha256(p) for p in (ROOT/'work').rglob('*.py')}
    stable_args={k:v for k,v in vars(a).items() if k not in ('phases','labels','fusion_rows')}
    base_binding=dict(config=stable_args,rules=sha256(RULES_PATH),fit_config=sha256(ROOT/'work/FIT_CONFIG.json'),code=code,weights=sha256(a.weights),
                       train=sha256(a.train),tuning=sha256(a.tuning),labels=sha256(a.labels) if a.labels else None,
                       fusion=sha256(a.fusion_rows) if a.fusion_rows else None)
    phase_args={
      'smoke':['gpu_smoke.py','--arm',a.arm,'--weights',a.weights,'--manifest',a.train,'--out',str(out/'SMOKE.json')],
      'extract':['extract.py','--arm',a.arm,'--weights',a.weights,'--feature-root',a.feature_root,'--train',a.train,'--tuning',a.tuning],
      'T1':['fit_t1.py','--arm',a.arm,'--feature-root',a.feature_root,'--out',str(out)],
      'T4':['fit_t4.py','--arm',a.arm,'--feature-root',a.feature_root,'--out',str(out)],
      'T2':['fit_t2.py','--arm',a.arm,'--weights',a.weights,'--train',a.train,'--tuning',a.tuning,'--out',str(out)],
      'T3':['fit_t3.py','--arm',a.arm,'--weights',a.weights,'--train',a.train,'--tuning',a.tuning,'--out',str(out)]}
    if a.fusion_rows:phase_args['T1']+=['--fusion-rows',a.fusion_rows]
    if a.labels:
        phase_args['T2']+=['--labels',a.labels];phase_args['T3']+=['--labels',a.labels]
    if a.arm=='A8':phase_args.pop('smoke');phase_args.pop('extract')
    for phase in ('T1','T2','T3','T4'):phase_args[phase]+=['--readout',getattr(a,'readout','four')]
    for phase in ('T2','T3'):phase_args[phase]+=['--feature-root',a.feature_root]
    if getattr(a,'readout','four')!='four':
        phase_args.pop('smoke',None);phase_args.pop('extract',None)
    selected=a.phases.split(',') if a.phases else list(phase_args)
    for phase in selected:
        if phase not in phase_args:raise ValueError(f'Unsupported phase for arm: {phase}')
        if phase=='extract':
            smoke=Path(a.results)/a.arm/'SMOKE.json'
            if not smoke.exists():raise ValueError('Extraction requires a real-frame smoke gate')
            report=json.loads(smoke.read_text())
            if report.get('arm')!=a.arm or any(m.get('spatial_correspondence',{}).get('status')!='PASS' for m in report.get('measurements',[])) or not report.get('measurements'):
                raise ValueError('Spatial gate has not passed for this provider')
            if a.arm=='A7' and not all(m.get('bf16_autocast') for m in report['measurements']):raise ValueError('SAM bf16 autocast unconfirmed')
        phase_binding={**base_binding}
        if phase not in ('T2','T3'):phase_binding.pop('labels')
        if phase!='T1':phase_binding.pop('fusion')
        binding=digest(phase_binding)
        if phase=='extract':
            smoke_marker=Path(a.results)/a.arm/'smoke.done.json'
            if not smoke_marker.exists():raise ValueError('Smoke completion marker is missing')
            verified=json.loads(smoke_marker.read_text())
            if verified['binding']!=binding or verified['outputs'].get(str(smoke))!=sha256(smoke):raise ValueError('Smoke gate binding differs')
        marker=out/(phase+'.done.json')
        failure=out/(phase+'.failure.json')
        if failure.exists() and json.loads(failure.read_text()).get('system_signal'):
            raise RuntimeError('This phase was system-killed. Stop and obtain user approval before any rerun.')
        if marker.exists():
            previous=json.loads(marker.read_text())
            if previous['binding']!=binding:raise ValueError('Resume requires unchanged code/config/inputs or a new results directory')
            if any(not Path(p).exists() or sha256(p)!=h for p,h in previous['outputs'].items()):raise ValueError('Completed output changed')
            print('resume completed',a.arm,phase,flush=True);continue
        if phase in ('T2','T3') and not a.labels:
            write_json(out/(phase+'.json'),dict(arm=a.arm,task=phase,status='pending',reason='O5 labels missing',rules_sha256=sha256(RULES_PATH)))
            print('pending O5 labels',phase,flush=True);continue
        ledger_path=Path(a.ledger) if a.ledger else Path(a.results)/'GPU_TIME.json'
        ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
        spent=sum(item['seconds'] for item in ledger.values())
        minutes={
            'A1':(2,13,25,20),'A2':(4,29,50,40),'A3':(4,29,50,40),
            'A4':(6,52,240,240),'A5':(4,32,50,40),'A6':(4,29,45,35),
            'A7':(6,48,80,65),'A8':(0,0,260,260),'D2':(2,15,40,35)}[a.arm]
        estimates=dict(zip(('smoke','extract','T2','T3'),[v*60 for v in minutes]))
        estimates.update(T1=240,T4=180)
        if spent+estimates[phase]>a.budget_minutes*60:
            write_json(out/'BUDGET_STOP.json',dict(phase=phase,spent_seconds=spent,budget_minutes=a.budget_minutes,
                       reason='Insufficient estimated time for the next phase; no job was killed or retried'))
            print('budget stop before',a.arm,phase,flush=True);return
        cmd=[sys.executable,str(ROOT/'work'/phase_args[phase][0])]+phase_args[phase][1:]+['--device',a.device]
        print('run',a.arm,phase,flush=True);start=time.monotonic();result=subprocess.run(cmd,check=False)
        elapsed=time.monotonic()-start
        ledger_key=a.arm+'/'+phase+'/attempt-'+str(time.time_ns())
        ledger[ledger_key]=dict(seconds=elapsed,binding=binding,returncode=result.returncode)
        write_json(ledger_path,ledger)
        if result.returncode:
            # No automatic retry, including negative return codes from system signals.
            write_json(out/(phase+'.failure.json'),dict(binding=binding,returncode=result.returncode,
                         system_signal=(-result.returncode if result.returncode<0 else result.returncode-128 if 128<result.returncode<193 else None),command=cmd,
                         action='Stop. A system-killed process requires user approval before any rerun.'))
            raise SystemExit(result.returncode if result.returncode>0 else 128-result.returncode)
        outputs={str(p):sha256(p) for p in out.glob('*') if p.is_file() and not p.name.endswith('.done.json')}
        if phase=='extract':
            p=Path(a.feature_root)/a.arm/'COMPLETE.json';outputs[str(p)]=sha256(p)
            summaries={}
            for energy_path in (Path(a.feature_root)/a.arm).glob('*.energy.json'):
                for item in json.loads(energy_path.read_text())['energy']:
                    key=(item['split'],item['tap'],item['stage'])
                    total,n=summaries.get(key,(0.,0))
                    summaries[key]=(total+item['tokens']*item['mean_token_largest_channel_share'],n+item['tokens'])
            rows=[]
            for split,tap in sorted({(k[0],k[1]) for k in summaries}):
                rows.append(dict(split=split,tap=tap,**{stage:summaries[split,tap,stage][0]/summaries[split,tap,stage][1] for stage in ('before','after','before_head','after_head')}))
            energy_out=out/'CHANNEL_ENERGY.json';write_json(energy_out,dict(arm=a.arm,summary=rows));outputs[str(energy_out)]=sha256(energy_out)
            stats_path=Path(a.feature_root)/a.arm/'CHANNEL_STATS.json';outputs[str(stats_path)]=sha256(stats_path)
        write_json(marker,dict(binding=binding,phase=phase,seconds=elapsed,outputs=outputs))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--arm',choices=ARMS,required=True)
    p.add_argument('--weights',required=True);p.add_argument('--results',required=True);p.add_argument('--feature-root',required=True)
    p.add_argument('--train',default=str(ROOT/'out/b2_manifest.jsonl'));p.add_argument('--tuning',default=str(ROOT/'out/tuning_manifest.jsonl'))
    p.add_argument('--labels');p.add_argument('--fusion-rows');p.add_argument('--device',default='cuda:0');p.add_argument('--phases')
    p.add_argument('--budget-minutes',type=float,default=240.)
    p.add_argument('--readout',choices=['four','final','unstandardized'],default='four')
    p.add_argument('--ledger',help='Shared allocation ledger, including runs in different result directories')
    run(p.parse_args())
