"""Exercise the entire worker on two generated videos and two items per subtype."""
from pathlib import Path
import sys
from .io import dump, sha, digest
from .paths import ROOT
from .fixture import Runtime
from .worker import Worker
from .scoring import Scorer
from .reporting import report
from offkit.bind import bind
from offkit.frames import bind_frames
from offkit.report import ReadMode

def run(destination, kind, *, mutate_proof=False):
    dest = Path(destination)
    dest.mkdir(parents=True, exist_ok=False)
    mode = ReadMode('revsi999t32', kind)
    items = []
    for typ in mode.types:
        for i in range(2):
            items.append(dict(id=str(len(items)+1),example_id=str(len(items)+1),question_type=typ,
                              dataset='fixture',scene_name=str(i),question='Count or measure the fixture.',
                              options=[],ground_truth='2',fixture_refusal=typ=='object_abs_distance' and i==0))
    labels = dest/'labels.json'; dump(labels,items)
    items = [{k:v for k,v in r.items() if k!='ground_truth'} for r in items]
    kwargs = {}
    if kind=='harness':
        f = dest/'ROUTED_PATH_FROZEN_20261116.md'
        f.write_text('Synthetic fixture only.\n```json\n'+__import__('json').dumps({'freeze_values':{'selector':{'source':'K1_refit','kill_rules_passed':True},'fixture':True}})+'\n```\n')
        kwargs['freeze_file'] = f
    else:
        f = dest/'e2e.json'; dump(f, {'fixture':True})
        kwargs['e2e_manifest'] = f
    b = bind('revsi999t32','step544',kind+':'+sha(f),mode='fixture',**kwargs)
    from .source import bind_source
    b['read_config'] = dict(frames=bind_frames(),g3t=bind_source('clip32',reader=kind))
    b['binding_sha256'] = digest({k:v for k,v in b.items() if k!='binding_sha256'})
    dump(dest/'BINDING.json', b)
    config = dict(schema='orchkit-config-v1', binding_sha256=b['binding_sha256'],
                  transport={'kind':'local_fixture'}, reader=kind, frames=b['read_config']['frames'],
                  production_admissible=False)
    dump(dest/'CONFIG.json',config)
    runtime = Runtime(dest/'assets',items,kind,mutate_proof=mutate_proof)
    worker = Worker(config,b,items,runtime,Scorer(labels),dest/'return',fixture=True)
    worker.run()
    report(b,items,dest/'return',dest/'reports',fixture=True,repetitions=100)
    dump(dest/'RESULT.json',dict(passed=True,phases=7,items=len(items),videos=2,reader=kind,
        official_decodes=worker.official_decodes,tower_calls=runtime.entry.tower_calls,
        production_config_transport_only=False,
        limitations=['Production loader and harness decoder are not exercised.','Synthetic tower arrays replace tower inference.']))
    return dest/'RESULT.json'

if __name__=='__main__':
    print(run(sys.argv[1],sys.argv[2]))
