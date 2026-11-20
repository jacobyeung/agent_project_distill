"""Header-only index of the needed frames in the 12 frame-store shards: sha, shard path, data offset, size. No frame bytes are copied."""
import gzip, os, tarfile, time
J = '/project/community/jjyeung/4f5e45fe5d74c'; P = '/project/community/jjyeung/cp4tk_fr/k6tk/parts'
want = set(gzip.open(J + '/hold/WANT_k6.txt.gz', 'rt').read().split()); t0 = time.time(); n = 0
os.makedirs(J + '/idx', exist_ok=True)
with gzip.open(J + '/idx/k6.tsv.gz.tmp', 'wt') as out:
    for part in sorted(os.listdir(P)):
        for f in sorted(os.listdir(os.path.join(P, part))):
            if not f.endswith('.tar'): continue
            p = os.path.join(P, part, f)
            with tarfile.open(p, 'r:') as tf:
                for m in tf:
                    h = os.path.basename(m.name).split('.')[0]
                    if m.isfile() and h in want: out.write('%s\t%s\t%d\t%d\n' % (h, p, m.offset_data, m.size)); n += 1
            print(f, n, round(time.time() - t0, 1), flush=True)
os.replace(J + '/idx/k6.tsv.gz.tmp', J + '/idx/k6.tsv.gz'); print('want', len(want), 'indexed', n, 'seconds', round(time.time() - t0, 1))
