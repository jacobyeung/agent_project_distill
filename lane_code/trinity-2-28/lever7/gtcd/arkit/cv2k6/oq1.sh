P=/project/community/jjyeung/cp4tk_fr/venv/bin/python
echo "== host"; hostname
echo "== lscpu"; lscpu | head -16; lscpu | grep -i '^flags' | tr ' ' '\n' | grep -c avx512
echo "== py"; ls -l $P; readlink -f $P
timeout 120 $P -I -c '
import sys, os, numpy, cv2
print("python", sys.version.replace("\n"," "))
print("numpy", numpy.__version__, numpy.__file__)
print("cv2", cv2.__version__, cv2.__file__)
print("useOptimized", cv2.useOptimized(), "threads", cv2.getNumThreads())
bi = cv2.getBuildInformation()
for l in bi.splitlines():
    s = l.strip().lower()
    if any(k in s for k in ("version control","platform","timestamp","host","compiler","baseline","dispatch","cpu","png","zlib","sse","avx","parallel","lapack","c++ flags (release)","build type")):
        print("BI|", l.rstrip())
sp = os.path.dirname(os.path.dirname(cv2.__file__))
print("site", sp)
for n in sorted(os.listdir(sp)):
    if any(k in n.lower() for k in ("opencv","numpy","cv2")):
        print("SP|", n)
'
echo "== wheel"; for d in $(dirname $(dirname $P))/lib/python3*/site-packages/opencv*.dist-info $(dirname $(dirname $P))/lib/python3*/site-packages/numpy-*.dist-info; do echo "-- $d"; cat $d/WHEEL 2>/dev/null; grep -E '^(Name|Version):' $d/METADATA 2>/dev/null; cat $d/INSTALLER 2>/dev/null; grep -E 'direct_url' $d/RECORD >/dev/null && cat $d/direct_url.json 2>/dev/null; done
echo "== env"; env | grep -i -E 'OPENCV|CV_' || true
