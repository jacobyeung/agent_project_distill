set -e; export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -h -o "%i %P %j %T" | grep cbee11a6 && { echo "MY JOB QUEUED/RUNNING; stop"; exit 1; }
test -d $X/s24 && test -d $X/s24c && test ! -e $X/a24
cd $X/s24c && sha256sum -c - <<"EOS" 2>&1 | grep -v ": OK$" | head -3; echo S24C_CHECKED
11d66a301ab8423611bbc35416da7a97b54d2b8edd1da0ba9e64bfbd83046d20  n/BUILD.json
bff6d42cd55558534be50305607f063b4f7f5bf37fe3be670746aa632f992699  n/SHA256SUMS.txt
6b756ba9cc7ab6b08bec07b972c08490e22e3f4ef83837d1e5a9d498772f1643  n/b/e.sh
d08c7e535bf2aa3c20b0af35c7dd353f5be42bce7edfbc395e8485218d140f32  n/b/f.sh
e397ea709f4376236db6741bc279ae6f1bd2ef72d78db23466a45bf7df58b6bf  n/b/g.py
dad7a085f81c6c9fd0ef5b89e18181e9519f1fcf9975b18ba806c2dbc3c41a59  n/b/o.py
985c3c63e512771656ebd9829d961376afe6ee505f29d8c0780b3dee19593551  n/b/q.sh
985c3c63e512771656ebd9829d961376afe6ee505f29d8c0780b3dee19593551  n/b/q1.sh
962e0839a3b0084f6c4ec04b382ff28186a7ec39825927d6dfe4ab0c074938de  n/b/resolve.py
8fcb8426125d1b4ac51b8e1bc47e30b401f5f4466a3a2587eb706497b583687e  n/b/t.py
de59feda7fda87c5bfeadfbb662230ced6df44db73d88363441c4f21d2811dc7  n/b/u.py
9cd3403d1a1e86558fd38425e2ac6f7f69958fba1fb0e74cbae6bc154e31e9c4  n/b/z.py
a0ecf3d62529b08965dc268cd7c6118dbf48716aa36f1dba056fe4cbe81dabd6  n/job.sh
63d3b5f36736f42f8675435baaf94b0262f23bc91a81ca49080ac4d5852fdafc  n/k/7.json
70ea89a808d2a401c9151de9419fd5b0d10690e371301149ee10bc45470695cb  n/k/a.json
0283bc8cc68979f06c66c80fefacc94edeeab7326e48b489be80e1d15115adb9  n/k/c.json
09be8a9dd9fbcbaabaa9a82f267cb6f502a8269d9c6129994e067150dcdc6353  n/k/c0.json
86c8f50fe96c266c536bc92ee1510b7858137914051b172331f5be4130b5d19e  n/k/j.json
f21e197474f88f3a75b1613a9fc588d479f2bded43218f740f744d62226c38a8  n/k/n.json
8bf54097e3e14aacacb7bfd9d755a63278c3bed4ef39bd3a6fb2b5354c51d9ad  n/k/p.json
53c80ea73e0d664811af24fdf7d4c7be6fb3ea33617136fe9060f383a23ee4d4  n/k/r.json
ae0978ee4935b185832baf3bb6942015480ebfcf87a38dce569dfeb5bffdbf07  n/k/t_e047002134f979bd.tar
28e6db34613b8f3bc538de2a14ebea0a051c4aca77334a630beb829ef027a52e  q/BUILD.json
edb324ff474c598328542084d549e6a8540eed7127d63e2b1f886c64a0865c5f  q/SHA256SUMS.txt
d08c7e535bf2aa3c20b0af35c7dd353f5be42bce7edfbc395e8485218d140f32  q/b/f.sh
e397ea709f4376236db6741bc279ae6f1bd2ef72d78db23466a45bf7df58b6bf  q/b/g.py
dad7a085f81c6c9fd0ef5b89e18181e9519f1fcf9975b18ba806c2dbc3c41a59  q/b/o.py
985c3c63e512771656ebd9829d961376afe6ee505f29d8c0780b3dee19593551  q/b/q.sh
985c3c63e512771656ebd9829d961376afe6ee505f29d8c0780b3dee19593551  q/b/q1.sh
962e0839a3b0084f6c4ec04b382ff28186a7ec39825927d6dfe4ab0c074938de  q/b/resolve.py
9cd3403d1a1e86558fd38425e2ac6f7f69958fba1fb0e74cbae6bc154e31e9c4  q/b/z.py
22ee9a866c4d9c7d9d4b348a4cfbff25b03f6e2207cfd02921b87f967e057435  q/job.sh
63d3b5f36736f42f8675435baaf94b0262f23bc91a81ca49080ac4d5852fdafc  q/k/7.json
70ea89a808d2a401c9151de9419fd5b0d10690e371301149ee10bc45470695cb  q/k/a.json
203cfb8480b88c3063dc199f786324b855da39772824258d60352b408b5945f7  q/k/c.json
09be8a9dd9fbcbaabaa9a82f267cb6f502a8269d9c6129994e067150dcdc6353  q/k/c0.json
0fa3e9dc2ed4beda1f0969d4e6ea96769ef85424669288c692aa10c744518a2b  q/k/j.json
812806f4cd9652e62397b8d02814cd1f9eb63f616b03610394afc5a2884e6e6f  q/k/n.json
8bf54097e3e14aacacb7bfd9d755a63278c3bed4ef39bd3a6fb2b5354c51d9ad  q/k/p.json
ae0978ee4935b185832baf3bb6942015480ebfcf87a38dce569dfeb5bffdbf07  q/k/t_e047002134f979bd.tar
EOS
mkdir -m 700 $X/a24 && mv $X/q $X/a24/q_23d
test ! -e $X/n
mv $X/s24/q $X/q && mv $X/s24/n $X/n
for K in q n; do cd $X/s24c/$K; for f in $(find . -type f | sed "s#^\./##"); do mkdir -p $X/$K/$(dirname $f); if [ -e $X/$K/$f ]; then mkdir -p $X/a24/over_$K/$(dirname $f); mv $X/$K/$f $X/a24/over_$K/$f; fi; mv $f $X/$K/$f; done; done
for f in $(cd $X/s24 && find u -type f); do if [ -e $X/$f ]; then cmp -s $X/s24/$f $X/$f || { echo "DIFFERS $f"; exit 1; }; else mv $X/s24/$f $X/$f; fi; done
for K in q n; do cd $X/$K; for f in $(find . -type f | sed 's#^\./##'); do case $f in BUILD.json|SHA256SUMS.txt) ;; *) grep -q "  $f\$" SHA256SUMS.txt || { mkdir -p $X/a24/extra_$K/$(dirname $f); mv $f $X/a24/extra_$K/$f; echo "moved extra $K/$f"; } ;; esac; done
 echo "$K seal $(sha256sum SHA256SUMS.txt | cut -c1-16) bad $(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$') files $(find . -type f | wc -l) lines $(wc -l < SHA256SUMS.txt) pyc $(find . -name __pycache__ | wc -l)"; done
