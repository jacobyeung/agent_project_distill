#!/usr/bin/python3
"""Lane san_dd_app: prints the five numbers REPORT.md rests on (R0-dev obj_appearance_order, step 200 = R1 run 673bc60f).
Run: /usr/bin/python3 /scratch/jjyeung/orch_n30/san_dd_app/work/reproduce.py   (CPU, read-only, about 10 s)"""
import sys
from collections import defaultdict
sys.dont_write_bytecode = True
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_app/work')
import app as A, pred as Q
P = A.load('R1', 200)
def fdec(p, order):  # option nearest an order: exact match, else longest shared prefix, else most agreeing pairs, else first letter
    return sorted(p['op'], key=lambda L: (-Q.lcp(order, p['op'][L]), -Q.kt(order, p['op'][L]), L))[0]
W = [p for p in P.values() if p['score'] != 1]
print('1. wrong items whose stated frames imply a wrong order: %d of %d' % (sum(p['fo'] != p['truth'] for p in W), len(W)))
print('2. answer = option nearest the stated frames: %d of %d; that decoder right on %d, the answers on %d' % (
    sum(p['pred'] == fdec(p, p['fo']) for p in P.values()), len(P), sum(fdec(p, p['fo']) == p['gt'] for p in P.values()),
    sum(p['score'] == 1 for p in P.values())))
D = [p for p in P.values() if p['w'] != p['fo']]
print('3. written order departs from the sorted frames on %d; of these the written order is an option and the sorted frames are not on %d' % (
    len(D), sum(p['w_opt'] is not None and p['fo_opt'] is None for p in D)))
def first_fixed(p):
    t = p['truth']; return [t[0]] + [o for o in p['fo'] if o != t[0]]
print('4. frames decoder right with the truly-first object moved to the front: %d of %d' % (sum(fdec(p, first_fixed(p)) == p['gt'] for p in P.values()), len(P)))
ob = defaultdict(list)
for p in P.values():
    for o, v in p['fr'].items(): ob[(p['room'], o)].append(v)
multi = [v for v in ob.values() if len(v) > 1]
print('5. same object in the same video asked in 2+ items: identical stated frame on %d of %d' % (sum(len(set(v)) == 1 for v in multi), len(multi)))
