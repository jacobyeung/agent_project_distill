from pathlib import Path
import json
L=Path(__file__).resolve().parents[1]
load=lambda n:json.loads((L/'out'/n).read_text())
base=load('CPU_base_proof_off.json');old=load('CPU_patched_off.json');new=load('CPU_patched_on.json')
report=dict(source=str(L/'work/tests/fixtures_contracts.py'),fixtures={},exceptions=[])
for kind,b in base.items():
    assert b==old[kind],kind
    n=new[kind]
    differences={c:dict(base=b['responses'].get(c),patched=n['responses'].get(c)) for c in set(b['responses'])|set(n['responses']) if b['responses'].get(c)!=n['responses'].get(c)}
    if kind in ('landscape','portrait','rolled','small'):assert not differences,(kind,differences)
    if kind in ('nadir','nadir_positive','vertical'):
        assert n['verdict']=='pass'
        assert 'heading unavailable' in next(iter(n['responses'].values()))
    if kind=='nadir_positive':
        for call in b['responses']:
            if call.startswith('<gap') or call=='<ground mode="room">':
                assert b['responses'][call]==n['responses'][call],call
            if call.startswith('<ground obj=') and 'mode="instances"' not in call:
                sizes=lambda body:[line for line in body.splitlines() if line.startswith('size ')]
                assert sizes(b['responses'][call])==sizes(n['responses'][call]),call
            if 'mode="instances"' in call:
                assert b['responses'][call].splitlines()[0]==n['responses'][call].splitlines()[0],call
    if kind.startswith('inverted'):assert n['verdict']==b['verdict']=='reference_camera_up_opposes_gravity'
    report['fixtures'][kind]=dict(plane=n['plane'],margin=n['margin'],optical_horizontal=n['optical_horizontal'],
        base_verdict=b['verdict'],patched_verdict=n['verdict'],off_verdict=old[kind]['verdict'],
        base_responses=b['responses'],patched_responses=n['responses'],off_responses=old[kind]['responses'],
        replay_off_byte_equal=True,default_on_byte_equal=not differences,differences=differences,source=n['source'])
report['exceptions']=[
    'Default ON intentionally changes heading-dependent outputs for sealed-positive ill-conditioned headings; universal ON byte parity contradicts the required heading policy.',
    'Default ON repairs the MDG box defect; preserving its unavailable responses would contradict the required bridge.',
    'Exactly vertical references can pass the sealed floating-point sign check but fail its lifting basis. The new epoch serves private metrics and suppresses public heading.']
(L/'out/CPU_PROOF_B1.json').write_text(json.dumps(report,indent=2)+'\n')
print('Replay OFF matches every base fixture; defined-heading non-MDG responses match ON.')
