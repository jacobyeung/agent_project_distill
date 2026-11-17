for p in /project/community/jjyeung/latency/envs/*/bin/python3 /project/community/jjyeung/cp4tk_rt/*/bin/python3 /project/community/jjyeung/cp4tk_rt/kit/*/bin/python3; do
  [ -x "$p" ] || continue
  r=$(timeout 60 nice -n 19 "$p" -I -c 'import torch,numpy,tokenizers;print(torch.__version__,numpy.__version__,tokenizers.__version__)' 2>&1 | tail -1 | cut -c1-80)
  echo "$p :: $r"
done
ls /project/community/jjyeung/cp4tk_rt/kit | head -30
