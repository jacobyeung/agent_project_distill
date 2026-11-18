"""Sealed resource authority for one continuation kit; GO is separate."""
import copy


def fields():
    return dict(
        modes=['p', 't', 'u'], new_gpus={'p': 0, 't': 4, 'u': 4},
        partition='advanced', allowed_partitions=['advanced', 'general', 'bootstrap'],
        wall_seconds=86400, nodes=1, resume='latest', arm='0', gpu_cap=4,
        other_running_and_pending_gpus=0, max_parallel_jobs=1,
        production_go_granted=False, production_go_required_separately=True,
        mode_resources={
            'p': dict(partitions=['general', 'bootstrap'], nodes=1, gpus=0, wall_seconds=14400),
            't': dict(partitions=['advanced'], nodes=1, gpus=4, wall_seconds=86400),
            'u': dict(partitions=['advanced'], nodes=1, gpus=4, wall_seconds=86400)},
    )


def bind(auth):
    value=copy.deepcopy(auth)
    value.update(fields())
    value.update(scope='Sealed CPU proof and continuation resources; separate identity-bound GO required for training.',
                 conditions=['Mode p: general/bootstrap, one node, zero GPUs, four hours.',
                             'Modes t/u: advanced, one node, four GPUs, 24 hours; resume latest.',
                             'Certify the final manifest before proof; never mutate the certified kit.',
                             'Training submission requires a separate identity-bound go.json.'])
    return value


def validate(auth):
    for key, value in fields().items():
        # JSON equality alone would admit booleans in place of integer counts.
        import json
        if json.dumps(auth.get(key),sort_keys=True)!=json.dumps(value,sort_keys=True):
            raise ValueError('Continuation authority differs: '+key)


def allocation(auth, mode, environment):
    validate(auth)
    if mode not in auth['modes']:
        raise ValueError('Operation not authorized')
    # Native admission runs mode p inside the already allocated training job.
    # The sealed entry sets its allocation mode before p0 and recursive r.sh p.
    allocation_mode=environment.get('TK_ALLOCATION_MODE',mode)
    if allocation_mode not in auth['modes'] or (mode!='p' and allocation_mode!=mode):
        raise ValueError('Allocation mode differs')
    limits=auth['mode_resources'][allocation_mode]
    if environment.get('SLURM_JOB_PARTITION') not in limits['partitions']:
        raise ValueError('Partition not authorized for mode '+mode)
    if (environment.get('SLURM_JOB_NUM_NODES')!='1'
            or environment.get('SLURM_GPUS_ON_NODE','0')!=str(limits['gpus'])):
        raise ValueError('Resources differ')
    if allocation_mode=='p' and environment.get('CUDA_VISIBLE_DEVICES','') not in ('','-1','NoDevFiles'):
        raise ValueError('Proof must be CPU-only')
    # Slurm does not export this variable on every site. The sealed job script
    # and launch slot also pin the wall limit; check the allocation when supplied.
    wall=environment.get('SLURM_TIMELIMIT')
    if wall is not None:
        if wall.isdigit():
            seconds=int(wall)*60
        else:
            days, clock=wall.split('-',1) if '-' in wall else ('0',wall)
            parts=[int(v) for v in clock.split(':')]
            if len(parts)==2:parts=[0,*parts]
            if len(parts)!=3:raise ValueError('Invalid allocation wall limit')
            seconds=int(days)*86400+parts[0]*3600+parts[1]*60+parts[2]
        if seconds!=limits['wall_seconds']:
            raise ValueError('Allocation wall limit differs')
    return limits

def check_authority(kit):
    """Authenticate the deployed authority before checking its resource limits."""
    import hashlib
    import json
    import re
    from pathlib import Path
    for entry in kit.iterdir():
        if entry.is_symlink() or entry.name not in {'SHA256SUMS.txt','ANON_OK.json','b','k','job.sh','job8.sh','o','arm','runs','sess.json'}:
            raise ValueError('Unexpected kit top-level entry: '+entry.name)
    manifest = kit/'SHA256SUMS.txt'
    if manifest.is_symlink() or not manifest.is_file():
        raise ValueError('Missing or linked derived manifest')
    pins = {}
    for line in manifest.read_text().splitlines():
        digest, name = line.split('  ', 1)
        if (not re.fullmatch('[0-9a-f]{64}', digest) or name in pins
                or Path(name).is_absolute() or '..' in Path(name).parts):
            raise ValueError('Invalid derived manifest')
        pins[name] = digest
    path = kit/'k/4.json'
    if (path.parent.is_symlink() or path.is_symlink() or not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != pins.get('k/4.json')):
        raise ValueError('Authority SHA differs from derived manifest')
    auth = json.loads(path.read_bytes())
    validate(auth)
    for key, value in dict(config_sha256='6594f46cdc16168514aca26a6ce38285907adfc6ece0b75d8e10428ea0b2fe74',
                           source_revision='sha256:b83a8a35d420815b9d6396e1fc1178e94c20d47ad459aa6da964e85bdec0f87b',
                           admission_contract_sha256='26059aff098020a08adcef7ad6ced09ab2aedb2edd4f3c6607028e496ebb8970').items():
        if auth.get(key) != value:
            raise ValueError('Authority identity differs: '+key)
    print('PASS sealed p/t/u authority; k/4.json SHA matches derived manifest')
    return auth
