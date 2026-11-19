K=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a
P=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7/packet/d6e92a81.tar
mkdir -p /tmp/k1fwd_ev_$$ && cd /tmp/k1fwd_ev_$$ && tar xf $P --wildcards '*evalpath/runtime.py' '*/out2/routed.py' 2>/dev/null; tar tf $P | grep -i "evalpath/\|bindings.py\|student_pilot/carrier_c1_run.py" | head
cd $K && tar czf /tmp/k1fwd_kit_$$.tgz native_kit/*.py work/*.py -C /tmp/k1fwd_ev_$$ . && base64 -w0 /tmp/k1fwd_kit_$$.tgz; echo
