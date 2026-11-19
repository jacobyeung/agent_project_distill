import gzip, hashlib, json, os, sqlite3, sys, tarfile, time
C = '/project/community/jjyeung/distill/okit/in/cr'
OUT = sys.argv[1]
TARS = ['rt_b8b60bcef027.tar', 'rt_81d2cd86786b.tar', 'rt_ca97b9979a7b.tar', 'rt_fb6bf34c7748.tar', 'rt_abd1d506a71c.tar']
KEYS = ('scene', 'scene_id', 'scene_name', 'room', 'room_id', 'video', 'video_id', 'video_path', 'recording',
        'recording_id', 'dataset', 'source', 'source_dataset', 'qid', 'question_id', 'split', 'stream', 'family',
        'capture', 'capture_id', 'question_type', 'task')
rep = {'host': os.uname()[1], 'start': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'tars': {}}
for t in TARS:
    hs, hm, n = hashlib.sha256(), hashlib.md5(), 0
    with open(C + '/' + t, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            hs.update(b); hm.update(b); n += len(b)
    with tarfile.open(C + '/' + t) as tf:
        mem = [(m.name, m.size) for m in tf.getmembers()]
    rep['tars'][t] = {'bytes': n, 'sha256': hs.hexdigest(), 'md5_hex': hm.hexdigest(), 'members': mem}
    print(t, n, hs.hexdigest(), flush=True)
def pick(obj, prefix):
    out = {}
    if isinstance(obj, dict):
        for k in KEYS:
            v = obj.get(k)
            if isinstance(v, (str, int)) and not isinstance(v, bool):
                out[prefix + k] = v
        for k2, v2 in obj.items():
            if isinstance(v2, dict):
                for k in KEYS:
                    v = v2.get(k)
                    if isinstance(v, (str, int)) and not isinstance(v, bool) and (prefix + k) not in out:
                        out[prefix + k2 + '.' + k] = v
    return out
with tarfile.open(C + '/rt_b8b60bcef027.tar') as tf:
    data = tf.extractfile('ap/5e1d07a4/f/h/r16/rows.sqlite').read()
rep['r16_rows_sha256'] = hashlib.sha256(data).hexdigest()
con = sqlite3.connect(':memory:'); con.deserialize(data); del data
keyc, n, sc = {}, 0, {}
dst = OUT + '/5e1d07a4_f_h_r16.scenes.jsonl.gz'
with gzip.open(dst, 'wt') as o:
    for i, row, target in con.execute('SELECT i, row, target FROM rows ORDER BY i'):
        n += 1; r = {}
        try:
            rj = json.loads(row)
            if n <= 2000 and isinstance(rj, dict):
                for k in rj: keyc[k] = keyc.get(k, 0) + 1
            r.update(pick(rj, ''))
        except Exception as e:
            r['row_error'] = str(e)[:80]
        try: r.update(pick(json.loads(target), 't.'))
        except Exception: pass
        r['i'] = i
        s = r.get('scene') or r.get('scene_id') or r.get('video_id') or r.get('video')
        sc[str(s)] = sc.get(str(s), 0) + 1
        o.write(json.dumps(r, sort_keys=True) + '\n')
h = hashlib.sha256(open(dst, 'rb').read()).hexdigest()
rep['r16_scenes'] = {'rows': n, 'distinct_scenes': len(sc), 'scene_none_rows': sc.get('None', 0), 'row_keys_first2000': keyc,
                     'out': dst, 'out_bytes': os.path.getsize(dst), 'out_sha256': h}
rep['end'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
json.dump(rep, open(OUT + '/REPORT.json', 'w'), indent=1, sort_keys=True)
print('DONE', json.dumps(rep['r16_scenes']), flush=True)
