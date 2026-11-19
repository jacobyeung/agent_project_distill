# Load routed distance/room rows at steps 200 and 544 through san_kit and cache a compact pickle in /tmp (scratch only).
import os, sys, pickle, time
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1'); os.environ.setdefault('OMP_NUM_THREADS', '1')
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
t = time.time(); out = {}
for step in (200, 544):
    out[('A', step)] = K.routed(step, types=['object_abs_distance', 'room_size_estimation'], part='A')
    out[('B', step)] = K.routed(step, part='B')
    print(step, 'A', len(out[('A', step)]), 'B', len(out[('B', step)]), round(time.time() - t, 1), 's', flush=True)
out['SOURCES'] = sorted(set(K.SOURCES))
pickle.dump(out, open('/tmp/san_dd_dist/routed.pkl', 'wb'))
print('sources', len(out['SOURCES'])); [print(' ', s) for s in out['SOURCES'][:30]]
