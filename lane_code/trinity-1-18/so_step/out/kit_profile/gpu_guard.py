"""Refuse occupied or undersized target GPUs before trainer allocation."""
import os
import subprocess

# Maximum observed production usage: look2.out GPU samples, 76,699 MiB.
MIN_FREE_MIB = 76699


def check(local_rank=None):
    def query(option):
        return subprocess.run(['nvidia-smi', option, '--format=csv,noheader,nounits'],
            check=True, capture_output=True, text=True, timeout=10).stdout.strip().splitlines()
    devices = [tuple(v.strip() for v in row.split(','))
               for row in query('--query-gpu=index,uuid,memory.free')]
    visible = os.environ.get('CUDA_VISIBLE_DEVICES')
    tokens = visible.split(',') if visible is not None else [row[0] for row in devices]
    selected = []
    for token in tokens:
        matches = [row for row in devices if token and (token == row[0] or row[1].startswith(token))]
        if len(matches) != 1:
            raise ValueError('GPU guard cannot resolve target: ' + token)
        selected.append(matches[0])
    if local_rank is not None:
        selected = [selected[local_rank]]
    apps = [tuple(v.strip() for v in row.split(','))
            for row in query('--query-compute-apps=gpu_uuid,pid')]
    for index, uuid, free in selected:
        if any(gpu == uuid and int(pid) != os.getpid() for gpu, pid in apps):
            raise ValueError('GPU guard: another compute process on target ' + index)
        if int(free) < MIN_FREE_MIB:
            raise ValueError('GPU guard: insufficient free memory on target ' + index)
    return [dict(index=i, uuid=u, free_mib=int(f)) for i,u,f in selected]


if __name__ == '__main__':
    import json
    print(json.dumps(check()))
