"""Check the compiled thresholded filter against the exact Python implementation."""
import random
from camera_contract import *
from fast_wording import distance
from build_camera import levenshtein
pin(__file__)
for p in ['fast_wording.py','wording_distance.cpp','out/wording_distance.so','build_camera.py']:pin(ROOT/p)
rng=random.Random(41)
for _ in range(1000):
 a=''.join(rng.choices('abcé’ #-',k=rng.randrange(130)))
 b=''.join(rng.choices('abcé’ #-',k=rng.randrange(130)));cap=rng.randrange(50)
 assert distance(a,b,cap)==min(levenshtein(a,b),cap+1)
save(OUT/'WORDING_DISTANCE_CHECK.json',dict(status='PASS',command='python -B check_wording_distance.py',unicode_pairs=1000,seed=41))
print('PASS: bounded C++ and exact Python Levenshtein agree on 1000 Unicode pairs')
