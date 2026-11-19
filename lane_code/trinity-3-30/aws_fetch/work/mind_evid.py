import gzip, hashlib, json, os, sqlite3, subprocess, sys, tarfile, time
from multiprocessing import Pool

E = '/lab_data/tarrlab/jacoby/agent_project/aws_evac'
OUT = E + '/d/w19/evid'
W5 = ('/lab_data/tarrlab/jacoby/gcs_evac_20261111/wave5/q8/8865619b/state-copy/169097/'
      'metadata-only/469ddece/step000160/f878645673d16bf36ed7ba23263e18ae')
PARTS = [('metadata.tar.part00-of-04', 'fa861e27904159412c005f4e62a1c3e9945ab6b1712bde6684863d79360af6ff'),
         ('metadata.tar.part01-of-04', '3d6c079ccb667b19e0bc82d95d5dd79fc6abc7fe9d77cac11319a4220c6fb749'),
         ('metadata.tar.part02-of-04', 'e85f307ad8a861e8fa77e8d425167c2c89a038a47008a7c38f8c21af1cc9b391'),
         ('metadata.tar.part03-of-04', '9c0c9f7bc2201b245ea4938dd31f0db553b5f0d5896a57f31e56375dd2b21f55')]
PREP = 'inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/'
WANT = {PREP + s + '/' + f: (s, f) for s in ('pointing', 'routing', 'vqa') for f in ('rows.sqlite', 'receipt.json')}
PINS = {'pointing': 'faa0cfc43bed88bf0f2dad6da57bc57c7dcfb8c3aba65cecc045a3de327cc85d',
        'routing': 'c48d5b6201c935e2de8e985d2d8a163d9bb46603e693e790733e3c86fe59db53',
        'vqa': '5deb54bc4ef34c46371916feb2ab7fc83a707666cc36c5f2749b144647caa81d',
        'a2v3': 'b32359ce256a567912d6436fac95dcab78bcef3bb2e1154cabdca57bacdc5320',
        'a3v2': '0b95850a2dec57ec6702ca72cd198eb5afdcdcdd5f711a76a878104e30ec3571'}
RATE = 200e6
KEYS = ('scene', 'scene_id', 'scene_name', 'room', 'room_id', 'video', 'video_id', 'video_path', 'recording',
        'recording_id', 'dataset', 'source', 'source_dataset', 'qid', 'question_id', 'split', 'stream', 'family',
        'capture', 'capture_id', 'question_type', 'task')
REPORT = {'host': os.uname()[1], 'start': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def throttled_copy(src, dst_path):
    h = hashlib.sha256(); n = 0; t0 = time.time()
    with open(dst_path + '.part', 'wb') as o:
        while True:
            b = src.read(8 << 20)
            if not b:
                break
            o.write(b); h.update(b); n += len(b)
            ahead = n / RATE - (time.time() - t0)
            if ahead > 0:
                time.sleep(ahead)
    os.rename(dst_path + '.part', dst_path)
    return n, h.hexdigest()


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def step_parts():
    out = []
    for name, pin in PARTS:
        s = sha_file(W5 + '/' + name)
        out.append({'part': name, 'sha256': s, 'ok': s == pin})
        log('part', name, s == pin)
    REPORT['wave5_parts'] = out
    return all(x['ok'] for x in out)


def step_extract_8865():
    d = OUT + '/8865619b_469ddece_inputs'
    os.makedirs(d, exist_ok=True)
    cat = subprocess.Popen(['cat'] + [W5 + '/' + n for n, _ in PARTS], stdout=subprocess.PIPE, bufsize=1 << 20)
    res = {}
    with tarfile.open(fileobj=cat.stdout, mode='r|') as tf:
        for m in tf:
            if m.name in WANT:
                s, f = WANT[m.name]
                dst = '%s/%s_%s' % (d, s, f)
                n, h = throttled_copy(tf.extractfile(m), dst)
                res[m.name] = {'dest': dst, 'bytes': n, 'sha256': h,
                               'pin_ok': (h == PINS[s]) if f == 'rows.sqlite' else None}
                log('extracted', m.name, n, h[:12])
    cat.wait()
    REPORT['extract_8865619b'] = res


def step_extract_a2v3():
    tarp = E + '/d/w19/pose/a2/pda2_001.tar'
    dst = OUT + '/f02f16ad_s_a2v3_rows.sqlite'
    with tarfile.open(tarp, 'r:') as tf:
        names = tf.getnames()
        mem = [n for n in names if n.endswith('s/a2v3/rows.sqlite')]
        REPORT['pda2_001_members'] = names[:50]
        m = tf.getmember(mem[0])
        n, h = throttled_copy(tf.extractfile(m), dst)
    REPORT['extract_a2v3'] = {'member': mem[0], 'dest': dst, 'bytes': n, 'sha256': h, 'pin_ok': h == PINS['a2v3']}
    log('a2v3', n, h[:12], h == PINS['a2v3'])


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


def scenes(args):
    label, path = args
    t0 = time.time()
    con = sqlite3.connect('file:%s?mode=ro&immutable=1' % path, uri=True)
    keycensus = {}; nrows = 0; scene_counts = {}
    dst = OUT + '/scene_cols/%s.scenes.jsonl.gz' % label
    with gzip.open(dst + '.part', 'wt') as o:
        for i, row, target in con.execute('SELECT i, row, target FROM rows ORDER BY i'):
            nrows += 1
            r = {}
            try:
                rj = json.loads(row)
                if nrows <= 2000 and isinstance(rj, dict):
                    for k in rj:
                        keycensus[k] = keycensus.get(k, 0) + 1
                r.update(pick(rj, ''))
            except Exception as e:
                r['row_error'] = str(e)[:80]
            try:
                r.update(pick(json.loads(target), 't.'))
            except Exception:
                pass
            r['i'] = i
            sc = r.get('scene') or r.get('scene_id') or r.get('video_id') or r.get('video')
            scene_counts[str(sc)] = scene_counts.get(str(sc), 0) + 1
            o.write(json.dumps(r, sort_keys=True) + '\n')
    os.rename(dst + '.part', dst)
    return label, {'path': path, 'rows': nrows, 'distinct_scenes': len(scene_counts),
                   'scene_none_rows': scene_counts.get('None', 0), 'row_keys_first2000': keycensus,
                   'out': dst, 'out_bytes': os.path.getsize(dst), 'out_sha256': sha_file(dst),
                   'secs': round(time.time() - t0, 1)}


def main():
    os.makedirs(OUT + '/scene_cols', exist_ok=True)
    ok = step_parts()
    if ok:
        step_extract_8865()
    step_extract_a2v3()
    jobs = []
    for s in ('pointing', 'routing', 'vqa'):
        p = OUT + '/8865619b_469ddece_inputs/%s_rows.sqlite' % s
        if os.path.exists(p):
            jobs.append(('8865619b_469ddece_%s' % s, p))
    jobs.append(('f02f16ad_s_a2v3', OUT + '/f02f16ad_s_a2v3_rows.sqlite'))
    jobs.append(('f02f16ad_s_a3v2', E + '/d/w19/pose/a2/ap_f02f16ad_s_a3v2_rows.sqlite'))
    with Pool(len(jobs)) as pool:
        REPORT['scenes'] = dict(pool.map(scenes, jobs))
    REPORT['end'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    with open(OUT + '/scene_cols/REPORT.json', 'w') as f:
        json.dump(REPORT, f, indent=1, sort_keys=True)
    print('REPORT_JSON ' + json.dumps(REPORT, sort_keys=True))


if __name__ == '__main__':
    main()
