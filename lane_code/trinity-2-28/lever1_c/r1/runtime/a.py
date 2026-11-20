"""Restore submission contracts from the checked package under export=NONE."""
def allocation(shared, public, sha):
    import json
    import os
    cpu=json.loads((shared/'2.json').read_text())
    if (cpu.get('passed') is not True or cpu.get('plan')!=public['plan_sha256']
            or cpu.get('inputs')!=sha(shared/'a/1.json')
            or cpu.get('package')!=sha(shared/'PACKAGE.json')
            or cpu.get('gpus')!=1 or cpu.get('time')!='00:50:00'):
        raise ValueError('E60')
    values=dict(A_N='1',A_T='3000',A_I=cpu['inputs'],A_C=sha(shared/'2.json'))
    for key,value in values.items():
        if key in os.environ and os.environ[key]!=value:raise ValueError('E61')
    os.environ.update(values)
    return values
