"""Index the k6tk frame store's tar parts on Orchard: sha -> (tar path, data offset, size). Reads tar headers only (seek mode).
Writes /tmp/nvk1/work/k6tk_index.tsv.gz. usage: python3 k6tk_index.py"""
import tarfile, gzip, json, os, time
P = '/project/community/jjyeung/cp4tk_fr/k6tk/parts'; OUT = '/tmp/nvk1/work/k6tk_index.tsv.gz'; os.makedirs('/tmp/nvk1/work', exist_ok=True)
t0 = time.time(); n = 0
with gzip.open(OUT + '.tmp', 'wt') as out:
    for part in sorted(os.listdir(P)):
        d = os.path.join(P, part)
        for f in sorted(os.listdir(d)):
            if not f.endswith('.tar'): continue
            p = os.path.join(d, f)
            with tarfile.open(p, 'r:') as tf:
                for m in tf:
                    if m.isfile():
                        out.write('%s\t%s\t%d\t%d\n' % (os.path.basename(m.name).split('.')[0], p, m.offset_data, m.size)); n += 1
            print(f, n, round(time.time() - t0, 1), flush=True)
os.replace(OUT + '.tmp', OUT); print('members', n, 'seconds', round(time.time() - t0, 1))
