"""Union successful runtime imports with the retained staged-interpreter inventory."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
trace=json.loads((ROOT/'out/WORKER_IMPORT_TRACE.json').read_text())
baseline=json.loads((ROOT/'tests/import_baseline.json').read_text())
assert trace['passed'] and trace['records']==8
excluded={name:'Trace harness alias; production executes its own entry/storage/batch modules by file path.'
          for name in ('__main__','__mp_main__','a_storage','builder','ctl','probe','batched')}
excluded.update({name:'Local tiny-model test fixture; not production workload code.'
                 for name in ('tests','tests.test_carrier_c1','tests.test_carrier_c1_final')})
for name in trace['modules']:
    if name.startswith('_cython_') or name=='cython_runtime':
        excluded[name]='Synthetic Cython runtime cache; importing its required native extension creates it, and it has no independent import target.'
    if name=='_remote_module_non_scriptable':
        excluded[name]='Generated PyTorch RPC helper; required torch.distributed.nn.api.remote_module creates it, and it has no independent import target.'
gpu_only={name:'CUDA backend cannot execute on this CPU host; GPU boot must import it before bulk.'
          for name in ('fla','triton','causal_conv1d')}
# Failed optional probes are evidence, not required imports. Their importing
# libraries completed successfully without them on the traced CPU path.
for name in sorted(set(trace['audit_modules'])-set(trace['modules'])-set(gpu_only)):
    excluded[name]='Unsuccessful optional import probe; the real CPU worker completed without this module.'
pinned=json.loads((ROOT/'tests/pinned_exclusions.json').read_text())
excluded.update(pinned['drops'])
required=sorted((set(baseline['modules'])|set(trace['modules']))-set(excluded)-set(gpu_only))
assert 'student_pilot.carrier_c1_canary' in required
value=dict(method=trace['method']+'; union with tests/import_baseline.json; normal-name replay in authenticated pinned Orchard pre-bulk environment; no source import scanning',
    pinned_environment=pinned['environment'], pinned_drops=pinned['drops'],
    previous_cpu_modules=3338, previous_gpu_modules=3341,
    trace='out/WORKER_IMPORT_TRACE.json', generator='tests/trace_worker.py',
    generator_sha256=hashlib.sha256((ROOT/'tests/trace_worker.py').read_bytes()).hexdigest(),
    baseline_raw_modules=len(baseline['modules']),baseline_modules=len(set(baseline['modules'])-set(excluded)),
    traced_modules=len(trace['modules']),required_modules=required,
    aliases={n:v for n,v in trace['spec_names'].items() if n!=v and n in required},
    cpu_modules=len(required),gpu_modules=len(required)+len(gpu_only),
    exclusions=excluded,gpu_only=gpu_only,
    closure_sha256=hashlib.sha256('\n'.join(required).encode()).hexdigest())
(ROOT/'IMPORT_CLOSURE.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({k:v for k,v in value.items() if k not in ('required_modules','exclusions')}))
