import hashlib, json, os, subprocess, tarfile, time
E = '/lab_data/tarrlab/jacoby/agent_project/aws_evac'
OUT = E + '/d/w19/evid/pins2'
W5 = ('/lab_data/tarrlab/jacoby/gcs_evac_20261111/wave5/q8/8865619b/state-copy/169097/'
      'metadata-only/469ddece/step000160/f878645673d16bf36ed7ba23263e18ae')
PARTS = ['metadata.tar.part0%d-of-04' % i for i in range(4)]
P = 'inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/prepared/'
WANT1 = {P + n for n in ('pointing_scene_indices.json', 'routing_scene_indices.json', 'vqa_scene_indices.json',
                         'vqa_indices.json', 'pose_scene_order.json', 'pose_mix_order.json', 'receipt.json', 's1_receipt.json')}
rep = {'host': os.uname()[1]}
os.makedirs(OUT, exist_ok=True)
def save(name, data):
    p = OUT + '/' + name.replace('/', '__')
    with open(p, 'wb') as f: f.write(data)
    return {'dest': p, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
cat = subprocess.Popen(['cat'] + [W5 + '/' + n for n in PARTS], stdout=subprocess.PIPE, bufsize=1 << 20)
r = {}
with tarfile.open(fileobj=cat.stdout, mode='r|') as tf:
    all_names = []
    for m in tf:
        all_names.append((m.name, m.size))
        if m.name in WANT1:
            r[m.name] = save('8865619b/runs/469ddece/' + m.name, tf.extractfile(m).read())
cat.wait()
rep['statecopy'] = r
rep['statecopy_members'] = all_names
for tarp, wants in ((E + '/d/new/e84d901c_z.tar', ('z/eb035f92.json', 'z/986ba20f.npz')),
                    (E + '/d/new/544dcf9b.tar', ('in/30c516bf.json',))):
    res = {}
    with tarfile.open(tarp, 'r:') as tf:
        for m in tf:
            if any(m.name.endswith(w) for w in wants):
                res[m.name] = save(m.name, tf.extractfile(m).read()) if m.size < (200 << 20) else {'size': m.size}
    rep[os.path.basename(tarp)] = res
    print(tarp, res, flush=True)
fnd = subprocess.run('timeout 600 find %s/d %s/t1 %s/t3 %s/t4 %s/t5 %s/gcs /lab_data/tarrlab/jacoby/gcs_evac_20261111 -maxdepth 6 \\( -iname "*sam3*" -o -iname "*g3t*" \\) -printf "%%s %%p\\n"' % ((E,) * 6),
                     shell=True, stdout=subprocess.PIPE, universal_newlines=True).stdout
rep['find_sam3_g3t'] = fnd.splitlines()[:200]
json.dump(rep, open(OUT + '/REPORT.json', 'w'), indent=1)
print('REPORT_JSON', json.dumps({k: v for k, v in rep.items() if k != 'statecopy_members'}), flush=True)
