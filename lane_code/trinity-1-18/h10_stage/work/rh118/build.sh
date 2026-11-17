set -eu
W=/scratch/jjyeung/orch_n30/h10_stage/work; R=/scratch/jjyeung/b01ec87a6f29b
mkdir -p $R/p $R/d/k $R/d/g $R/d/q
tar xzf $W/rh118/0.tgz -C $R/p
cat /scratch/jjyeung/k1/m544_parts/469ddece_mstop.tar.part0{0,1,2,3}-of-04 | tee >(sha256sum > $W/rh118/m544.sha) | tar xf - -C $R/d
cp -al /scratch/jjyeung/devs1_frames $R/d/f
cp -al /scratch/jjyeung/orch_cd/evalx/work/trin_vl/sam3src $R/d/s
ln /scratch/jjyeung/orch_cd/ttower/work/sam3_weights/sam3.pt $R/d/k/sam3.pt
cp $W/stage/a2/k/SAM3_RECEIPT.json $R/d/k/
cp -a $W/stage/a2/h $W/stage/a2/o $W/stage/a2/b $R/d/
ln /scratch/jjyeung/k1/g3t/model.safetensors $R/d/g/model.safetensors; ln /scratch/jjyeung/k1/g3t/config.json $R/d/g/config.json
cp -a $W/stage/a3/q/. $R/d/q/; cp $W/rh118/env_rh.json $R/d/q/
cp -a $W/stage/a4/v $R/d/v
printf '#!/bin/sh\nexec /scratch/jjyeung/envs/vllm/bin/python -I -B /scratch/jjyeung/b01ec87a6f29b/d/v/boot.py "$@"\n' > $R/d/v/py_rh; chmod 755 $R/d/v/py_rh
echo BUILD_OK
