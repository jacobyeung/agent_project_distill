from pathlib import Path
import json
L=Path(__file__).resolve().parents[1]
report=json.loads((L/'work/mutation_r3/all_first_r3.json').read_text())
repeat=json.loads((L/'out/MUTATION_R3.json').read_text())
report['mutations'].update(repeat['mutations'])
descriptions=[
 'Change the convention boundary comparison from inclusive to strict',
 'Weaken the usable-frame median convention threshold',
 'Use the wrong gravity projection components for heading availability',
 'Stop recognizing runtime error responses',
 'Stop recognizing bare unavailable responses',
 'Allow a gap immediately after a failed ground',
 'Admit operator faults',
 'Apply the depth-cut bridge with the contract epoch disabled',
 'Remove the ies-to-y normalization rule',
 'Measure fallback move distance from the reference instead of the source frame',
 'Measure camera gap from the reference instead of the named camera',
 'Skip materializer contract deferral',
 'Use source.names instead of capture cache phrases',
 'Print witness horizontal coordinates without checking heading availability',
 'Drop the generator BoxRegistry epoch dispatch',
 'Drop training head-response heading dispatch',
 'Drop cache_phrases wiring in build_backend',
 'Print instance horizontal coordinates without checking heading availability',
 'Treat a served point with missing size as failed',
 'Turn dispatched generator classes into functions',
 'Admit cache-backed named grounds without a phrase manifest',
 'Ignore the queried pose frame heading',
 'Gate calculator responses on point heading availability',
 'Raise on malformed training records',
 'Discard one alias record while merging cache phrases',
]
for i,description in enumerate(descriptions,1):
    report['mutations'][f'M{i}']['description']=description
report['killed']=sum(v['killed'] for v in report['mutations'].values())
report['reviewed_count']=18;report['new_count']=len(descriptions)-18
report['baseline_suite']=str(L/'out/FINAL_TEST_RESULTS_R3.json')
assert len(report['mutations'])==len(descriptions) and all(v['killed'] for v in report['mutations'].values())
(L/'out/MUTATION_R3.json').write_text(json.dumps(report,indent=2)+'\n')
