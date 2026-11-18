"""CPU subprocess fixture: real launcher/journals with a deterministic generator."""
import json,sys,time,os
from pathlib import Path
from unittest.mock import patch

def main():
 cfg=json.loads(Path(sys.argv[1]).read_text());p=Path(cfg['package']);c=cfg['config']
 sys.path[:0]=[str(p/'b'),str(p/'tree'),str(p)]
 import e2e_reader
 from orchard_h10.runner import worker_args
 from h1eval.h10 import launch,parity_adapter
 from h1eval.items import load_manifest
 args=launch.parser().parse_args(worker_args(cfg));items=load_manifest(args.items)['items']
 loads=[]
 def maker(export,artifact,selection,**kw):
  loads.append(len(selection))
  def gen(item):
   if c.get('fixture_stop'):
    Path(c['fixture_stop']).write_text('ready')
    until=time.monotonic()+10
    while not Path(args.stop_file).exists() and time.monotonic()<until:time.sleep(.02)
    assert Path(args.stop_file).exists(),'parent did not write top STOP'
   return dict(text='<answer>1</answer>',finish='eos',fixture_pid=os.getpid())
  return gen
 with patch.object(parity_adapter,'map_items',return_value=({r['id']:r for r in items},{'sha256':'a'*64})):
  result=launch.run_types(args,make_real=maker)
 Path(c['output'],'metadata/LOADS.json').write_text(json.dumps(loads))
 print(json.dumps(result))
