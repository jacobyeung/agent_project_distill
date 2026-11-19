from pathlib import Path
import sys,tarfile
sys.path.insert(0,'kit/files');import count_guard as G
p=Path('out/MISSING_INPUTS.json');d=G.read(p);fm=G.read('kit/work/FIXTURE_MANIFEST.json')
archive=Path('/scratch/jjyeung/n30_mirror/b05_owngrd/B05_K1_TEACHER_LABELS.tar')
wanted={Path(f['path']).name:f for c in fm['captures'] for f in c['frames']};matches=[]
with tarfile.open(archive) as t:
 for m in t:
  if m.isfile() and Path(m.name).name in wanted:matches.append(m.name)
# No scenes or path mapping is inferred from missing PNGs.
d['fixture_archive_matches']=matches;d['fixture_archive_searched']=str(archive);d['inputs_sha256'][str(__file__)]=G.sha(__file__)
G.write(p,d)
G.write('out/PILOT_STATUS.json',dict(status='MISSING',unavailable_full_table='kit/work/k1_final.py',missing_inputs=d['pilot_missing'],available_reproduction='K1 raw labels and teacher outputs; training selection and independent reviewer label/oracle audit',inputs_sha256={str(p):G.sha(p),'kit/work/k1_final.py':G.sha('kit/work/k1_final.py')}))
print('fixture archive matches',len(matches),'missing fixture paths',len(d['fixture_missing']))
