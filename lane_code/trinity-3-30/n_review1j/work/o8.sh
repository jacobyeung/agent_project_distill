TZ=UTC date +%TZ; TZ=UTC squeue -j 174134 -h -o '%i %T %N %M' < /dev/null
timeout 120 srun --overlap --jobid 174134 -N1 -n1 nice -n 15 bash -c '
N=/tmp/q_22c714e1_174134; cd $N/p/q 2>&1 && ls | tr "\n" " "; echo; ls -la sc 2>&1 | head; ls sc/* 2>/dev/null | head -30
echo == dbg; ls /tmp/a15_dbg_174134 2>&1 | head; find /tmp/a15_dbg_174134 -maxdepth 3 -name "*_scene_*" 2>/dev/null | head
echo == u sizes; for h in 30612832cc84ad83f9500ecbeac57704767568ff24482475feb42a92c7f166b8 1e7b491b810bd45b47a6d0e02be2f123e0ba8f8851f3e48fc1164f15611c9201 4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84; do ls -la $N/u/$h 2>&1; done
python3 -c "import json;d=json.load(open(\"sc/0.json\"));print(list(d)); print(json.dumps(d.get(\"withheld_training_rows\"))[:3000])" 2>&1
python3 -c "import json;d=json.load(open(\"sc/2.json\"));print(list(d)); print(json.dumps(d.get(\"receipts\"))[:1500]); print(json.dumps(d.get(\"scene_coverage\"))[:1500])" 2>&1
' < /dev/null
