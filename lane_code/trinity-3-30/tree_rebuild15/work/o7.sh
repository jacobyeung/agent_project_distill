set -e; export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -h -o "%i %P %j %T" | grep -E "cbee11a6|24a9e61c|97f8b3c867" && { echo "MY JOB QUEUED/RUNNING; stop"; exit 1; }
test -d $X/s24m1 && test ! -e $X/a24m1
cd $X/s24m1 && sha256sum -c - <<"EOS" 2>&1 | grep -v ": OK$" | head -3; echo S24M1_CHECKED $(find . -type f | wc -l)
bc07574abcab80cdce71dfadb70d20740cc850ee8fe85338ab0fc3db82adfb20  n/BUILD.json
07c1dc147b70724b98eb58134b060776690871cc24dc2c44ee0e8032d0f37700  n/SHA256SUMS.txt
45e76f57d6580a3ddec3effc80003121a7298559858b9e8cf9cdd34bd1ea3eba  n/b/a.py
6b756ba9cc7ab6b08bec07b972c08490e22e3f4ef83837d1e5a9d498772f1643  n/b/e.sh
b34eeb2bd0c5db05d2ed2056369f2838211d8a7b5134e59fb7b8d9080d5e2341  n/b/f.sh
4cb9f8df31574615bc9ac43a08924ba66a86673ba9e152e34d472dd3cc73bf03  n/b/pc.sh
a5ebc4d6e6c5ec5b183127c736fd61f996a90a5ae10694e2810781c24b0b8d0c  n/b/pl.py
985c3c63e512771656ebd9829d961376afe6ee505f29d8c0780b3dee19593551  n/b/q.sh
985c3c63e512771656ebd9829d961376afe6ee505f29d8c0780b3dee19593551  n/b/q1.sh
b080eb7b4611e96528a6134ab2e5e8daf77be8d9698415b2e5aa5b5323a39c94  n/b/rd.py
0e762c283aab28ff4ec4c5960516d3a7640ae57b98abf42c4d28473c70e3e15f  n/b/rg.py
141ef64d5dc79c463b48ea40a3ec584417753beeff093d7a8a8c9d06c28a14f8  n/b/rv.py
5d1a50004e298cb32076af6a5eccf5c2528d0680544fe8f7412551811005ad55  n/job.sh
c80063a1b0e82642c8c56215a3014c1341c589f6d679880be4a48ad8103f0c58  n/k/j.json
a80ab85c0b47dbc8f9028e2960db62e8330e580255a385d0c74b55379219115b  q/BUILD.json
b7ac3ea9f42c0d5c4681a5353cc6870a13a32a7b4efb28ed5fc947b9c7036364  q/SHA256SUMS.txt
d906a33c9a9e731dde39fb12d409dfe00d4039d85286033ff4cd191cdf9ff03d  q/b/a.py
b34eeb2bd0c5db05d2ed2056369f2838211d8a7b5134e59fb7b8d9080d5e2341  q/b/f.sh
a5ebc4d6e6c5ec5b183127c736fd61f996a90a5ae10694e2810781c24b0b8d0c  q/b/pl.py
985c3c63e512771656ebd9829d961376afe6ee505f29d8c0780b3dee19593551  q/b/q.sh
985c3c63e512771656ebd9829d961376afe6ee505f29d8c0780b3dee19593551  q/b/q1.sh
b080eb7b4611e96528a6134ab2e5e8daf77be8d9698415b2e5aa5b5323a39c94  q/b/rd.py
0e762c283aab28ff4ec4c5960516d3a7640ae57b98abf42c4d28473c70e3e15f  q/b/rg.py
80040cb7ab58e3d8a9229972d73ab31db2e2bae7fd674634c7af6414742ffb30  q/job.sh
250cf2e1dfa9ba348b4051889f8063819adba3b6bff82edf585263bb21564354  q/k/j.json
EOS
mkdir -m 700 $X/a24m1
for K in q n; do cd $X/s24m1/$K; for f in $(find . -type f | sed "s#^\./##"); do mkdir -p $X/$K/$(dirname $f); if [ -e $X/$K/$f ]; then mkdir -p $X/a24m1/over_$K/$(dirname $f); mv $X/$K/$f $X/a24m1/over_$K/$f; fi; mv $f $X/$K/$f; done; done
for f in $(cd $X/s24m1 && find u -type f); do if [ -e $X/$f ]; then cmp -s $X/s24m1/$f $X/$f || { echo "DIFFERS $f"; exit 1; }; else mv $X/s24m1/$f $X/$f; fi; done
for K in q n; do cd $X/$K; for f in $(find . -type f | sed 's#^\./##'); do case $f in BUILD.json|SHA256SUMS.txt) ;; *) grep -q "  $f\$" SHA256SUMS.txt || { mkdir -p $X/a24m1/extra_$K/$(dirname $f); mv $f $X/a24m1/extra_$K/$f; echo "moved extra $K/$f"; } ;; esac; done
 echo "$K seal $(sha256sum SHA256SUMS.txt | cut -c1-16) bad $(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$') files $(find . -type f | wc -l) lines $(wc -l < SHA256SUMS.txt) pyc $(find . -name __pycache__ | wc -l)"; sha256sum -c SHA256SUMS.txt 2>&1 | grep -v ": OK$" | head -5; done

echo JR $(sha256sum $X/jr.sh | cut -c1-16) JRW $(sha256sum $X/jrw.sh | cut -c1-16)
sbatch $X/jrw.sh; sleep 5; squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R" | grep -E "24a9e61c|JOBID"
