# streamed variant: s<tag>.tar.part already on Orchard (tssh cat | ossh cat). usage: python3 mkcand.py <tag e.g. 24m4s> <stage.out> <job-name> > oX.sh
import sys,re
tag,out,jn=sys.argv[1:4]; s=open(out).read().split('\n')
tarsha=[l.split()[0] for l in s if l.endswith('/work/s%s.tar'%tag) and len(l.split()[0])==64][0]
seals={m.group(2):m.group(1) for l in s for m in [re.match(r'([0-9a-f]{64})  (n|q|qd)/SHA256SUMS.txt$',l)] if m}
qd=seals['qd'][:8]; C='c_'+qd+(sys.argv[4] if len(sys.argv)>4 else '')
print(f'''set -e; export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X; test -f s{tag}.tar.part && test ! -e s{tag}.tar && test ! -e s{tag} && test ! -e {C} || {{ echo EXISTS; exit 1; }}
squeue -u $USER -h -o "%j" | grep -q {jn[10:]} && {{ echo QUEUED; exit 1; }}
mv s{tag}.tar.part s{tag}.tar
[ "$(sha256sum s{tag}.tar | cut -c1-64)" = {tarsha} ] || {{ echo TAR BAD; exit 1; }}
mkdir -m 700 s{tag} && tar xf s{tag}.tar -C s{tag} && echo S {tag} $(find s{tag} -type f | wc -l)
if [ -d s{tag}/u ]; then for f in $(ls s{tag}/u); do if [ -e u/$f ]; then cmp -s u/$f s{tag}/u/$f || {{ echo U DIFF $f; exit 1; }}; else cp s{tag}/u/$f u/$f && echo U ADDED $f; fi; done; fi
mkdir -m 700 {C} && cp -a qd {C}/qd && cp -a s{tag}/qd/. {C}/qd/
cd {C}/qd; for f in $(find . -type f | sed 's#^\\./##'); do case $f in BUILD.json|SHA256SUMS.txt) ;; *) grep -q "  $f\\$" SHA256SUMS.txt || {{ echo "EXTRA $f"; exit 1; }} ;; esac; done
[ "$(sha256sum SHA256SUMS.txt | cut -c1-64)" = {seals['qd']} ] && [ "$(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$')" = 0 ] && [ -z "$(find . -name __pycache__)" ] || {{ echo CAND SEAL BAD; exit 1; }}
echo CAND {C}/qd seal $(sha256sum SHA256SUMS.txt | cut -c1-16) files $(find . -type f | wc -l)
cd $X; mkdir -m 700 {C}/rcj && cp -a rcj/. {C}/rcj/ && if [ -d s{tag}/rcj ]; then cp -a s{tag}/rcj/. {C}/rcj/; fi; echo CAND RCJ; (cd {C}/rcj && sha256sum * | cut -c1-16,65-); RS=$X/rcj/rcj.sh; [ -f s{tag}/rcj/rcj.sh ] && RS=$X/s{tag}/rcj/rcj.sh; sed "s#^ROOT=/project/community/jjyeung/okh7/x_22c714e1/qd\\$#ROOT=$X/{C}/qd#; s#^H=/project/community/jjyeung/okh7/x_22c714e1/rcj\\$#H=$X/{C}/rcj#" $RS > {C}/rcj.sh; chmod 700 {C}/rcj.sh; grep -n "^ROOT=\|^H=" {C}/rcj.sh; diff rcj/rcj.sh {C}/rcj.sh | wc -l
for f in x.py:d8517333228a4cac pc.py:bd87252b711f9a2b nd.py:eb0ba92e7e989752 ch.py:16d7210bbca556a0 f.json:37cbc05d134a0129 ps.py:6945292e167d9f60 P_SAMPLE_I.json:fff742bb8ca70d50; do [ "$(sha256sum rcj/${{f%%:*}} | cut -c1-16)" = "${{f##*:}}" ] || {{ echo "BAD rcj/$f"; exit 1; }}; done
[ "$(sha256sum qd/SHA256SUMS.txt | cut -c1-16)" = 221d17824d467daa ] || {{ echo REVIEWED QD CHANGED; exit 1; }}
cd {C}/qd && sbatch --job-name={jn} ../rcj.sh r; sleep 15
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"''')
