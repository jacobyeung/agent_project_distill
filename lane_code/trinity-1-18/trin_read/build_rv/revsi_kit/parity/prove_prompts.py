"""Rebind dev main through the unchanged wrapper, then compare accepted prompts."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reader/out'))
import direct


def prove(output,processor_dir=None,reader_root=None,kit_root=None):
    if reader_root is not None:
        global direct
        import importlib
        for name in ('direct','common','export_check'):sys.modules.pop(name,None)
        sys.path.insert(0,str(Path(reader_root)/'out'))
        direct=importlib.import_module('direct')
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    models=json.loads((ROOT/'launcher/MODELS.json').read_text())
    (output/'models.json').write_text(json.dumps(models)+'\n')
    direct.bind(SimpleNamespace(dest=str(output/'bound'),models=str(output/'models.json'),
        export=models['cp1m200']['path'],sha256=models['cp1m200']['sha256'],step=544,
        family='main',kit=str(kit_root or ROOT/'reader'),frames_root=str(output/'v'),dry=True,parent_standin=False))
    pins=json.loads((output/'bound/PROMPT_PINS.json').read_text())
    expected=json.loads((ROOT/'parity/PROMPT_PINS.json').read_text())
    if pins!=expected:raise ValueError('PROMPT_PINS entries differ')
    if (output/'bound/PROMPT_PINS.json').read_bytes()!=(ROOT/'parity/PROMPT_PINS.json').read_bytes():
        raise ValueError('PROMPT_PINS serialized bytes differ')
    cfg=json.loads((output/'bound/request.json').read_text())
    from data import tasks_for
    from parity import prompt
    tasks=sorted(tasks_for(cfg['datasets'][0],cfg['roots']),key=lambda t:(t['benchmark'],t['example_id']))[:20]
    accepted=json.loads((ROOT/'parity/ACCEPTED20.json').read_text())
    if [t['example_id'] for t in tasks]!=[r['example_id'] for r in accepted]:raise ValueError('First-20 ordering differs')
    report=dict(prompt_pins_equal=True,prompt_pins_sha256=hashlib.sha256((output/'bound/PROMPT_PINS.json').read_bytes()).hexdigest(),
                items=20,processor_checked=False,all_prompt_bytes_equal=None)
    if processor_dir is not None:
        from transformers import AutoProcessor
        processor=AutoProcessor.from_pretrained(processor_dir,local_files_only=True)
        equal=[prompt(processor,t,cfg['cells'][0]).encode()==r['prompt_text'].encode() for t,r in zip(tasks,accepted)]
        report.update(processor_checked=True,all_prompt_bytes_equal=all(equal),equal=equal)
        if not all(equal):raise ValueError('Accepted prompt bytes differ')
    (output/'PARITY.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--processor-dir');p.add_argument('--reader-root');p.add_argument('--kit-root')
    a=p.parse_args();print(json.dumps(prove(a.output,a.processor_dir,a.reader_root,a.kit_root)))
