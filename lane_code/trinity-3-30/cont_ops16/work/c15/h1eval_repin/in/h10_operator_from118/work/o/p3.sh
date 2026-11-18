export TZ=UTC
P=/project/community/jjyeung; W=$P/okh7/e6fc152498
mkdir -p -m 700 $W
echo "== M544_SOURCE"; cat $P/okh7/i_bb09a77d/M544_SOURCE.json; echo; head -c 1500 $P/okh7/i_bb09a77d/derive.result.json; echo
echo "== hf g3t"; ls -laR $P/cache/hf/hub/models--thatbrguy--g3t 2>&1 | head -30
echo "== terminators"
for d in /home/jjyeung $P/cp4tk_rt $P/cp4tk_launch $P/okh7/j; do timeout 40 nice -n 19 find $d -maxdepth 4 \( -name 'terminator*' -o -name 'vnice*' \) -type f 2>/dev/null | head -10; done > $W/term.txt
cat $W/term.txt; [ -s $W/term.txt ] && xargs -a $W/term.txt -d '\n' sha256sum
echo "== login"; df -h /tmp | tail -1; nproc; ldd --version | head -1; python3 -V; free -g | head -2
echo "== start listings"
cat > $W/l.sh <<'EOS'
cd /project/community/jjyeung/okh7/e6fc152498
for g in 0 1 2; do
  case $g in
   0) F="/home/jjyeung/okit/p/d59945c1/4fe70504.00 /home/jjyeung/okit/p/d59945c1/4fe70504.01";;
   1) F="/home/jjyeung/okit/p/d59945c1/50011a59.00 /home/jjyeung/okit/p/d59945c1/50011a59.01 /home/jjyeung/okit/p/d59945c1/50011a59.02 /home/jjyeung/okit/p/d59945c1/50011a59.03 /home/jjyeung/okit/p/d59945c1/50011a59.04 /project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.05 /project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.06 /project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.07 /project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.08 /project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.09";;
   2) F="/project/community/jjyeung/bd8ae51c/p/d59945c1/371be2e2.00";;
  esac
  cat $F | tar tvf - > g$g.list 2> g$g.err; echo "g$g rc=$? $(date -u +%T)" >> l.done
done
EOS
nohup nice -n 19 ionice -c3 bash $W/l.sh > /dev/null 2>&1 < /dev/null &
echo started $!
