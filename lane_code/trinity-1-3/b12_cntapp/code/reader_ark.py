"""Governed reader (child of the stopped root): for each ARKit capture, list lowres_depth once, pick the 32 pins
(timestamp-sorted index, the K1 rule), and stream annotation + traj + 32 depth PNGs + 32 pincams as a tar to stdout.
Paced to <= ~100 NFS files/s on top of the byte limiter. Listings are saved on /scratch for the builder."""
import json, os, subprocess, sys, time
jobs = json.load(open(sys.argv[1])); lst = sys.argv[2]; pace = float(sys.argv[3]) if len(sys.argv) > 3 else 0.7
A = '/data3/shared/datasets/arkitscenes/3dod/Training'
os.makedirs(lst, exist_ok=True)
log = open(lst + '/../reader_ark.log', 'a')
def ts(s): return float(s.split('_')[1].rsplit('.', 1)[0])
for j in jobs:
    t0 = time.time(); i = j['id']
    try:
        names = sorted(os.listdir(f'{A}/{i}/{i}_frames/lowres_depth'), key=ts)
        open(f'{lst}/{i}.depth_list.txt', 'w').write('\n'.join(names) + '\n')
        if max(j['pins']) >= len(names):
            log.write(json.dumps(dict(id=i, status='pin beyond depth list', n=len(names))) + '\n'); continue
        f = [f'{i}/{i}_3dod_annotation.json', f'{i}/{i}_frames/lowres_wide.traj']
        f += [f'{i}/{i}_frames/lowres_depth/' + names[k] for k in j['pins']]
        f += [f'{i}/{i}_frames/lowres_wide_intrinsics/' + names[k][:-4] + '.pincam' for k in j['pins']]
        open(f'{lst}/{i}.files.txt', 'w').write('\n'.join(f) + '\n')
        sys.stdout.flush()
        r = subprocess.run(['tar', 'cf', '-', '--ignore-failed-read', '-C', A, '-T', f'{lst}/{i}.files.txt'], stdout=sys.stdout.buffer, stderr=subprocess.PIPE)
        log.write(json.dumps(dict(id=i, status='ok' if r.returncode == 0 else 'tar rc %d' % r.returncode, n=len(names), err=r.stderr.decode()[-300:])) + '\n')
    except Exception as e:
        log.write(json.dumps(dict(id=i, status='error', err=str(e)[-300:])) + '\n')
    log.flush()
    dt = time.time() - t0
    if dt < pace: time.sleep(pace - dt)
log.write('READER_DONE\n'); log.close()
