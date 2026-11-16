cd /scratch/jjyeung/orch_cd/mp3d_dl
python3 - <<'PY'
import zipfile, collections
z = zipfile.ZipFile('dl/tailprobe.zip')
inf = z.infolist(); print("members", len(inf))
ext = collections.Counter(i.filename.rsplit('.',1)[-1] for i in inf); print(ext.most_common(12))
sc = collections.defaultdict(int)
for i in inf: 
    p=i.filename.split('/')
    if len(p)>=3: sc[p[-2]]+=i.file_size
print("scenes", len(sc)); print([i.filename for i in inf[:8]])
print("navmesh", sum(1 for i in inf if i.filename.endswith('.navmesh')), "glb", sum(1 for i in inf if i.filename.endswith('.glb')))
print("glb+navmesh bytes", sum(i.file_size for i in inf if i.filename.endswith(('.glb','.navmesh'))))
PY
cat bin/extract_partial.py | head -30
ls -la /scratch/jjyeung/mp3d/e0_scenes/mp3d/8194nk5LbLH /scratch/jjyeung/mp3d/v1/tasks
cat /scratch/jjyeung/mp3d/datasets/R2R_VLNCE_v1-3_preprocessed.zip.sha256
