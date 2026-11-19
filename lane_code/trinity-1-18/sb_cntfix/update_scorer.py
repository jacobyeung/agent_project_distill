from pathlib import Path
p=Path('kit/files/score_count_pricing.py');s=p.read_text()
keep=[]
for start,end in [('def rle_decode','def frame_count'),('def spearman','CONSTANTS ='),('def boot','def summarize')]:keep.append(s[s.index(start):s.index(end)])
header='''#!/usr/bin/env python3
"""Score a preregistered counting comparison under the K1 training freeze."""
import argparse, collections, gzip, json, math, os, random, sys
from pathlib import Path
import numpy as np
import count_guard as G
from official_vsi_mra import official_mra
SEED, DRAWS = 20261119, 10000

def mra(pred, truth):
    try: p, t = float(pred), float(truth)
    except (TypeError, ValueError): return 0.0
    return official_mra(p, t)

'''
p.write_text(header+'\n'.join(keep))
