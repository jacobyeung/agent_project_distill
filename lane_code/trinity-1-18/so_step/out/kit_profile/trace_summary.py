"""Interval unions avoid double-counting overlapping GPU kernels in a short trace."""
import argparse
import json
from pathlib import Path


def union(intervals):
    merged = []
    for start,end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1],end)
        else:
            merged.append([start,end])
    return merged


def duration(intervals):
    return sum(b-a for a,b in union(intervals)) / 1e6


def summarize(path):
    events = json.loads(Path(path).read_text())['traceEvents']
    kernels = [e for e in events if e.get('ph') == 'X' and 'kernel' in e.get('cat','').lower()]
    all_intervals = [(e['ts'],e['ts']+e['dur']) for e in kernels]
    comm = [(e['ts'],e['ts']+e['dur']) for e in kernels if 'nccl' in e['name'].lower()]
    compute = [(e['ts'],e['ts']+e['dur']) for e in kernels if 'nccl' not in e['name'].lower()]
    total,network,math = duration(all_intervals),duration(comm),duration(compute)
    span = (max(b for a,b in all_intervals)-min(a for a,b in all_intervals))/1e6 if all_intervals else 0.
    return dict(kernel_union_s=total,nccl_union_s=network,compute_union_s=math,
                nccl_only_s=total-math,compute_nccl_overlap_s=network+math-total,
                gaps_between_first_and_last_kernel_s=span-total,
                scope='short trace; NCCL-only is not guaranteed critical-path exposure')


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('trace')
    args=parser.parse_args()
    print(json.dumps(summarize(args.trace),indent=2))
