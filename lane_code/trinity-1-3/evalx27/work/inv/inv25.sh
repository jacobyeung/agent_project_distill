set +e
df -h /tmp /home/jjyeung/okit/tmp | cat; nproc; uptime; free -g | head -2
E=/home/jjyeung/okit/tmp/x27env; mkdir -p $E
cat /home/jjyeung/okit/p/d59945c1/4fe70504.00 /home/jjyeung/okit/p/d59945c1/4fe70504.01 | tar xf - -C $E 2>&1 | tail -2
ls $E/sj/envs/p1cpu/bin | head; cat $E/sj/envs/p1cpu/pyvenv.cfg
P=$E/sj/envs/p1cpu/bin/python
ls -la $P
$P -c "import sys;print(sys.version)" 2>&1 | tail -1
$P -c "import av,numpy,PIL;print(av.__version__,numpy.__version__,PIL.__version__)" 2>&1 | tail -1
$P -c "import transformers;print(transformers.__version__)" 2>&1 | tail -1
du -sh $E
