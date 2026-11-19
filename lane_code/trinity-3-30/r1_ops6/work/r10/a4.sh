export TZ=UTC; date -u +%T
ls -d /project/community/jjyeung/okh7/*/runs/469ddece* /project/community/jjyeung/*/runs/469ddece* /project/community/jjyeung/okh7/*/469ddece* 2>/dev/null | head
ls -la /project/community/jjyeung/okh7/r/673bc60f/ | head; head -c 600 /project/community/jjyeung/okh7/r/673bc60f/A.json; echo
timeout 60 tar tvf /project/community/jjyeung/okh7/r/673bc60f/A.tar 2>/dev/null | head -30
timeout 200 srun --overlap --jobid 172660 -n1 -N1 timeout -k 5 180 nice -n 19 ionice -c3 bash -c 'V=/tmp/jjyeung/a_6ed2c7aa/root/c7d31ddd/venvs/rwtrain_torch211_cu129; ls /tmp/jjyeung/a_6ed2c7aa/runs/; ls /tmp/jjyeung/a_6ed2c7aa/root/aws/u/ap/ | head -30; OMP_NUM_THREADS=2 PYTHONPATH=$(ls -d $V/lib/python3*/site-packages) nice -n 19 /usr/bin/python3.12 -s -c "
import torch,collections
o=torch.load(\"/tmp/jjyeung/a_6ed2c7aa/runs/6ed2c7aa/m400/heads.pt\",map_location=\"cpu\",mmap=True,weights_only=False)
c=collections.Counter(\".\".join(k.split(\".\")[:3]) for k in o); print(sorted(c.items()))
"' 2>&1 | grep -v -i cgroup | head -60
